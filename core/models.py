# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone
from core.utils import sizeof_fmt
import time
from django.contrib.auth.models import User


class VideoCam(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название", blank=True)
    ip = models.CharField(max_length=255, null=True, blank=True, verbose_name="IP")
    rtsp_port = models.IntegerField(blank=True, verbose_name="RTSP port", default=554)
    url = models.CharField(max_length=255, null=True, blank=True, verbose_name="URL")
    main_stream_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="Main stream URL",
                                       default="cam/realmonitor?channel=1&subtype=0")
    sub_stream_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="Sub stream URL",
                                      default="cam/realmonitor?channel=1&subtype=1")
    login = models.CharField(max_length=255, null=True, blank=True, verbose_name="Login", default="admin")
    password = models.CharField(max_length=255, null=True, blank=True, verbose_name="Password", default="admin")
    enable = models.BooleanField(default=False, verbose_name="Включена", blank=True)
    stream = models.BooleanField(default=False, verbose_name="Трансляция", blank=True)
    record = models.BooleanField(default=False, verbose_name="Запись", blank=True)
    params = models.TextField(verbose_name="Параметры", blank=True)

    def __str__(self):
        return self.name


class CamRecordLog(models.Model):
    cam_id = models.ForeignKey(VideoCam,
                               models.CASCADE,
                               verbose_name="Камера",
                               related_name="cam_set",
                               blank=False,
                               null=False)
    type = models.CharField(max_length=6, choices=(('stream', 'Stream'), ('rec', 'Rec'),), blank=False, db_index=True)
    cmd = models.CharField(max_length=5, choices=(('start', 'Start'), ('stop', 'Stop'),), blank=False)
    timestamp = models.DateTimeField(verbose_name="Время", auto_now_add=True, db_index=True)

    def __str__(self):
        return self.cam_id.name


class CamRec(models.Model):
    cam_id = models.ForeignKey(VideoCam,
                               models.CASCADE,
                               verbose_name="Камера",
                               related_name="camrec",
                               blank=False,
                               null=False)
    order_id = models.IntegerField(blank=True, verbose_name="Order number", null=True)

    filename = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename", db_index=True)
    path = models.CharField(max_length=255, null=True, blank=True, verbose_name="Path")
    short_url = models.CharField(max_length=255, null=True, blank=True, verbose_name="Short URL", db_index=True)
    finish = models.BooleanField(default=False, verbose_name="Finish Rec", blank=True)
    publish = models.BooleanField(default=False, verbose_name="Опубликовано", blank=True)
    rec_time = models.DateTimeField(verbose_name="Время записи", auto_now_add=True)
    publish_time = models.DateTimeField(verbose_name="Время публикации", null=True, blank=True)
    duration = models.IntegerField(blank=True, verbose_name="Длинна", null=True)
    size = models.IntegerField(blank=True, verbose_name="Размер", null=True)
    user = models.ForeignKey(
        User,
        models.CASCADE,
        verbose_name="Пользователь",
        related_name="user",
        blank=True,
        null=True
    )

    def rec_time_iso(self):
        return timezone.localtime(self.rec_time).strftime('%d/%m/%y %H:%M')

    def publish_time_iso(self):
        if self.publish_time:
            return timezone.localtime(self.publish_time).strftime('%d/%m/%y %H:%M')
        return None

    def duration_human(self):
        if self.duration and self.duration > 0:
            return time.strftime('%H:%M:%S', time.gmtime(self.duration))
        return ""

    def size_human(self):
        if self.size and self.size > 0:
            return sizeof_fmt(self.size)
        return ""
