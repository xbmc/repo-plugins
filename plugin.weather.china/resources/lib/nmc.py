# -*- coding: utf-8 -*-
"""
lib/nmc.py — 中央气象台（nmc.cn）数据源：接口调用与数据格式解析。

接口链（详见 docs/DATA_SOURCE.md）：
  GET /rest/province                     -> 34 个省级行政区 [{code,name,url}]
  GET /rest/province/{code}              -> 省内站点 [{code,province,city,url}]
  GET /rest/weather?stationid={code}     -> {msg,code,data:{real,predict,air,...}}
  GET /rest/findAlarm?pageNo&pageSize    -> {data:{page:{list},provinceAlarms,stat}}

关键解析规则：
  * 缺失值哨兵是字符串 "9999"（温度也用 9999.0）、"-"、空串，统一转 None；
  * real.weather.info 常为 "-"，此时用 predict.detail[0] 的天气描述兜底；
  * predict.detail 共 7 天；第 0 天白天数据常为 9999（白天已过），高温记 None；
  * real.warn 中 alert=="9999" 表示当前无预警；
  * 所有文本按 UTF-8（接口已声明 application/json;charset=UTF-8）。
"""
from __future__ import unicode_literals

import time

from . import alerts, config, icons

CURRENT_FIELDS = (
    "temp", "feels_like", "humidity", "pressure", "rain",
    "condition", "condition_key", "condition_icon",
    "wind_dir", "wind_power", "wind_speed",
    "aqi", "pm25", "visibility", "sunrise", "sunset", "time",
)


def num(value):
    """把 '9' / 7.8 / '9999' 统一成数字或 None。"""
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "-", "--", "9999", "9999.0", "None", "null"):
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    if number >= 9998 or number <= -9998:
        return None
    return int(number) if number == int(number) else round(number, 1)


