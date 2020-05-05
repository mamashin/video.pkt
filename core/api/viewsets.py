# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.shortcuts import render
from django.conf import settings
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from decouple import config
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from core.api.permissions import SuperuserAccessPermission, OnlySuperuserRW
from .serializers import VideoCamSerializer, VideoRecSerializer, VideoCamSerializerAnon
from core.utils import rtmp_control, rq_send, waz_app_send, send_mail
from core.models import VideoCam, CamRec
from core.bitrix import btx_get_order, btx_update_order
import time
import re
from django.utils.http import urlquote
from pathlib import Path
import short_url
import logging
from django.db.models import Value, BooleanField

logger = logging.getLogger(__name__)


class VideoCamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = VideoCam.objects.filter(enable=True).order_by('id')
    serializer_class = VideoCamSerializer

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return VideoCamSerializer
        return VideoCamSerializerAnon

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return VideoCam.objects.filter(enable=True).order_by('id')
        return VideoCam.objects.filter(stream=True).order_by('id')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # self.perform_update(serializer)

        if 'order' in request.data:
            try:
                order_id = int(request.data['order'])
            except ValueError:
                return Response({'error': True}, status=401)

            if request.data['record']:
                rec_file, rec_path = rtmp_control('start', instance.id, 'main')
                if rec_file and rec_file:
                    CamRec.objects.create(cam_id_id=instance.id,
                                          order_id=order_id,
                                          filename=rec_file,
                                          path=rec_path,
                                          finish=False,
                                          short_url=short_url.encode_url(order_id),
                                          user=self.request.user
                                          )
                else:
                    return Response({'status': False}, status=200)

            if not request.data['record']:
                rec_file, rec_path = rtmp_control('stop', instance.id, 'main')
                if rec_file and rec_path:
                    rec = CamRec.objects.filter(order_id=order_id, filename=rec_file).first()
                    if rec:
                        rec.finish = True
                        rec.save()
                        out = CamRec.objects.filter(id=rec.id).values()
                        self.perform_update(serializer)
                        # Add status field for front-end
                        return Response(CamRec.objects.filter(id=rec.id).values().
                                        annotate(status=Value(True, output_field=BooleanField())).first())
                else:
                    return Response({'status': False}, status=200)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        self.perform_update(serializer)

        # Add status field for front-end
        out = serializer.data
        out['status'] = True
        return Response(out)


class VideoRecViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CamRec.objects.filter(finish=True).order_by('-id')
    serializer_class = VideoRecSerializer


class CheckOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'order' not in request.data:
            return Response({"status": False})
        order_id = request.data['order']
        if type(order_id) != int:
            return Response({"status": False})

        btx = btx_get_order(order_id)
        if not btx:
            return Response({"status": False}, status=200)

        resp = {
            "status": True,
            "order": btx.json()['result']['order']
        }

        return Response(resp)


class GetOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'cam_id' not in request.data:
            return Response({"status": False})
        cam_id = request.data['cam_id']
        rec = CamRec.objects.filter(cam_id_id=cam_id, finish=False).order_by('rec_time').last()
        if rec:
            return Response({"status": True, "order_id": rec.order_id})
        return Response({"status": False})


class FileInfo(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)
        if 'filename' not in request.data:
            return Response({"status": False}, status=400)
        f_name = request.data['filename']
        rec = CamRec.objects.filter(filename=f_name).first()
        if rec:
            rec.duration = request.data['duration']
            rec.size = request.data['size']
            rec.save()
            return Response({"status": True})
        return Response({"status": False}, status=400)


class SendOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_data = []
        if type(request.data) == dict:
            request_data = [request.data]
        if type(request.data) == list:
            request_data = request.data
        for data in request_data:
            valid_data = VideoRecSerializer(data=data)
            if not valid_data.is_valid():
                return Response({"status": False}, status=200)
            camera_record = CamRec.objects.filter(id=data['id']).filter(publish=False).first()
            if camera_record:
                camera_record.publish = True
                camera_record.publish_time = timezone.localtime(timezone.now())

                # Обновляем свойство заказа VIDEO_PACKING - прописываем туда ссылку на видео
                btx_update_order.delay(camera_record.order_id, camera_record.pk)
                # Отправляем нотификацию на тел клиента
                waz_app_send.delay(camera_record.order_id, camera_record.pk)
                # Отправляем нотификацию на почту
                send_mail.delay(camera_record.order_id, camera_record.pk)

                camera_record.save()

        return Response({"status": True}, status=200)


class GetVideo(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'head', 'options']

    def get(self, request, *args, **kwargs):
        response = HttpResponse()
        path_obj = Path(request.path)
        if not request.user.is_authenticated:
            req_playlist = re.match(r'(sub|main)-([0-9]+).m3u8', path_obj.name)
            if req_playlist:
                if not VideoCam.objects.filter(pk=int(req_playlist.group(2))).filter(stream=True):
                    bad_response = HttpResponse(status=403)
                    bad_response['Cache-Control'] = 'no-cache'
                    bad_response['Content-Type'] = ""
                    return bad_response

        uri = '/x-video/{}'.format("/".join(path_obj.parts[2:]))
        response['Content-Type'] = ""
        response['X-Accel-Buffering '] = "no"
        response['X-Accel-Redirect'] = urlquote(uri)
        return response


class SrvReload(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'reload' in request.data:
            for camrec in CamRec.objects.filter(finish=False):
                camrec.delete()
            for cam in VideoCam.objects.filter(record=True):
                cam.record = False
                cam.save()
            if not settings.DEBUG:
                rq_send('nginx-stream', 'reload')
            time.sleep(2)
            return Response({"status": True})
        return Response({"status": False})
