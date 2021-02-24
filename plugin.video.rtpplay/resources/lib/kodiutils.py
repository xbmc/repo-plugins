# -*- coding: utf-8 -*-
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import sys
import logging
import json as json
import re
import base64

PY3 =  sys.version_info > (3, 0)

if PY3:
    from urllib.request import urlopen
    from urllib.parse import unquote
    from html.parser import HTMLParser
else:
    from urllib2 import urlopen
    from urlparse import unquote
    from HTMLParser import HTMLParser

# read settings
ADDON = xbmcaddon.Addon()
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
TEMP = os.path.join(PROFILE, 'temp', '')

if PY3:
    ICON = xbmcvfs.translatePath(ADDON.getAddonInfo("icon"))
    FANART = xbmcvfs.translatePath(ADDON.getAddonInfo("fanart"))
else:
    ICON = xbmc.translatePath(ADDON.getAddonInfo("icon"))
    FANART = xbmc.translatePath(ADDON.getAddonInfo("fanart"))

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        if PY3:
            self.strict = False
            self.convert_charrefs = True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_html_tags(html):
    s = HTMLStripper()
    s.feed(html)
    return s.get_data()

def compat_py23str(x):
    if PY3:
        return str(x)
    else:
        if isinstance(x, unicode):
            try:
                return unicode(x).encode("utf-8")
            except UnicodeEncodeError:
                try:
                    return unicode(x).encode("utf-8")
                except:
                   return str(x)
        else:
            return str(x)


def ok(heading, line1, line2="", line3=""):
    xbmcgui.Dialog().ok(heading, line1, line2, line3)


def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


def get_setting(setting):
    return ADDON.getSetting(setting).strip()

def set_setting(setting, value):
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    return get_setting(setting).lower() == "true"


def get_setting_as_float(setting):
    try:
        return float(get_setting(setting))
    except ValueError:
        return 0


def get_setting_as_int(setting):
    try:
        return int(get_setting_as_float(setting))
    except ValueError:
        return 0


def get_string(string_id):
    return compat_py23str(ADDON.getLocalizedString(string_id))


def kodi_json_request(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return None
    except KeyError:
        logger.warn("[%s] %s" %
                    (params['method'], response['error']['message']))
        return None


def find_stream_url(html):
    try:
        for m in re.finditer(r'decodeURIComponent(?:(\s+)?)\((?:(\s+)?)\["(.*?)"]', html):
            url = unquote(m.group(3).replace(" ", "").replace('","', ""))
            if url.startswith("http"):
                return url
            if url.endswith(".mp4"):
                continue
            url = base64.b64decode(url).decode('utf-8')
            if url.startswith("http"):
                return url
    except:
        pass
    urls = ["ondemand.rtp.pt", "streaming.rtp.pt", "live.rtp.pt"]
    for base_url in urls:
        try:
            for m in re.finditer(r'"https://(.+?)' + base_url + '(.*?)"', html):
                if m.group(2) and "preview" not in m.group(2):
                    return "https://" + m.group(1) + base_url + m.group(2)
        except:
            pass
    raise ValueError


def convertVttSrt(fileContents):
    # taken from https://github.com/jansenicus/vtt-to-srt.py/blob/master/vtt_to_srt.py#L29
    replacement = re.sub(r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n',
                         r'\1,\2 --> \3,\4\n', fileContents)
    replacement = re.sub(r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n',
                         r'\1,\2 --> \3,\4\n', replacement)
    replacement = re.sub(r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n',
                         replacement)
    replacement = re.sub(r'WEBVTT\n', '', replacement)
    replacement = re.sub(r'Kind:[ \-\w]+\n', '', replacement)
    replacement = re.sub(r'Language:[ \-\w]+\n', '', replacement)
    replacement = re.sub(r'<c[.\w\d]*>', '', replacement)
    replacement = re.sub(r'</c>', '', replacement)
    replacement = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', replacement)
    replacement = re.sub(r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', replacement)
    replacement = re.sub(r'Style:\n##\n', '', replacement)
    return replacement


def find_subtitles(html):
    try:
        match = re.search(r'["\']\s*?http(.*?)\.vtt\s*?["\']', html)
        if match and len(match.groups()) > 0:
            url = "http" + match.group(1) + ".vtt"
            last_slash = url.rfind("/")
            if last_slash != -1:
                id = url[last_slash + 1:len(url) - 4]
                if not os.path.exists(TEMP):
                    os.makedirs(TEMP)
                file = os.path.join(TEMP, "{id}.srt".format(id=id))
                response = urlopen(url)
                with open(file, "w") as local_file:
                    local_file.write(convertVttSrt(response.read().decode('utf-8')))
                return file
    except Exception:
        pass
