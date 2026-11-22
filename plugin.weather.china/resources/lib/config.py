# -*- coding: utf-8 -*-
"""
lib/config.py — 插件配置、常量路径、本地化与日志。

设计要点：
* Kodi 专有 API（xbmc / xbmcaddon / xbmcvfs）**只在本模块导入**，
  lib 下其余模块均为纯 Python，可在 PC 上离线自测（见 tools/selftest.py）。
* 所有界面文本必须经 L() 取词，禁止在 UI 代码里硬编码中文。
* 所有设置读取都带默认值兜底，settings.xml 缺项/损坏不会导致崩溃。
"""
from __future__ import unicode_literals

import os

import xbmc
import xbmcaddon

try:
    import xbmcvfs
except ImportError:  # pragma: no cover - 极老版本或离线自测
    xbmcvfs = None

ADDON_ID = "plugin.weather.china"
ADDON = xbmcaddon.Addon(ADDON_ID)


def _translate(path):
    if xbmcvfs is not None:
        try:
            return xbmcvfs.translatePath(path)
        except Exception:  # noqa: BLE001
            pass
    return path


ADDON_PATH = _translate(ADDON.getAddonInfo("path"))
PROFILE_PATH = _translate(ADDON.getAddonInfo("profile"))
DATA_PATH = os.path.join(ADDON_PATH, "resources", "data")
MEDIA_PATH = os.path.join(ADDON_PATH, "resources", "media")
CACHE_PATH = os.path.join(PROFILE_PATH, "cache")

for _p in (PROFILE_PATH, CACHE_PATH):
    try:
        if _p and not os.path.isdir(_p):
            os.makedirs(_p)
    except Exception:  # noqa: BLE001
        pass

# ---------------------------------------------------------------- URL 常量
NMC_BASE = "http://www.nmc.cn"
NMC_PROVINCES = NMC_BASE + "/rest/province"
NMC_STATIONS = NMC_BASE + "/rest/province/{code}"
NMC_WEATHER = NMC_BASE + "/rest/weather?stationid={code}"
NMC_ALARMS = NMC_BASE + "/rest/findAlarm?pageNo={page}&pageSize={size}"
NMC_ALARM_PAGE = NMC_BASE + "/publish/alarm/{alertid}.html"
NMC_REFERER = NMC_BASE + "/"

WCN_INDEX = "http://d1.weather.com.cn/weather_index/{code}.html"
WCN_DINGZHI = "http://d1.weather.com.cn/dingzhi/{code}.html"
WCN_7DAY = "http://www.weather.com.cn/weather/{code}.shtml"
WCN_REFERER = "http://www.weather.com.cn/"
WCN_PROVINCES_5 = "https://www.weather.com.cn/data/city3jdata/china.html"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# ---------------------------------------------------------------- 本地化
# 极端情况下（语言文件缺失）保证界面不至于完全空白
_FALLBACK = {
    32100: "Current conditions", 32101: "Multi-day forecast",
    32102: "Weather alerts", 32103: "Change city", 32104: "Search city",
    32105: "Nationwide alerts", 32106: "Refresh city index",
    32107: "Settings", 32108: "No data", 32109: "Failed to fetch data",
    32110: "Refresh", 32137: "Unknown", 32139: "No active alerts",
    32163: "OK", 32165: "Error", 32166: "Information",
    32192: "Browse by province",
    32193: "No typing needed - just pick a province and city",
    32194: "Select a city",
}


def L(str_id, *args):
    """取本地化字符串；支持 {0} 占位符。"""
    try:
        text = ADDON.getLocalizedString(int(str_id))
    except Exception:  # noqa: BLE001
        text = ""
    if not text:
        text = _FALLBACK.get(int(str_id), str(str_id))
    if args:
        try:
            text = text.format(*args)
        except (IndexError, KeyError, ValueError):
            pass
    return text


# ---------------------------------------------------------------- 设置读取
def get(key, default=""):
    try:
        value = ADDON.getSetting(key)
    except Exception:  # noqa: BLE001
        return default
    if value is None or value == "":
        return default
    return value


def get_bool(key, default=False):
    value = get(key, "")
    if value == "":
        return default
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def get_int(key, default=0, minimum=None, maximum=None):
    try:
        value = int(float(get(key, str(default))))
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def put(key, value):
    try:
        ADDON.setSetting(key, "" if value is None else str(value))
        return True
    except Exception:  # noqa: BLE001
        return False


def current_location():
    """返回当前配置的城市三元组。"""
    return {
        "name": get("city_name", "北京"),
        "nmc_code": get("nmc_code", "Wqsps"),
        "wcn_code": get("wcn_code", "101010100"),
    }


# ---------------------------------------------------------------- 输出格式
DASH = "—"  # 全角破折号：所有缺失值统一显示


def is_fahrenheit():
    return get("temp_unit", "0") == "1"


def format_temp(value, with_unit=True):
    """统一温度输出：None -> '—'；°F 按 C*9/5+32 换算；整数不带小数点。"""
    if value is None or value == "":
        return DASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return DASH
    if is_fahrenheit():
        number = number * 9.0 / 5.0 + 32.0
        text = "%.0f" % number
        return text + "°F" if with_unit else text
    text = "%g" % number
    return text + "°C" if with_unit else text


def format_value(value, suffix="", digits=None):
    """统一数值输出，None -> '—'。"""
    if value is None or value == "":
        return DASH
    if isinstance(value, (int, float)):
        text = "%g" % value if digits is None else ("%.*f" % (digits, value))
    else:
        text = str(value).strip() or DASH
    return text + suffix if text != DASH else DASH


# ---------------------------------------------------------------- 日志
LOGDEBUG = getattr(xbmc, "LOGDEBUG", 0)
LOGINFO = getattr(xbmc, "LOGINFO", 1)
LOGWARNING = getattr(xbmc, "LOGWARNING", 2)
LOGERROR = getattr(xbmc, "LOGERROR", 4)
_LOG_PREFIX = "[%s] " % ADDON_ID


def log(message, level=None):
    if level is None:
        level = LOGINFO
    try:
        xbmc.log(_LOG_PREFIX + str(message), level)
    except Exception:  # noqa: BLE001
        pass


def debug(message):
    if get_bool("debug", False):
        log(message, LOGDEBUG)


def warn(message):
    log(message, LOGWARNING)


def error(message):
    log(message, LOGERROR)
