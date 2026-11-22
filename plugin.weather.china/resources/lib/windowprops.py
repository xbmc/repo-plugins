# -*- coding: utf-8 -*-
"""
lib/windowprops.py — 把标准天气结构写入 Kodi 皮肤可读取的 Window Properties。

Kodi 的天气部件读取 Home Window(10000) 上的属性。本模块按官方约定写出
  Weather.Location / Weather.IsFetched
  Current.Temperature / Current.Condition / Current.ConditionIcon / ...
  Day0.Title / Day0.HighTemp / Day0.LowTemp / Day0.Outlook / Day0.OutlookIcon ...
  Weather.AlertCount / Weather.Alert1.Title / ...
这样即使不使用本插件的菜单，支持天气的皮肤也能显示中国天气数据。

由 service.py 定时调用；也可在插件菜单刷新时即时调用。
"""
from __future__ import unicode_literals

import datetime
import os

import xbmcgui

from . import config


def weekday_label(date_str, index):
    if index == 0:
        return config.L(32117)
    if index == 1:
        return config.L(32118)
    if index == 2:
        return config.L(32119)
    try:
        date = datetime.date.fromisoformat(date_str)
        return config.L(32200 + date.weekday())
    except (ValueError, TypeError):
        return ""


def publish(result):
    if not config.get_bool("skin_props", True):
        return False
    try:
        window = xbmcgui.Window(10000)
    except Exception:  # noqa: BLE001
        return False

    location = result.get("location") or {}
    current = result.get("current") or {}
    forecast = result.get("forecast") or []
    alert_list = result.get("alerts") or []

    window.setProperty("Weather.Location", str(location.get("name", "")))
    window.setProperty("Weather.IsFetched", "true" if result.get("ok") else "false")
    window.setProperty("Weather.Provider", config.L(32180))
    window.setProperty("Weather.Source", str(result.get("source", "")))
    window.setProperty("Weather.Updated", str(result.get("updated", "")))

    window.setProperty("Current.Temperature", config.format_temp(current.get("temp")))
    window.setProperty("Current.FeelsLike", config.format_temp(current.get("feels_like")))
    window.setProperty("Current.Condition", str(current.get("condition") or config.DASH))
    window.setProperty("Current.ConditionIcon", str(current.get("condition_icon") or ""))
    window.setProperty("Current.OutlookIcon", str(current.get("condition_icon") or ""))
    window.setProperty("Current.Humidity", config.format_value(current.get("humidity"), "%"))
    window.setProperty("Current.Pressure", config.format_value(current.get("pressure")))
    window.setProperty("Current.Precipitation", config.format_value(current.get("rain"), " mm"))
    window.setProperty("Current.Wind", str(current.get("wind_power") or config.DASH))
    window.setProperty("Current.WindDirection", str(current.get("wind_dir") or config.DASH))
    window.setProperty("Current.WindSpeed", config.format_value(current.get("wind_speed")))
    window.setProperty("Current.Visibility", config.format_value(current.get("visibility")))
    window.setProperty("Current.UVIndex", config.DASH)
    window.setProperty("Current.DewPoint", config.DASH)
    window.setProperty("Current.AQI", config.format_value(current.get("aqi")))
    window.setProperty("Current.PM25", config.format_value(current.get("pm25")))
    window.setProperty("Current.Sunrise", str(current.get("sunrise") or config.DASH))
    window.setProperty("Current.Sunset", str(current.get("sunset") or config.DASH))
    window.setProperty("Current.FanartCode", str(current.get("condition_key") or "unknown"))

    for index, day in enumerate(forecast[:7]):
        prefix = "Day%d." % index
        title = weekday_label(day.get("date", ""), index) or str(day.get("date", ""))
        window.setProperty(prefix + "Title", title)
        window.setProperty(prefix + "Date", str(day.get("date", "")))
        window.setProperty(prefix + "HighTemp", config.format_temp(day.get("high")))
        window.setProperty(prefix + "LowTemp", config.format_temp(day.get("low")))
        condition = (day.get("day") or {}).get("condition") or \
                    (day.get("night") or {}).get("condition") or config.DASH
        icon = (day.get("day") or {}).get("icon") or ""
        key = (day.get("day") or {}).get("key") or "unknown"
        window.setProperty(prefix + "Outlook", str(condition))
        window.setProperty(prefix + "Condition", str(condition))
        window.setProperty(prefix + "OutlookIcon", str(icon))
        window.setProperty(prefix + "FanartCode", str(key))
        window.setProperty(prefix + "Wind", str((day.get("day") or {}).get("wind_power") or config.DASH))
        window.setProperty(prefix + "Precipitation",
                           config.format_value(day.get("precipitation"), " mm"))

    window.setProperty("Weather.AlertCount", str(len(alert_list)))
    for index, alert in enumerate(alert_list[:10], start=1):
        prefix = "Weather.Alert%d." % index
        window.setProperty(prefix + "Title", alert.get("title", ""))
        window.setProperty(prefix + "Type", alert.get("type", ""))
        window.setProperty(prefix + "Level", alert.get("level", ""))
        window.setProperty(prefix + "Time", alert.get("issue_time", ""))
        window.setProperty(prefix + "Icon", alert.get("icon", ""))
    return True


