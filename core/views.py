# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import VideoCam, CamRec
import short_url
from decouple import config


class MainPage(ListView):
    template_name = "main_auth_page.html"
    context_object_name = "result"
    model = VideoCam
    get_video = False
    order_id = None
    s_url = None
    carm_user = False
    arch = False

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.username == "carm":
            self.carm_user = True

        if self.request.method == "GET" and 'arch' in self.request.GET and self.request.user.is_authenticated:
            self.arch = True
            return CamRec.objects.all()

        if self.request.method == "GET" and 'v' in self.request.GET and len(self.request.GET['v']) == 5:
            video_qs = CamRec.objects.filter(short_url=self.request.GET['v']).filter(publish=True)
            if video_qs:
                self.get_video = True
                self.order_id = short_url.decode_url(self.request.GET['v'])
                self.s_url = self.request.GET['v']
                return video_qs

        if self.request.user.is_authenticated:
            return VideoCam.objects.filter(enable=True)

        return VideoCam.objects.filter(stream=True)

    def get_template_names(self):
        if self.get_video:
            return ['main_video_page.html']
        if self.arch:
            return ['arch_page.html']

        if self.request.user.is_authenticated:
            return ['main_auth_page.html']
        else:
            return ['main_anon_page.html']

    def get_context_data(self, **kwargs):
        context = super(MainPage, self).get_context_data(**kwargs)
        context['cdn_url'] = '/video'
        # context['cdn_url'] = config('CDN_HOST') + '/video'
        if self.carm_user:  # Если пользоваетль из Царма - отдаем прямой линк на видео
            context['cdn_url'] = config('CARM_URL')
            context['carm'] = True
        if self.get_video:
            context['get_video'] = True
            context['order_id'] = self.order_id
            context['short_url'] = self.s_url
        return context


class CamDetail(LoginRequiredMixin, ListView):
    raise_exception = True
    template_name = "cam_detail.html"
    context_object_name = "result"

    def get_queryset(self):
        return VideoCam.objects.filter(pk=self.kwargs['cam_id']).first()


class NginxConfig(ListView):
    template_name = "nginx.jinja2"
    context_object_name = "result"
    queryset = VideoCam.objects.filter(enable=True)

    def get_context_data(self, **kwargs):
        context = super(NginxConfig, self).get_context_data(**kwargs)
        context['rtpm_server'] = config('RTPM_SERVER')
        return context