def txt(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in ("-", "--", "9999", "None", "null") else text


def blank(location=None):
    current = {key: None for key in CURRENT_FIELDS}
    return {
        "ok": False,
        "source": "",
        "source_list": [],
        "location": location or {},
        "updated": "",
        "current": current,
        "forecast": [],
        "alerts": [],
        "indices": [],
        "notes": [],
        "errors": [],
        "cached": False,
        "stale": False,
        "fetched_at": 0,
    }


class NMCSource(object):
    def __init__(self, fetcher, debug=None):
        self.fetcher = fetcher
        self._debug = debug or (lambda msg: None)

    # ------------------------------------------------------------ 站点目录
    def provinces(self, force=False):
        payload, meta = self.fetcher.get_json(
            config.NMC_PROVINCES, referer=config.NMC_REFERER,
            ttl=86400, force=force)
        return (payload if isinstance(payload, list) else []), meta

    def stations(self, province_code, force=False):
        payload, meta = self.fetcher.get_json(
            config.NMC_STATIONS.format(code=province_code),
            referer=config.NMC_REFERER, ttl=86400, force=force)
        return (payload if isinstance(payload, list) else []), meta

    # ------------------------------------------------------------ 天气
    def weather(self, station_code, location=None, force=False):
        if not station_code:
            return None, None
        url = config.NMC_WEATHER.format(code=station_code)
        payload, meta = self.fetcher.get_json(
            url, referer=config.NMC_REFERER,
            ttl=config.get_int("cache_ttl", 10, 1, 1440) * 60, force=force)
        if payload is None:
            self._debug("nmc weather failed: %s" % (meta.error if meta else "?"))
            return None, meta
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or not data:
            self._debug("nmc weather: empty data (stationid 可能无效)")
            return None, meta
        result = self.parse(data, location or {})
        result["cached"] = bool(meta and meta.cached)
        result["stale"] = bool(meta and meta.stale)
        return result, meta

    def parse(self, data, location):
        result = blank(location)
        result["ok"] = True
        result["source"] = "nmc"
        result["source_list"] = ["nmc"]
        result["fetched_at"] = int(time.time())

        real = data.get("real") or {}
        predict = data.get("predict") or {}
        detail = predict.get("detail") or []
        weather = real.get("weather") or {}
        wind = real.get("wind") or {}
        sun = real.get("sunriseSunset") or {}

        first_text = ""
        if detail:
            first = detail[0]
            first_text = (txt(((first.get("day") or {}).get("weather") or {}).get("info")) or
                          txt(((first.get("night") or {}).get("weather") or {}).get("info")))
        cond = icons.resolve(code=weather.get("img"),
                             text=txt(weather.get("info")) or first_text)

        current = result["current"]
        current.update({
            "temp": num(weather.get("temperature")),
            "feels_like": num(weather.get("feelst")),
            "humidity": num(weather.get("humidity")),
            "pressure": num(weather.get("airpressure")),
            "rain": num(weather.get("rain")),
            "condition": txt(weather.get("info")) or first_text or cond["zh"],
            "condition_key": cond["key"],
            "condition_icon": cond["icon"],
            "wind_dir": txt(wind.get("direct")),
            "wind_power": txt(wind.get("power")),
            "wind_speed": num(wind.get("speed")),
            "visibility": None,
            "sunrise": _clock(sun.get("sunrise")),
            "sunset": _clock(sun.get("sunset")),
            "time": _clock(real.get("publish_time")),
        })
        _fill_air(current, data.get("air"))

        result["updated"] = txt(real.get("publish_time")) or txt(predict.get("publish_time"))

        for item in detail[:7]:
            day_w = ((item.get("day") or {}).get("weather") or {})
            night_w = ((item.get("night") or {}).get("weather") or {})
            day_wind = ((item.get("day") or {}).get("wind") or {})
            night_wind = ((item.get("night") or {}).get("wind") or {})
            day_cond = icons.resolve(day_w.get("img"), txt(day_w.get("info")))
            night_cond = icons.resolve(night_w.get("img"), txt(night_w.get("info")))
            result["forecast"].append({
                "date": txt(item.get("date")),
                "high": num(day_w.get("temperature")),
                "low": num(night_w.get("temperature")),
                "day": {
                    "condition": txt(day_w.get("info")),
                    "key": day_cond["key"], "icon": day_cond["icon"],
                    "wind_dir": txt(day_wind.get("direct")),
                    "wind_power": txt(day_wind.get("power")),
                },
                "night": {
                    "condition": txt(night_w.get("info")),
                    "key": night_cond["key"], "icon": night_cond["icon"],
                    "wind_dir": txt(night_wind.get("direct")),
                    "wind_power": txt(night_wind.get("power")),
                },
                "precipitation": num(item.get("precipitation")),
            })

        local_alert = alerts.from_nmc_warn(real.get("warn"), location.get("name", ""))
        if local_alert:
            result["alerts"].append(local_alert)
        return result

    # ------------------------------------------------------------ 全国预警
    def national_alerts(self, limit=30, force=False):
        page_size = min(100, max(10, int(limit)))
        url = config.NMC_ALARMS.format(page=1, size=page_size)
        payload, meta = self.fetcher.get_json(
            url, referer=config.NMC_REFERER, ttl=300, force=force)
        if payload is None:
            return [], meta
        data = payload.get("data") or {}
        page = data.get("page") or {}
        raw_items = list(page.get("list") or [])
        raw_items.extend(data.get("provinceAlarms") or [])
        out = []
        for item in raw_items:
            alert = alerts.from_nmc_list(item)
            if alert:
                out.append(alert)
        return out, meta


def _clock(value):
    """'2026-11-16 06:59' -> '06:59'；已是 HH:MM 则原样返回。"""
    text = txt(value)
    if not text:
        return ""
    if " " in text:
        return text.split(" ", 1)[1][:5]
    return text[:5]


def _fill_air(current, air):
    """中央气象台 /rest/weather 的 data.air 字段在不同版本结构不一，宽松提取。"""
    if not isinstance(air, dict):
        return
    for key in ("aqi", "AQI", "aqiValue", "value"):
        if air.get(key) not in (None, "", "9999"):
            current["aqi"] = num(air.get(key))
            break
    for key in ("pm25", "PM25", "pm2_5", "pm25Value"):
        if air.get(key) not in (None, "", "9999"):
            current["pm25"] = num(air.get(key))
            break
