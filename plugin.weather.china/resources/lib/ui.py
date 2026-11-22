# -*- coding: utf-8 -*-
"""
lib/ui.py — Kodi 界面层：目录构建、中文搜索交互、详情查看与导航。

所有可见文本都经 config.L() 取词（resources/language/*/strings.po）。
插件 URL 参数一律用 urllib.parse.urlencode(encoding="utf-8") 编码、
parse_qs(encoding="utf-8") 解码，保证中文城市名在 Kodi 内部传递不乱码。

页面均为「目录 + 文本查看器」组合：点击数据行弹出详情后重绘本页，
避免使用播放器路径，也不需要依赖任何皮肤文件。
"""
from __future__ import unicode_literals

import datetime
import os
import sys
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

from . import alerts, config, icons, windowprops
from .citydb import CityDB
from .weather import WeatherService

try:
    HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else 0
except (TypeError, ValueError):
    # 被 RunScript 误当作插件调用时也不应崩溃（正常路径由 default.py 判别）
    HANDLE = 0
PLUGIN_URL = sys.argv[0] if len(sys.argv) > 0 else "plugin://plugin.weather.china/"

ICON_PATH = os.path.join(config.ADDON_PATH, "icon.png")
FANART_PATH = os.path.join(config.ADDON_PATH, "fanart.jpg")


# ---------------------------------------------------------------- URL / 参数
def _url(action, **kwargs):
    data = {"action": action}
    for key, value in kwargs.items():
        if value is not None and value != "":
            data[key] = value
    # 显式 UTF-8：中文城市名在 percent-encode 后由 parse_qs 原样还原
    return PLUGIN_URL + "?" + urllib.parse.urlencode(data, encoding="utf-8")


def _params():
    if len(sys.argv) < 3 or not sys.argv[2]:
        return {}
    query = sys.argv[2].lstrip("?")
    parsed = urllib.parse.parse_qs(query, encoding="utf-8",
                                   errors="replace", keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items()}


# ---------------------------------------------------------------- 基础控件
def _add(label, label2="", icon="", url=None, folder=True, category=None):
    item = xbmcgui.ListItem(label=str(label), label2=str(label2 or ""))
    art = {"fanart": FANART_PATH}
    if icon:
        art["icon"] = icon
        art["thumb"] = icon
    item.setArt(art)
    if category:
        item.setProperty("category", str(category))
    xbmcplugin.addDirectoryItem(HANDLE, url or "", item, isFolder=folder)
    return item


def _finish(category=None):
    if category:
        xbmcplugin.setPluginCategory(HANDLE, category)
    xbmcplugin.setContent(HANDLE, "files")
    xbmcplugin.endOfDirectory(HANDLE)


def _notify(message, title=None, duration=3000):
    try:
        xbmcgui.Dialog().notification(title or config.L(32180), str(message),
                                      ICON_PATH, duration)
    except Exception:  # noqa: BLE001
        pass


def _text(title, body):
    try:
        xbmcgui.Dialog().textviewer(str(title), str(body))
    except Exception:  # noqa: BLE001
        _notify(body, str(title))


def _color(text, argb):
    return "[COLOR %s]%s[/COLOR]" % (argb, text)


def _weekday(date_str, index):
    if index == 0:
        return config.L(32117)
    if index == 1:
        return config.L(32118)
    if index == 2:
        return config.L(32119)
    try:
        return config.L(32200 + datetime.date.fromisoformat(date_str).weekday())
    except (ValueError, TypeError):
        return ""


def _short_date(date_str):
    return date_str[5:].replace("-", "/") if len(date_str) >= 10 else date_str


def _source_name(source):
    return {"nmc": config.L(32150), "wcn": config.L(32151),
            "mixed": "%s + %s" % (config.L(32150), config.L(32151))}.get(
                source, source or config.L(32137))


def _status_suffix(result):
    if "stale" in result.get("notes", []):
        return " " + config.L(32153)
    if "cached" in result.get("notes", []):
        return " " + config.L(32152)
    return ""


