# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

import requests
import short_url
from decouple import config
import re
from django_rq import job


def btx_get_order(order_id, tel=None, email=None, propertyvalue=None):
    url = "{}/sale.order.get".format(config('BITRIX_REST_URL'))
    body = {
        "id": "{}".format(order_id)
    }
    try:
        r = requests.post(url, json=body, timeout=5)
        if r.status_code != 200:
            return False
    except:
        return False

    if tel:
        for pv in r.json()['result']['order']['propertyValues']:
            if pv['code'] == "PHONE":
                only_digits = re.sub('\D', '', pv['value'])
                if len(only_digits) == 11 and only_digits[0:2] == '79':
                    return only_digits
                if len(only_digits) == 11 and only_digits[0:2] == '89':
                    return "7{}".format(only_digits[1:])
                if len(only_digits) == 10 and only_digits[0:1] == '9':
                    return "7{}".format(only_digits)
        return False

    if email:
        for pv in r.json()['result']['order']['propertyValues']:
            if pv['code'] == "EMAIL":
                e_mail = True
                if 'papakarlotools' in pv['value'] or 'papakarlsochi' in pv['value']:
                    e_mail = False
                if not bool(re.search(r"[\w.-]+@[\w.-]+.\w+", pv['value'])):
                    e_mail = False
                if e_mail:
                    return pv['value']
                else:
                    return False

    if propertyvalue:
        return r.json()['result']['order']['propertyValues']

    return r


@job
def btx_update_order(order_id, record_id=None):
    url = "{}/sale.propertyvalue.modify".format(config('BITRIX_REST_URL'))
    # Сначала сохраним все имеющийся свойства
    pvalues = btx_get_order(order_id, propertyvalue=True)
    # print(pvalues)
    if not pvalues:
        return False
    out_pvalues = []
    for idx, pv in enumerate(pvalues):
        if pv['code'] == "VIDEO_PACKING":
            pv['value'] = "https://video.papakarlotools.ru/?v={}".format(short_url.encode_url(order_id))
        if 'value' in pv and pv['value']:
            out_pvalues.append(pv)
    body = {
        "fields": {
            "order": {
                "id": "{}".format(order_id),
                "propertyValues": out_pvalues
            }
        }
    }
    try:
        r = requests.post(url, json=body, timeout=5)
        # print(r.text)
        if r.status_code != 200:
            return False
    except:
        return False

    from core.models import CamRec
    from django.db.models.expressions import F
    if record_id and CamRec.objects.filter(pk=record_id).exists():
        CamRec.objects.filter(pk=record_id).update(publish_detail=F('publish_detail') + 1)
    return True
