# encoding: utf-8
# util class for Hbo Go Kodi add-on
# Copyright (C) 2019 ArvVoid (https://github.com/arvvoid)
# Relesed under GPL version 2
#########################################################

from __future__ import absolute_import, division

import base64
import hashlib
import sys


class Util(object):

    @staticmethod
    def is_utc_datetime_past_now(date_string, date_string_format="%Y-%m-%dT%H:%M:%SZ", output_format="%d/%m/%Y %H:%M:%S"):
        from datetime import datetime
        from dateutil import tz
        import time
        from_zone = tz.tzutc()  # UTC ZONE
        to_zone = tz.tzlocal()  # LOCAL TIMEZONE
        try:
            avail_datetime = datetime.fromtimestamp(time.mktime(time.strptime(date_string, date_string_format)))
            avail_datetime = avail_datetime.replace(tzinfo=from_zone)
            avail_datetime = avail_datetime.astimezone(to_zone)
        except ValueError:
            return True  # date string in bad format, ignore, try to play
        current_time = datetime.now()
        current_time = current_time.replace(tzinfo=to_zone)
        if current_time < avail_datetime:
            return avail_datetime.strftime(output_format)  # if not past current date time return the local datetime as string
        else:
            return True  # if available return True

    @staticmethod
    def base64enc(data):
        if sys.version_info < (3, 0):
            return base64.b64encode(data)
        try:
            return base64.b64encode(bytes(data)).decode('utf8')
        except TypeError:
            return base64.b64encode(bytes(data, 'utf8')).decode('utf8')

    @staticmethod
    def base64dec_string(base64data):
        if sys.version_info < (3, 0):
            return base64.b64decode(base64data)
        return base64.b64decode(base64data).decode('utf8')

    @staticmethod
    def base64dec_bytes(base64data):
        return base64.b64decode(base64data)

    @staticmethod
    def hash225_bytes(data):
        if sys.version_info < (3, 0):
            return hashlib.sha256(bytes(data)).digest()
        try:
            return hashlib.sha256(bytes(data, 'utf8')).digest()
        except TypeError:
            return hashlib.sha256(bytes(data)).digest()

    @staticmethod
    def hash225_string(data):
        if sys.version_info < (3, 0):
            return hashlib.sha256(bytes(data)).hexdigest()
        try:
            return hashlib.sha256(bytes(data, 'utf8')).hexdigest()
        except TypeError:
            return hashlib.sha256(bytes(data)).hexdigest()
