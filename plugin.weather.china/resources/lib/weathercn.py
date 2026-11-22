# -*- coding: utf-8 -*-
"""
lib/weathercn.py — 中国天气网（weather.com.cn）备用/补充数据源。

接口（均无需 Key，必须带 Referer: http://www.weather.com.cn/）：
  GET http://d1.weather.com.cn/weather_index/{9位码}.html
      -> JS 变量 cityDZ / alarmDZ / dataSK / dataZS / fc
         dataSK = 实况；fc.f = 5 天预报；alarmDZ.w = 预警；dataZS.zs = 生活指数
  GET http://d1.weather.com.cn/dingzhi/{9位码}.html
      -> cityDZ{code} / alarmDZ{code}.w（预警字段 w1..w11，更新更及时）
  GET http://www.weather.com.cn/weather/{9位码}.shtml
      -> HTML 页面 <ul class="t clearfix"> 内 7 个 li = 7 天预报

返回体是 JavaScript 赋值而非纯 JSON，因此用「括号平衡扫描」把每个
`var NAME = {...};` 的 JSON 片段切出来再 json.loads（见 parse_js_vars）。
所有内容按 UTF-8 解码，数字字段统一经 num() 归一化。
"""
from __future__ import unicode_literals

import datetime
import json
import re
import time

from . import alerts, config, icons
from .nmc import blank, num, txt

_JS_VAR = re.compile(r"var\s+([A-Za-z_]\w*)\s*=\s*")
_UL_BLOCK = re.compile(r'<ul class="t clearfix">(.*?)</ul>', re.S)
_LI = re.compile(r"<li[^>]*>(.*?)</li>", re.S)
_TAG = re.compile(r"<[^>]+>")


def parse_js_vars(text):
    """'var a ={...};var b ={...};' -> {'a': {...}, 'b': {...}}。"""
    result = {}
    if not text:
        return result
    for match in _JS_VAR.finditer(text):
        start = match.end()
        end = _json_end(text, start)
        if end <= start:
            continue
        try:
            result[match.group(1)] = json.loads(text[start:end])
        except (ValueError, TypeError):
            continue
    return result


def _json_end(text, start):
    if start >= len(text) or text[start] not in "{[":
        return -1
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(text)):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
            if depth == 0:
                return pos + 1
    return -1


def _pick(variables, prefix):
    if prefix in variables:
        return variables[prefix]
    for key, value in variables.items():
        if key.startswith(prefix):
            return value
    return None


def _clean(text):
    return _TAG.sub("", str(text or "")).replace("&nbsp;", " ").strip()


def _percent(value):
    value = txt(value).replace("%", "")
    return num(value)


def _speed(value):
    """'8km/h' -> 8.0"""
    match = re.search(r"[\d.]+", str(value or ""))
    return num(match.group(0)) if match else None


def _full_date(short):
    """'11/16' -> '2026-11-16'（跨年时自动 +1 年）。"""
    parts = txt(short).split("/")
    if len(parts) != 2:
        return ""
    try:
        month, day = int(parts[0]), int(parts[1])
    except ValueError:
        return ""
    today = datetime.date.today()
    year = today.year
    if month < today.month - 6:
        year += 1
    try:
        return datetime.date(year, month, day).isoformat()
    except ValueError:
        return ""


