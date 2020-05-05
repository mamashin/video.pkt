# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework import routers

from .viewsets import VideoCamViewSet, CheckOrder, GetOrder, VideoRecViewSet, FileInfo, SendOrder, SrvReload

router = routers.DefaultRouter()
router.register(r'videocam', VideoCamViewSet)
router.register(r'videorec', VideoRecViewSet)

urlpatterns = [
    path('order/', CheckOrder.as_view()),
    path('last-order/', GetOrder.as_view()),
    path('file/', FileInfo.as_view()),
    path('reload/', SrvReload.as_view()),
    path('sendorder/', SendOrder.as_view()),
    path('', include(router.urls))
    ]
