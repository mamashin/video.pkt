# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from decouple import config
import requests
from pathlib import Path
import logging
import math
from redis import Redis
from rq import Queue
import requests
import short_url
from core.bitrix import btx_get_order
from django_rq import job
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def rtmp_control(cmd, cam_id, stream='main'):
    #  http://172.16.201.20:8080/control/record/start?app=cam2&name=sub-2
    base_url = "{}/{}?cam{}&name={}-{}".format(config('RTPM_CTRL_URL'), cmd, cam_id, stream, cam_id)
    req = requests.get(base_url, timeout=3)
    print("Request to MSK")
    print(req.status_code)
    print(req.text)
    if req.status_code != 200:
        return False, False
    if not req.text:
        return False, False
    return Path(req.text).stem, str(Path(req.text).parent)


def sizeof_fmt(num, suffix='b'):
    magnitude = int(math.floor(math.log(num, 1024)))
    val = num / math.pow(1024, magnitude)
    if magnitude > 7:
        return '{:.1f}{}{}'.format(val, ' Y', suffix)
    return '{:3.1f}{}{}'.format(val, ['', ' K', ' M', ' G', ' T', ' P', ' E', ' Z'][magnitude], suffix)


def rq_send(name, function, body=None):
    q = Queue(connection=Redis.from_url(config('RQ_REDIS_URL')), name=name)
    if body:
        q.enqueue('run.{}'.format(function), body)
    q.enqueue('run.{}'.format(function))


@job
def waz_app_send(order_id, record_id=None):
    client_tel = btx_get_order(order_id, tel=True)
    if settings.DEBUG:
        client_tel = config('DEBUG_TEL')
    send_msg_url = "{}/sendMessage?token={}".format(config('WAZAPP_API_URL'), config('WAZAPP_API_TOKEN'))
    send_link_url = "{}/sendLink?token={}".format(config('WAZAPP_API_URL'), config('WAZAPP_API_TOKEN'))
    post_data = {
        "phone": client_tel,
        "body": "👋 Здравствуйте! Это компания _«Папа Карло»_. Вы делали заказ *№{}* в нашем интернет магазине, "
                "мы его уже упаковали и готовы отправить Вам, а пока вы можете посмотреть видео сборки Вашего заказа, "
                "ссылка придет в следующем сообщение.".format(order_id)
    }
    try:
        r = requests.post(send_msg_url, json=post_data, timeout=5)
        result = True
    except:
        result = False

    post_data = {
        "phone": client_tel,
        "body": "https://video.papakarlotools.ru/?v={}".format(short_url.encode_url(int(order_id))),
        "title": "Сборка Вашего заказа №{}".format(order_id),
        "description": "© Торговая Компания «Папа Карло»",
        "previewBase64": "data:image/jpeg;base64,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"
    }
    try:
        r = requests.post(send_link_url, json=post_data, timeout=5)
        result = result and True
    except:
        result = result and False

    if result:
        from core.models import CamRec
        from django.db.models.expressions import F
        if record_id and CamRec.objects.filter(pk=record_id).exists():
            CamRec.objects.filter(pk=record_id).update(publish_detail=F('publish_detail') + 2)

    return result


@job
def send_mail(order_id, record_id=None):
    client_email = btx_get_order(order_id, email=True)
    if not client_email:
        return False
    subject = "[ПапаКарло] Видео сборки вашего заказа N{}".format(order_id)
    from_email = 'robot@papakarlotools.ru'
    to = [client_email]
    context = {
        "video_url": "https://video.papakarlotools.ru/?v={}".format(short_url.encode_url(int(order_id)))
    }
    message_txt = render_to_string('send_mail.txt', context)
    message_html = render_to_string('send_mail.html', context)
    msg = EmailMultiAlternatives(subject, message_txt, to=to, from_email=from_email)
    msg.attach_alternative(message_html, "text/html")
    msg.send()

    from core.models import CamRec
    from django.db.models.expressions import F
    if record_id and CamRec.objects.filter(pk=record_id).exists():
        CamRec.objects.filter(pk=record_id).update(publish_detail=F('publish_detail') + 4)

    return True
