#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import json
from datetime import datetime
import xbmc

try:
    from urllib.parse import urlencode,unquote
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
    from urllib import urlencode, unquote


def parameters_string_to_dict(parameters):
    param_dict = {}
    if parameters:
        param_pairs = parameters[1:].split("&")
        for param_pair in param_pairs:
            param_splits = param_pair.split('=')
            if (len(param_splits)) == 2:
                param_dict[param_splits[0]] = param_splits[1]
    return param_dict


def radiothek_log(msg, debug=True):
    if debug:
        xbmc.log(msg, xbmc.LOGDEBUG)
    else:
        xbmc.log(msg, xbmc.LOGNOTICE)


def unquote_url(url):
    if url:
        try:
            return unquote(url)
        except:
            return unquote(url.encode('utf-8'))
    return False


def url_encoder(parameters):
    return urlencode(parameters)


def get_js_json(js_data):
    regex = r"Z=\{(.*)\},Q="
    matches = re.findall(regex, str(js_data))
    for match in matches:
        json_data = "{%s}" % match
        json_data_clean = json_data.replace("new W.a(", "").replace(")", "").replace('!1', '"1"').replace('!0', '"0"').replace('Object({', "{").replace(".VUE_APP_STATION||null,", ",").replace('{?q,station*,day,offset,limit}', '')
        regex_replace = [(r"([ \{,:\[])(u)?'([^']+)'", r'\1"\3"'), (r" False([, \}\]])", r' false\1'), (r" True([, \}\]])", r' true\1')]
        for r, s in regex_replace:
            json_data_clean = re.sub(r, s, json_data_clean)
        json_data_clean = re.sub(r"{\s*'?(\w)", r'{"\1', json_data_clean)
        json_data_clean = re.sub(r",\s*'?(\w)", r',"\1', json_data_clean)
        json_data_clean = re.sub(r"(\w)'?\s*:(?!/)", r'\1":', json_data_clean)
        json_data_clean = re.sub(r":\s*'(\w+)'\s*([,}])", r':"\1"\2', json_data_clean)
        json_data_clean = re.sub(r",\s*]", "]", json_data_clean)
        json_data_clean = json_data_clean.replace("\\", "")
        json_data_clean = json_data_clean.replace("xc3x96", "OE")
        json_data_clean = json_data_clean.replace("xc3xa4", "ä")
        json_data_clean = json_data_clean.replace("xc3xb6", "ö")
        clean_json = json.loads(json_data_clean)
        return clean_json


def clean_html(html, convert_line_breaks=False):
    if html:
        if convert_line_breaks:
            html = html.replace("<br/>", "\n").replace("</p>", "\n")
        reg = re.compile('<.*?>')
        return re.sub(reg, '', html)
    return ""


def get_time_format(timestamp, offset=False, timeOnly=False):
    start_timestamp = int(str(timestamp)[:-3])
    if offset:
        start_timestamp = start_timestamp + int(str(offset)[:-3])
    start_time = datetime.fromtimestamp(start_timestamp)
    if not timeOnly:
        return start_time.strftime("%d.%m.%Y, %H:%M")
    else:
        return start_time.strftime("%H:%M")


def get_date_format(datestring):
    try:
        if datestring:
            date = datetime.strptime(str(datestring), '%Y%m%d')
            if date:
                return date.strftime("%d.%m.%Y")
        return ""
    except Exception as e:
        str_dat = str(datestring)
        return "%s.%s.%s" % (str_dat[6:8], str_dat[4:6], str_dat[0:4])


def get_images(image_versions, thumbnail=False, strict=False):
    images = []
    for image_info in image_versions:
        image_width = int(image_info['width'])
        if thumbnail and 400 <= image_width <= 500:
            return image_info['path']
        else:
            images.append(image_info['path'])
    if thumbnail and strict:
        return ""
    if thumbnail:
        images.reverse()
        return images[0]
    if images:
        images.reverse()
        return images

    if thumbnail:
        return ""
    return []