class WCNSource(object):
    def __init__(self, fetcher, debug=None):
        self.fetcher = fetcher
        self._debug = debug or (lambda msg: None)

    def _ttl(self):
        return config.get_int("cache_ttl", 10, 1, 1440) * 60

    # ------------------------------------------------------------ 综合接口
    def index(self, wcode, location=None, force=False):
        if not wcode:
            return None, None
        url = config.WCN_INDEX.format(code=wcode)
        result_obj = self.fetcher.get(
            url, referer=config.WCN_REFERER, ttl=self._ttl(), force=force)
        meta = result_obj
        if not result_obj.ok:
            self._debug("wcn index failed: %s" % result_obj.error)
            return None, meta
        variables = parse_js_vars(result_obj.text)
        if not variables:
            self._debug("wcn index: 未解析出 JS 变量")
            return None, meta
        result = self.parse_index(variables, location or {})
        result["cached"] = result_obj.cached
        result["stale"] = result_obj.stale
        return result, meta

    def parse_index(self, variables, location):
        result = blank(location)
        result["ok"] = True
        result["source"] = "wcn"
        result["source_list"] = ["wcn"]
        result["fetched_at"] = int(time.time())

        sk = _pick(variables, "dataSK") or {}
        city = _pick(variables, "cityDZ") or {}
        city_info = city.get("weatherinfo", {}) if isinstance(city, dict) else {}
        cond = icons.resolve(code=sk.get("weathercode"), text=sk.get("weather"))

        current = result["current"]
        current.update({
            "temp": num(sk.get("temp")),
            "feels_like": None,
            "humidity": _percent(sk.get("sd") or sk.get("SD")),
            "pressure": num(sk.get("qy")),
            "rain": num(sk.get("rain")),
            "condition": txt(sk.get("weather")) or txt(city_info.get("weather")) or cond["zh"],
            "condition_key": cond["key"],
            "condition_icon": cond["icon"],
            "wind_dir": txt(sk.get("WD")) or txt(city_info.get("wd")),
            "wind_power": txt(sk.get("WS")) or txt(city_info.get("ws")),
            "wind_speed": _speed(sk.get("wse")),
            "aqi": num(sk.get("aqi")),
            "pm25": num(sk.get("aqi_pm25")),
            "visibility": _speed(sk.get("njd")),
            "time": txt(sk.get("time")),
        })
        result["updated"] = txt(city_info.get("fctime")) or txt(sk.get("date"))

        fc = _pick(variables, "fc") or {}
        for entry in (fc.get("f") or [])[:7]:
            day_cond = icons.resolve(code=entry.get("fa"), text=None)
            night_cond = icons.resolve(code=entry.get("fb"), text=None)
            # fa/fb 只有代码，用 conditions.json 的中文名反查
            result["forecast"].append({
                "date": _full_date(entry.get("fi")),
                "high": num(entry.get("fc")),
                "low": num(entry.get("fd")),
                "day": {
                    "condition": day_cond["zh"], "key": day_cond["key"],
                    "icon": day_cond["icon"],
                    "wind_dir": txt(entry.get("fe")),
                    "wind_power": txt(entry.get("fg")),
                },
                "night": {
                    "condition": night_cond["zh"], "key": night_cond["key"],
                    "icon": night_cond["icon"],
                    "wind_dir": txt(entry.get("ff")),
                    "wind_power": txt(entry.get("fh")),
                },
                "precipitation": None,
            })

        alarm = _pick(variables, "alarmDZ") or {}
        for item in (alarm.get("w") or []):
            normalized = alerts.from_wcn(item, location.get("name", ""))
            if normalized:
                result["alerts"].append(normalized)

        zs = _pick(variables, "dataZS") or {}
        entries = zs.get("zs", {}) if isinstance(zs, dict) else {}
        for key in sorted(entries):
            if not key.endswith("_name"):
                continue
            prefix = key[:-5]
            result["indices"].append({
                "name": txt(entries.get(key)),
                "hint": txt(entries.get(prefix + "_hint")),
                "desc": txt(entries.get(prefix + "_des_s")),
            })
        return result

    # ------------------------------------------------------------ 预警补充
    def dingzhi(self, wcode, location=None, force=False):
        if not wcode:
            return [], None
        result_obj = self.fetcher.get(
            config.WCN_DINGZHI.format(code=wcode),
            referer=config.WCN_REFERER, ttl=self._ttl(), force=force)
        meta = result_obj
        if not result_obj.ok:
            return [], meta
        variables = parse_js_vars(result_obj.text)
        alarm = _pick(variables, "alarmDZ") or {}
        out = []
        for item in (alarm.get("w") or []):
            normalized = alerts.from_wcn(item, (location or {}).get("name", ""))
            if normalized:
                out.append(normalized)
        return out, meta

    # ------------------------------------------------------------ 7 天预报页
    def seven_day(self, wcode, force=False):
        if not wcode:
            return [], None
        result_obj = self.fetcher.get(
            config.WCN_7DAY.format(code=wcode),
            referer=config.WCN_REFERER, ttl=1800, force=force)
        meta = result_obj
        if not result_obj.ok:
            return [], meta
        return self.parse_7day(result_obj.text), meta

    @staticmethod
    def parse_7day(html):
        match = _UL_BLOCK.search(html or "")
        if not match:
            return []
        out = []
        today = datetime.date.today()
        for idx, li in enumerate(_LI.findall(match.group(1))):
            heading = re.search(r"<h1>(.*?)</h1>", li, re.S)
            wea = re.search(r'<p[^>]*class="wea"[^>]*>(.*?)</p>', li, re.S)
            wea_title = re.search(r'title="([^"]+)"\s+class="wea"', li)
            tem = re.search(r'<p class="tem">(.*?)</p>', li, re.S)
            win = re.search(r'<p class="win">(.*?)</p>', li, re.S)
            big_codes = re.findall(r'<big class="[^"]*?([dn]\d{2})[^"]*"', li)

            high = low = None
            if tem:
                span = re.search(r"<span>(.*?)</span>", tem.group(1), re.S)
                italic = re.search(r"<i>(.*?)</i>", tem.group(1), re.S)
                high = num(_clean(span.group(1))) if span else None
                low = num(_clean(italic.group(1)).replace("℃", "")) if italic else None

            wind_text = _clean(win.group(1)) if win else ""
            wind_dirs = re.findall(r'title="([^"]+)"', win.group(1)) if win else []
            day_code = next((c for c in big_codes if c.startswith("d")), None)
            night_code = next((c for c in big_codes if c.startswith("n")), None)
            day_cond = icons.resolve(code=day_code, text=None)
            night_cond = icons.resolve(code=night_code, text=None)
            condition = (wea_title.group(1) if wea_title else
                         _clean(wea.group(1)) if wea else "")
            heading_text = _clean(heading.group(1)) if heading else ""
            # 页面只给「16日（今天）」，用相对偏移还原完整日期，避免跨年歧义
            date = (today + datetime.timedelta(days=idx)).isoformat()

            out.append({
                "date": date,
                "label": heading_text,
                "high": high,
                "low": low,
                "condition": condition,
                "day": {
                    "condition": condition, "key": day_cond["key"],
                    "icon": day_cond["icon"],
                    "wind_dir": wind_dirs[0] if wind_dirs else "",
                    "wind_power": wind_text,
                },
                "night": {
                    "condition": condition, "key": night_cond["key"],
                    "icon": night_cond["icon"],
                    "wind_dir": wind_dirs[-1] if wind_dirs else "",
                    "wind_power": wind_text,
                },
                "precipitation": None,
            })
        return out[:7]