# ---------------------------------------------------------------- 天气窗口 12600
# Kodi 的天气系统读取 Window(12600) 的属性并负责单位换算（°C→°F、km/h→mph），
# 因此这里的数值必须是纯数字字符串，不能带 °C / % / mm 等单位。
# 条件代码对应 Kodi 自带图标包 resource.images.weathericons.default。
KODI_CODES = {
    "sunny": 32, "partly_cloudy": 30, "overcast": 26, "cloudy": 26,
    "shower": 11, "thunderstorm": 4, "hail": 35, "sleet": 18,
    "light_rain": 9, "rain": 12, "heavy_rain": 12,
    "snow": 16, "light_snow": 14, "heavy_snow": 41,
    "fog": 20, "dust": 19, "haze": 21, "frost": 25, "wind": 24,
    "unknown": "na",
}

MAX_LOCATIONS = 3


def kodi_code(key):
    return KODI_CODES.get(key or "unknown", "na")


def _num(value):
    """转成 Kodi 要求的纯数字（缺测返回空串）。"""
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return ""


def _wind_kmh(current):
    """数据源风速为 m/s，Kodi 天气窗口要求 km/h。"""
    try:
        return str(int(round(float(current.get("wind_speed")) * 3.6)))
    except (TypeError, ValueError):
        return ""


def publish_locations():
    """把 settings.xml 中配置的地点写进天气窗口（Kodi 要求 LocationN / Locations）。"""
    try:
        window = xbmcgui.Window(12600)
    except Exception:  # noqa: BLE001
        return 0
    count = 0
    for index in range(1, MAX_LOCATIONS + 1):
        name = (config.get("location%d" % index, "") or
                config.get("location%d_name" % index, ""))
        window.setProperty("Location%d" % index, name)
        if name:
            count += 1
    window.setProperty("Locations", str(count))
    return count


