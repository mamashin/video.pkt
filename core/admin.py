# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import VideoCam, CamRecordLog, CamRec


@admin.register(VideoCam)
class VideoCamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ip', 'url', 'enable', 'stream', 'record')
    list_editable = ('name', 'ip', 'url', 'enable', 'stream', 'record')


@admin.register(CamRecordLog)
class CamRecordLogAdmin(admin.ModelAdmin):
    list_display = ('cam_name', 'type', 'cmd', 'timestamp')
    ordering = ['-id', ]

    @staticmethod
    def cam_name(obj):
        return obj.cam_id.name


@admin.register(CamRec)
class CamRecAdmin(admin.ModelAdmin):
    search_fields = ['order_id', ]
    list_display = ('cam_name', 'order_id', 'filename', 'duration_human', 'size_human', 'short_url',
                    'finish', 'publish', 'rec_time', 'open')

    @staticmethod
    def cam_name(obj):
        return obj.cam_id.name
