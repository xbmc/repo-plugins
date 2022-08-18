import os

import requests
import xbmcaddon
import xbmcgui
import xbmcvfs
import logging
import re

# read settings
ADDON = xbmcaddon.Addon()

ICON = xbmcvfs.translatePath(ADDON.getAddonInfo("icon"))
FANART = xbmcvfs.translatePath(ADDON.getAddonInfo("fanart"))
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

TEMP = os.path.join(PROFILE, 'temp', '')
logger = logging.getLogger(__name__)


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
    return str(ADDON.getLocalizedString(string_id))


def convert_vtt_to_srt(fileContents):
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


def format_date(date):
    return "/".join(date.split("-")[::-1])


def get_stream_url(source):
    if "hls_url_new" in source:
        return source["hls_url_new"]
    elif "hls_url" in source:
        return source["hls_url"]
    elif "dash_stream_name" in source:
        return source["dash_stream_name"]
    return source["stream"]["clean"]["standard"]


def get_subtitles(source):
    subtitles = []
    try:
        if "subtitles" in source and "vtt_list" in source["subtitles"]:
            for vtt in source["subtitles"]["vtt_list"]:
                url = vtt["file"]
                last_slash = url.rfind("/")
                main_file_path = url[last_slash + 1: len(url) - 4] + "." + vtt["code"].lower()
                if not os.path.exists(TEMP):
                    os.makedirs(TEMP)
                file = os.path.join(TEMP, f"{main_file_path}.srt")
                response = requests.get(url).text
                with open(file, "w", encoding='latin-1') as local_file:
                    local_file.write(convert_vtt_to_srt(response))
                subtitles.append(file)
    except Exception:
        pass
    return subtitles
