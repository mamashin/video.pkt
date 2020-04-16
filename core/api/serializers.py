# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from core.models import VideoCam, CamRec
from rest_framework import serializers


class VideoCamSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoCam
        fields = '__all__'


class VideoCamSerializerAnon(serializers.ModelSerializer):

    class Meta:
        model = VideoCam
        fields = ('id', 'name', 'url', 'stream')


class VideoRecSerializer(serializers.ModelSerializer):
    cam_name = serializers.ReadOnlyField(source='cam_id.name')

    class Meta:
        model = CamRec
        fields = ('id', 'cam_name', 'order_id', 'short_url', 'finish', 'publish', 'rec_time_iso', 'duration', 'size',
                  'duration_human', 'size_human', 'publish_time_iso', 'filename')
