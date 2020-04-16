# -*- coding: utf-8 -*-

__author__ = 'Nikolai Mamashin (mamashin@gmail.com)'

from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed, pre_delete
from django.dispatch import receiver
from .models import VideoCam, CamRecordLog, CamRec
from .utils import rtmp_control


@receiver(pre_save, sender=VideoCam)
def model_pre_save(sender, instance, **kwargs):
    if instance.id is not None:
        instance.__pre_save_instance = VideoCam.objects.get(pk=instance.pk)


@receiver(post_save, sender=VideoCam)
def create_log(sender, instance, created, **kwargs):
    if not created:
        if instance.record != instance.__pre_save_instance.record:
            cmd = 'stop'
            if instance.record:
                cmd = 'start'
            CamRecordLog.objects.create(cam_id_id=instance.id, type='rec', cmd=cmd)
        if instance.stream != instance.__pre_save_instance.stream:
            cmd = 'stop'
            if instance.stream:
                cmd = 'start'
            CamRecordLog.objects.create(cam_id_id=instance.id, type='stream', cmd=cmd)
