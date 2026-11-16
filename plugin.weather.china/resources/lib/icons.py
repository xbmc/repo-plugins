# -*- coding: utf-8 -*-
"""
lib/icons.py — 天气现象代码 / 中文描述 → 统一 condition key 与本地图标。

两套数据源用的是同一套「中国天气网天气现象代码」(0~53)：
  nmc.cn  predict.detail[].day.weather.img = "7"  (小雨)
  weather.com.cn  fc.f[].fa = "02" / weathercode = "d02"  (阴)
因此统一在 conditions.json 中映射。代码无法识别时，退回中文关键词匹配；
再失败则用 unknown.png，绝不抛异常。

模块零 Kodi 依赖，路径由 __file__ 推导，可在 PC 上离线自测。
"""
from __future__ import unicode_literals

import json
import os
import re

_RESOURCES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(_RESOURCES, "data")
MEDIA_PATH = os.path.join(_RESOURCES, "media")

_TABLE = None
_CODE_RE = re.compile(r"(\d{1,2})")


def _table():
    global _TABLE
    if _TABLE is None:
        try:
            with open(os.path.join(DATA_PATH, "conditions.json"), "r",
                      encoding="utf-8") as fp:
                _TABLE = json.load(fp)
        except Exception:  # noqa: BLE001
            _TABLE = {"codes": {}, "keywords": [],
                      "fallback": {"zh": "未知", "en": "Unknown", "key": "unknown"}}
    return _TABLE


def _pack(entry):
    return {
        "zh": entry.get("zh", "未知"),
        "en": entry.get("en", "Unknown"),
        "key": entry.get("key", "unknown"),
        "icon": icon_path(entry.get("key", "unknown")),
    }


def icon_path(key):
    """返回 resources/media 下的图标绝对路径，缺失时回退 unknown.png。"""
    path = os.path.join(MEDIA_PATH, "%s.png" % key)
    if not os.path.isfile(path):
        path = os.path.join(MEDIA_PATH, "unknown.png")
    return path


def alert_icon(level_key):
    """预警等级色块图标。"""
    name = "alert_%s.png" % (level_key or "unknown")
    path = os.path.join(MEDIA_PATH, name)
    if not os.path.isfile(path):
        path = os.path.join(MEDIA_PATH, "alert_unknown.png")
    return path


def from_code(code):
    """'d02' / '02' / 2 / 'n07' → 统一 dict；无效返回 None。"""
    if code is None:
        return None
    text = str(code).strip()
    if text in ("", "-", "9999", "None", "null"):
        return None
    match = _CODE_RE.search(text)
    if not match:
        return None
    entry = _table().get("codes", {}).get(str(int(match.group(1))))
    if not entry:
        return None
    return _pack(entry)


def from_text(text):
    """中文描述 → condition；取描述里出现最早的关键词（同位取更长者）。"""
    if not text:
        return None
    text = str(text).strip()
    best = None  # (position, -length, entry)
    for kw in _table().get("keywords", []):
        word = kw.get("zh", "")
        if not word:
            continue
        pos = text.find(word)
        if pos < 0:
            continue
        candidate = (pos, -len(word), kw)
        if best is None or candidate < best:
            best = candidate
    if best is None:
        return None
    return _pack(best[2])


def resolve(code=None, text=None):
    """优先用代码，其次中文描述，最后 fallback。"""
    return from_code(code) or from_text(text) or _pack(_table()["fallback"])


def split_text(text):
    """'阴转多云' → ['阴', '多云']，便于白天/夜间分别取图标。"""
    if not text:
        return []
    return [p for p in re.split(r"[转/到至,，、\s]+", str(text)) if p]