def publish_weather(result, location_index=1):
    """按官方 Weather add-ons 规范填充 Window(12600)，供皮肤 infolabel 使用。"""
    try:
        window = xbmcgui.Window(12600)
    except Exception:  # noqa: BLE001
        return False

    location = result.get("location") or {}
    current = result.get("current") or {}
    forecast = result.get("forecast") or []
    alerts = result.get("alerts") or []
    city = str(location.get("name", ""))

    fetched = "true" if result.get("ok") else "false"
    window.setProperty("Location", city)
    window.setProperty("Current.Location", city)
    window.setProperty("WeatherProvider", config.L(32180))
    window.setProperty("WeatherProviderLogo",
                       os.path.join(config.ADDON_PATH, "icon.png"))
    window.setProperty("Weather.IsFetched", fetched)
    window.setProperty("Current.IsFetched", fetched)
    window.setProperty("Hourly.IsFetched", "false")
    window.setProperty("Daily.IsFetched",
                       "true" if forecast else "false")
    window.setProperty("Forecast.IsFetched", "true" if forecast else "false")
    window.setProperty("Forecast.City", city)
    window.setProperty("Updated", str(result.get("updated", "")))

    code = kodi_code(current.get("condition_key"))
    window.setProperty("Current.Condition", str(current.get("condition") or ""))
    window.setProperty("Current.Temperature", _num(current.get("temp")))
    window.setProperty("Current.FeelsLike", _num(current.get("feels_like")))
    window.setProperty("Current.Wind", _wind_kmh(current))
    window.setProperty("Current.WindDirection", str(current.get("wind_dir") or ""))
    window.setProperty("Current.Humidity", _num(current.get("humidity")))
    window.setProperty("Current.UVIndex", "")
    window.setProperty("Current.DewPoint", "")
    window.setProperty("Current.Precipitation", _num(current.get("rain")))
    window.setProperty("Current.Cloudiness", "")
    window.setProperty("Current.OutlookIcon", "%s.png" % code)
    window.setProperty("Current.FanartCode", str(code))
    window.setProperty("Current.Pressure", _num(current.get("pressure")))
    window.setProperty("Current.WindChill", _num(current.get("feels_like")))
    window.setProperty("Current.Visibility", _num(current.get("visibility")))
    window.setProperty("Current.AQI", _num(current.get("aqi")))
    window.setProperty("Current.PM25", _num(current.get("pm25")))
    window.setProperty("Today.Sunrise", str(current.get("sunrise") or ""))
    window.setProperty("Today.Sunset", str(current.get("sunset") or ""))

    for index, day in enumerate(forecast[:7]):
        info = day.get("day") or {}
        night = day.get("night") or {}
        condition = info.get("condition") or night.get("condition") or ""
        day_code = kodi_code(info.get("key") or "unknown")
        icon = "%s.png" % day_code
        title = weekday_label(day.get("date", ""), index)
        short_date = str(day.get("date", ""))[5:].replace("-", "/")
        high = _num(day.get("high"))
        low = _num(day.get("low"))

        # 新版 Daily.N.*（1 起）
        prefix = "Daily.%d." % (index + 1)
        window.setProperty(prefix + "ShortDate", short_date)
        window.setProperty(prefix + "ShortDay", title)
        window.setProperty(prefix + "HighTemperature",
                           (high + "\u00b0C") if high else "")
        window.setProperty(prefix + "LowTemperature",
                           (low + "\u00b0C") if low else "")
        window.setProperty(prefix + "Outlook", str(condition))
        window.setProperty(prefix + "OutlookIcon", icon)
        window.setProperty(prefix + "FanartCode", str(day_code))
        window.setProperty(prefix + "WindSpeed", str(info.get("wind_power") or ""))
        window.setProperty(prefix + "WindDirection", str(info.get("wind_dir") or ""))
        window.setProperty(prefix + "Precipitation", _num(day.get("precipitation")))

        # 兼容属性 DayN.*（0 起，数值为纯数字）
        compat = "Day%d." % index
        window.setProperty(compat + "Title", title or short_date)
        window.setProperty(compat + "HighTemp", high)
        window.setProperty(compat + "LowTemp", low)
        window.setProperty(compat + "Outlook", str(condition))
        window.setProperty(compat + "OutlookIcon", icon)
        window.setProperty(compat + "FanartCode", str(day_code))

    window.setProperty("Weather.AlertCount", str(len(alerts)))
    for index, alert in enumerate(alerts[:10], start=1):
        prefix = "Weather.Alert%d." % index
        window.setProperty(prefix + "Title", str(alert.get("title", "")))
        window.setProperty(prefix + "Level", str(alert.get("level", "")))

    publish_locations()
    return True


def clear():
    try:
        window = xbmcgui.Window(10000)
        window.clearProperty("Weather.IsFetched")
    except Exception:  # noqa: BLE001
        pass
