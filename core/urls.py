# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from django.urls import path, include
from .views import MainPage, CamDetail, NginxConfig

urlpatterns = [
    path('', MainPage.as_view()),
    path('cam/<int:cam_id>/', CamDetail.as_view()),
    path('nginx/', NginxConfig.as_view())
]