# ---------------------------------------------------------------- 页面：根
def _render_root(params, result):
    location = result.get("location") or {}
    current = result.get("current") or {}
    city = location.get("name", config.L(32137))
    heading = "%s  %s  %s" % (
        city, config.format_temp(current.get("temp")),
        current.get("condition") or config.L(32137))
    _add(_color(heading, "FF4FC3F7") + _status_suffix(result),
         "%s · %s" % (config.L(32159), _source_name(result.get("source"))),
         current.get("condition_icon") or ICON_PATH,
         _url("current"), folder=True)

    alert_count = len(result.get("alerts") or [])
    _add(config.L(32100), config.L(32135) + "：%s" % (result.get("updated") or config.DASH),
         icons.icon_path("sunny"), _url("current"), folder=True)
    _add(config.L(32101, config.get_int("forecast_days", 7, 3, 7)),
         config.L(32158),
         icons.icon_path("partly_cloudy"), _url("forecast"), folder=True)
    _add(config.L(32102), config.L(32157, alert_count),
         icons.alert_icon("red" if alert_count else "unknown"),
         _url("alerts"), folder=True)
    _add(config.L(32103), city, ICON_PATH, _url("city_picker"), folder=True)
    _add(config.L(32105), config.L(32150),
         icons.alert_icon("orange"), _url("national"), folder=True)
    if result.get("indices"):
        _add(config.L(32155), config.L(32157, len(result["indices"])),
             icons.icon_path("haze"), _url("indices"), folder=True)
    _add(config.L(32110), config.L(32168), ICON_PATH, _url("refresh"), folder=True)
    _add(config.L(32106), "", ICON_PATH, _url("refresh_cities"), folder=True)
    _add(config.L(32107), "", ICON_PATH, _url("settings"), folder=True)

    if not result.get("ok"):
        _add(_color(config.L(32109), "FFFF5252"),
             "; ".join(result.get("errors") or [])[:120],
             icons.icon_path("unknown"), _url("settings"), folder=True)


# ---------------------------------------------------------------- 页面：实况
def _render_current(params, result):
    cur = result.get("current") or {}
    rows = [
        (32122, config.format_temp(cur.get("temp"))),
        (32123, config.format_temp(cur.get("feels_like"))),
        (32170, cur.get("condition") or config.DASH),
        (32124, config.format_value(cur.get("humidity"), "%")),
        (32125, config.format_value(cur.get("pressure"), " hPa")),
        (32126, config.format_value(cur.get("rain"), " mm")),
        (32127, cur.get("wind_dir") or config.DASH),
        (32128, cur.get("wind_power") or config.DASH),
        (32129, config.format_value(cur.get("wind_speed"), " m/s")),
        (32130, config.format_value(cur.get("visibility"), " km")),
        (32131, config.format_value(cur.get("aqi"))),
        (32132, config.format_value(cur.get("pm25"))),
        (32133, cur.get("sunrise") or config.DASH),
        (32134, cur.get("sunset") or config.DASH),
        (32135, result.get("updated") or cur.get("time") or config.DASH),
        (32136, _source_name(result.get("source"))),
    ]
    for label_id, value in rows:
        _add("%s：%s" % (config.L(label_id), value), "",
             cur.get("condition_icon") or ICON_PATH, _url("current"), folder=True)
    _add(config.L(32110), "", ICON_PATH, _url("refresh"), folder=True)


# ---------------------------------------------------------------- 页面：预报
def _render_forecast(params, result):
    forecast = result.get("forecast") or []
    if not forecast:
        _add(config.L(32108), "", icons.icon_path("unknown"),
             _url("forecast"), folder=True)
        return
    for index, day in enumerate(forecast):
        weekday = _weekday(day.get("date", ""), index)
        label = "%s %s   %s / %s" % (
            weekday, _short_date(day.get("date", "")),
            config.format_temp(day.get("high")),
            config.format_temp(day.get("low")))
        day_info = day.get("day") or {}
        night_info = day.get("night") or {}
        condition = day_info.get("condition") or night_info.get("condition") or config.DASH
        label2 = "%s  %s  %s" % (condition,
                                 day_info.get("wind_dir") or config.DASH,
                                 day_info.get("wind_power") or config.DASH)
        _add(label, label2, day_info.get("icon") or icons.icon_path("unknown"),
             _url("forecast_detail", idx=index), folder=True)


