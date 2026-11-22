# -*- coding: utf-8 -*-
"""
lib/weatherprovider.py — Kodi「天气」服务的逻辑层（xbmc.python.weather）。

Kodi 通过 RunScript 调用 weather.py 并传入一个参数：
  * ``location1`` / ``location2`` / ``location3`` —— 配置第 N 个地点，
    由 settings.xml 的按钮触发，优先弹出「省份 → 城市」列表选择（零输入，
    适配 PC 端 Kodi 无法输入中文的虚拟键盘），末项保留手动输入兜底；
  * ``1`` / ``2`` / ``3``（或空） —— 抓取第 N 个地点的天气，
    把结果写入 Kodi 天气窗口 Window(12600) 的标准属性。

地点未配置时回退到插件主设置里的当前城市，保证装上就能显示天气。
"""
from __future__ import unicode_literals

import os
import re
import sys

import xbmcgui

from . import config, windowprops
from .citydb import CityDB
from .weather import WeatherService

MAX_LOCATIONS = 3


def run(arg=""):
    arg = str(arg or "").strip()
    # 写日志便于在 kodi.log 里确认 RunScript 是否真的调用了脚本
    config.log("weather provider called: arg=%r argv=%r" %
               (arg, sys.argv[:3]), config.LOGINFO)
    try:
        match = re.match(r"^(?:location|loc)(\d+)$", arg, re.I)
        if match:
            _configure(int(match.group(1)))
            return
        try:
            index = int(arg)
        except (TypeError, ValueError):
            index = 1
        if not 1 <= index <= MAX_LOCATIONS:
            index = 1
        _fetch(index)
    except Exception as exc:  # noqa: BLE001
        config.warn("weather provider failed: %s" % exc)
        _notify("%s: %s" % (config.L(32165), exc))


def _location(index):
    prefix = "location%d" % index
    name = config.get(prefix, "")
    nmc_code = config.get(prefix + "_nmc", "")
    wcn_code = config.get(prefix + "_wcn", "")
    manual = str(config.get(prefix + "_name", "")).strip()
    if manual and (not name or not nmc_code):
        # 备用手动输入框：即使 RunScript 按钮未触发，也能直接填中文城市名
        name, nmc_code, wcn_code = manual, "", ""
    if name and not nmc_code:
        # 兼容直接填入城市名（例如 Kodi 设置里手填、或旧版只写了名称）
        # 用内置城市索引解析出两套数据源编码并回写，避免"点了没数据"。
        try:
            hits = CityDB(debug=config.debug).search(name, limit=1)
            if hits:
                nmc_code = hits[0]["nmc_code"]
                wcn_code = hits[0].get("wcn_code", "")
                config.put(prefix + "_nmc", nmc_code)
                config.put(prefix + "_wcn", wcn_code)
                config.log("resolved location%d %s -> %s" %
                           (index, name, nmc_code), config.LOGINFO)
        except Exception as exc:  # noqa: BLE001
            config.warn("resolve location%d failed: %s" % (index, exc))
    if name and nmc_code:
        return {"name": name, "nmc_code": nmc_code, "wcn_code": wcn_code}
    # 地点未配置时回退到插件主设置（可用插件菜单「切换城市」修改）
    return config.current_location()


def _apply_location(index, hit):
    """把选中的城市写入地点设置并刷新天气。"""
    prefix = "location%d" % index
    config.put(prefix, hit["name"])
    config.put(prefix + "_nmc", hit["nmc_code"])
    config.put(prefix + "_wcn", hit.get("wcn_code", ""))
    if index == 1:
        # 地点 1 与插件菜单共用当前城市
        config.put("city_name", hit["name"])
        config.put("nmc_code", hit["nmc_code"])
        config.put("wcn_code", hit.get("wcn_code", ""))
    windowprops.publish_locations()
    _notify(config.L(32188, hit["name"]))
    _fetch(index)


def _configure(index):
    if not 1 <= index <= MAX_LOCATIONS:
        return
    dialog = xbmcgui.Dialog()
    db = CityDB(debug=config.debug)

    # 优先「省份 → 城市」逐级选择：PC 端 Kodi 虚拟键盘打不出中文，
    # 用 Dialog().select 全程方向键操作，零输入。
    provinces = db.provinces()
    options = list(provinces)
    options.append(config.L(32104))  # 末项保留手动输入，供愿意打字的平台使用
    try:
        picked = dialog.select(config.L(32192), options)
    except Exception:  # noqa: BLE001
        picked = -1
    if picked < 0:
        return

    if picked < len(provinces):
        province = provinces[picked]
        cities = db.cities_in_province(province)
        if not cities:
            _notify(config.L(32187))
            return
        try:
            cpick = dialog.select(
                config.L(32186),
                ["%s  %s" % (c["name"], c["nmc_code"]) for c in cities])
        except Exception:  # noqa: BLE001
            cpick = -1
        if cpick < 0:
            return
        _apply_location(index, cities[cpick])
        return

    # 手动输入兜底（原路径）
    try:
        query = dialog.input(config.L(32104), "",
                             type=getattr(xbmcgui, "INPUT_ALPHANUM", 0))
    except Exception:  # noqa: BLE001
        query = ""
    query = str(query or "").strip()
    if not query:
        return
    hits = db.search(query, limit=50)
    if not hits:
        _notify(config.L(32187))
        return
    try:
        pick = dialog.select(config.L(32186), [h["display"] for h in hits])
    except Exception:  # noqa: BLE001
        pick = -1
    if pick < 0:
        return
    _apply_location(index, hits[pick])


def _fetch(index):
    location = _location(index)
    try:
        result = WeatherService().fetch_all(location=location)
    except Exception as exc:  # noqa: BLE001
        config.warn("weather provider fetch failed: %s" % exc)
        return
    windowprops.publish_weather(result, index)
    try:
        windowprops.publish(result)
    except Exception:  # noqa: BLE001
        pass


def _notify(message):
    try:
        xbmcgui.Dialog().notification(
            config.L(32180), str(message),
            os.path.join(config.ADDON_PATH, "icon.png"), 3000)
    except Exception:  # noqa: BLE001
        pass
