# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'

from decouple import config
import requests
from pathlib import Path
import logging
import math

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