def _forecast_detail_text(day, index):
    day_info = day.get("day") or {}
    night_info = day.get("night") or {}
    weekday = _weekday(day.get("date", ""), index)
    lines = [
        "%s %s" % (weekday, day.get("date", "")),
        "%s：%s / %s" % (config.L(32154),
                         config.format_temp(day.get("high")),
                         config.format_temp(day.get("low"))),
        "",
        "%s  %s：%s  %s  %s" % (config.L(32120), config.L(32170),
                                day_info.get("condition") or config.DASH,
                                day_info.get("wind_dir") or "",
                                day_info.get("wind_power") or ""),
        "%s  %s：%s  %s  %s" % (config.L(32121), config.L(32170),
                                night_info.get("condition") or config.DASH,
                                night_info.get("wind_dir") or "",
                                night_info.get("wind_power") or ""),
    ]
    if day.get("precipitation") is not None:
        lines.append("%s：%s mm" % (config.L(32126), day["precipitation"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- 页面：预警
def _render_alerts(params, result, national=None, title=None):
    if national is not None:
        items = national
        back = "national"
    else:
        items = result.get("alerts") or []
        back = "alerts"
    if not items:
        _add(config.L(32139), config.L(32175),
             icons.alert_icon("unknown"), _url(back), folder=True)
    else:
        for index, alert in enumerate(items):
            label = "%s  %s" % (
                _color("[%s]" % alert.get("level", ""), alert.get("level_color", "FF9AA0A6")),
                alert.get("title", "") or alert.get("type", ""))
            label2 = "%s · %s · %s" % (alert.get("type") or config.L(32137),
                                       alert.get("issue_time") or config.DASH,
                                       _source_name("nmc" if alert.get("source", "").startswith("nmc") else "wcn"))
            _add(label, label2, alert.get("icon") or icons.alert_icon("unknown"),
                 _url("alert_detail", idx=index, back=back, scope=back), folder=True)
            # 把详情文本暂存到内存，供同一进程内的 textviewer 使用
            _ALERT_CACHE[back] = items
    _add(config.L(32105), "", icons.alert_icon("orange"),
         _url("national"), folder=True)
    _add(config.L(32110), "", ICON_PATH, _url("refresh"), folder=True)


_ALERT_CACHE = {}


def _alert_detail_text(alert):
    return "\n".join([
        alert.get("title", ""),
        "",
        "%s：%s" % (config.L(32141), alert.get("issuer") or config.DASH),
        "%s：%s" % (config.L(32142), alert.get("type") or config.DASH),
        "%s：%s" % (config.L(32143), alert.get("level") or config.L(32149)),
        "%s：%s" % (config.L(32144), alert.get("issue_time") or config.DASH),
        "%s：%s" % (config.L(32136), _source_name(
            "nmc" if alert.get("source", "").startswith("nmc") else "wcn")),
        "",
        config.L(32171) + "：",
        alert.get("content") or alert.get("title") or config.DASH,
    ])


# ---------------------------------------------------------------- 页面：城市
def _render_city_picker(params, result):
    # 放在首位：PC 端 Kodi 虚拟键盘打不出中文时，用方向键逐级选择即可
    _add(_color(config.L(32192), "FF4FC3F7"), config.L(32193),
         ICON_PATH, _url("city_provinces"), folder=True)
    _add(_color(config.L(32104), "FF4FC3F7"), config.L(32111),
         ICON_PATH, _url("city_input"), folder=True)
    _add(config.L(32160), "", ICON_PATH, _url("city_popular"), folder=True)
    _add(config.L(32159), (result.get("location") or {}).get("name", ""),
         ICON_PATH, _url("root"), folder=True)


def _render_city_provinces():
    """列出全部省份，纯方向键选择，零输入。"""
    provinces = CityDB(debug=config.debug).provinces()
    for prov in provinces:
        _add(prov, "", ICON_PATH,
             _url("city_by_province", prov=prov), folder=True)
    _add(config.L(32159), "", ICON_PATH, _url("city_picker"), folder=True)


def _render_city_by_province(province):
    """列出指定省份下全部站点，点击即选中该城市。"""
    cities = CityDB(debug=config.debug).cities_in_province(province)
    for hit in cities:
        _add(hit["display"],
             "%s / %s" % (hit["nmc_code"], hit["wcn_code"] or config.L(32138)),
             ICON_PATH,
             _url("city_select", name=hit["name"], code=hit["nmc_code"],
                  wcode=hit["wcn_code"]), folder=True)
    if not cities:
        _add(config.L(32113), province, icons.icon_path("unknown"),
             _url("city_provinces"), folder=True)
    _add(config.L(32159), province, ICON_PATH,
         _url("city_provinces"), folder=True)


def _render_city_results(query, result):
    if not query:
        _render_city_picker({}, result)
        return
    city_db = CityDB(debug=config.debug)
    hits = city_db.search(query, limit=50)
    if not hits:
        _add(config.L(32113), query, icons.icon_path("unknown"),
             _url("city_input"), folder=True)
        return
    for hit in hits:
        _add(hit["display"],
             "%s / %s" % (hit["nmc_code"], hit["wcn_code"] or config.L(32138)),
             ICON_PATH,
             _url("city_select", name=hit["name"], code=hit["nmc_code"],
                  wcode=hit["wcn_code"]), folder=True)


# ---------------------------------------------------------------- 页面：生活指数
def _render_indices(params, result):
    indices = result.get("indices") or []
    if not indices:
        _add(config.L(32108), "", icons.icon_path("unknown"),
             _url("root"), folder=True)
        return
    for index, entry in enumerate(indices):
        _add("%s：%s" % (entry.get("name"), entry.get("hint") or config.DASH),
             (entry.get("desc") or "")[:90], icons.icon_path("sunny"),
             _url("index_detail", idx=index), folder=True)


# ---------------------------------------------------------------- 路由
def run():
    params = _params()
    action = params.get("action", "root")
    config.debug("action=%s params=%s" % (action, params))
    service = WeatherService()
    result = None

    if action == "settings":
        try:
            config.ADDON.openSettings()
        except Exception:  # noqa: BLE001
            pass
        result = service.fetch_all()
        _render_root(params, result)
        _finish(config.L(32107))
        return

    if action == "refresh":
        service.clear_cache()
        result = service.fetch_all(force=True)
        windowprops.publish(result)
        _notify(config.L(32168))
        _render_root(params, result)
        _finish(config.L(32110))
        return

    if action == "refresh_cities":
        count = service.refresh_cities(force=True)
        _notify(config.L(32115, count) if count else config.L(32116))
        result = service.fetch_all()
        _render_root(params, result)
        _finish(config.L(32106))
        return

    if action == "city_select":
        name = params.get("name", "")
        CityDB(debug=config.debug).select({
            "name": name,
            "nmc_code": params.get("code", ""),
            "wcn_code": params.get("wcode", ""),
        })
        service.clear_cache()
        result = service.fetch_all(force=True)
        windowprops.publish(result)
        _notify(config.L(32114, name))
        _render_root(params, result)
        _finish(config.L(32103))
        return

    if action == "city_provinces":
        _render_city_provinces()
        _finish(config.L(32192))
        return

    if action == "city_by_province":
        _render_city_by_province(params.get("prov", ""))
        _finish(params.get("prov", config.L(32192)))
        return

    if action == "city_input":
        query = ""
        try:
            query = xbmcgui.Dialog().input(
                config.L(32104), "", type=getattr(xbmcgui, "INPUT_ALPHANUM", 0))
        except Exception:  # noqa: BLE001
            pass
        result = service.fetch_all()
        _render_city_results(str(query or "").strip(), result)
        _finish(config.L(32112))
        return

    if action == "city_results":
        result = service.fetch_all()
        _render_city_results(params.get("q", ""), result)
        _finish(config.L(32112))
        return

    if action == "city_popular":
        result = service.fetch_all()
        _add(config.L(32104), config.L(32111), ICON_PATH,
             _url("city_input"), folder=True)
        for hit in CityDB(debug=config.debug).popular():
            _add(hit["display"], hit["nmc_code"], ICON_PATH,
                 _url("city_select", name=hit["name"], code=hit["nmc_code"],
                      wcode=hit["wcn_code"]), folder=True)
        _finish(config.L(32160))
        return

    # 以下页面都需要天气数据
    result = service.fetch_all()
    windowprops.publish(result)

    if action in ("root", ""):
        _render_root(params, result)
        _finish(config.L(32180))
    elif action == "current":
        _render_current(params, result)
        _finish(config.L(32100))
    elif action == "forecast":
        _render_forecast(params, result)
        _finish(config.L(32101, config.get_int("forecast_days", 7, 3, 7)))
    elif action == "forecast_detail":
        try:
            index = int(params.get("idx", 0))
            day = result["forecast"][index]
            _text(day.get("date", "") or config.L(32101, 1),
                  _forecast_detail_text(day, index))
        except (IndexError, ValueError, KeyError):
            pass
        _render_forecast(params, result)
        _finish(config.L(32101, config.get_int("forecast_days", 7, 3, 7)))
    elif action == "alerts":
        _render_alerts(params, result)
        _finish(config.L(32102))
    elif action == "national":
        national, meta = service.national_alerts()
        _render_alerts(params, result, national=national)
        _finish(config.L(32105))
    elif action == "alert_detail":
        scope = params.get("scope", "alerts")
        if scope == "national":
            items, meta = service.national_alerts()
        else:
            items = result.get("alerts") or []
        try:
            alert = items[int(params.get("idx", 0))]
            _text(config.L(32140), _alert_detail_text(alert))
        except (IndexError, ValueError, KeyError):
            pass
        if scope == "national":
            _render_alerts(params, result, national=items)
            _finish(config.L(32105))
        else:
            _render_alerts(params, result)
            _finish(config.L(32102))
    elif action == "indices":
        _render_indices(params, result)
        _finish(config.L(32155))
    elif action == "index_detail":
        try:
            entry = result["indices"][int(params.get("idx", 0))]
            _text(entry.get("name", ""), entry.get("desc") or entry.get("hint", ""))
        except (IndexError, ValueError, KeyError):
            pass
        _render_indices(params, result)
        _finish(config.L(32155))
    elif action == "city_picker":
        _render_city_picker(params, result)
        _finish(config.L(32103))
    else:
        _render_root(params, result)
        _finish(config.L(32180))
