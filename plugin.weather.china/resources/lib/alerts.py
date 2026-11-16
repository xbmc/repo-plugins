# -*- coding: utf-8 -*-
"""
lib/alerts.py — 中国气象预警归一化：类型、等级、颜色、去重、排序、过滤。

预警等级遵循《气象灾害预警信号发布与传播办法》四级制：
    蓝色(Ⅳ/一般) < 黄色(Ⅲ/较重) < 橙色(Ⅱ/严重) < 红色(Ⅰ/特别严重)
颜色为中国通行的标准色，Kodi 里用 ARGB 供 ListItem 标签着色 / 图标生成。

解析原则：**以中文文本为准，编码仅作辅助**。
  nmc.cn findAlarm 的标题形如「山西省气象台发布大雾黄色预警」；
  weather.com.cn alarmDZ 的 w5=类型名、w7=等级名、w6=等级码(01蓝/02黄/03橙/04红)。
  接口编码在不同版本间可能变动，文本解析最稳定。
"""
from __future__ import unicode_literals

import hashlib
import re
from urllib.parse import urljoin

from . import icons

NMC_BASE = "http://www.nmc.cn"

LEVELS = [
    {"key": "blue", "zh": "蓝色", "code": "01", "rank": 0,
     "color": "FF2E7CF6", "en": "Blue", "label_id": 32145},
    {"key": "yellow", "zh": "黄色", "code": "02", "rank": 1,
     "color": "FFF5C518", "en": "Yellow", "label_id": 32146},
    {"key": "orange", "zh": "橙色", "code": "03", "rank": 2,
     "color": "FFEE8A17", "en": "Orange", "label_id": 32147},
    {"key": "red", "zh": "红色", "code": "04", "rank": 3,
     "color": "FFD93025", "en": "Red", "label_id": 32148},
    {"key": "unknown", "zh": "未知等级", "code": "00", "rank": -1,
     "color": "FF9AA0A6", "en": "Unknown", "label_id": 32149},
]
LEVEL_BY_CHAR = {lv["zh"][0]: lv for lv in LEVELS[:4]}
LEVEL_BY_CODE = {lv["code"]: lv for lv in LEVELS[:4]}
LEVEL_BY_NAME = {lv["zh"]: lv for lv in LEVELS[:4]}
_UNKNOWN = LEVELS[-1]

# 常见预警类型（文本兜底用）
KNOWN_TYPES = [
    "道路结冰", "森林火险", "地质灾害", "山洪", "城市内涝", "雷雨大风",
    "强对流", "雷电", "冰雹", "沙尘暴", "特大暴雨", "大暴雨", "暴雨",
    "暴雪", "寒潮", "大风", "高温", "干旱", "低温", "霜冻", "大雾",
    "浓雾", "霾", "台风", "海上大风", "低温雨雪冰冻", "森林草原火险",
]

_LEVEL_RE = re.compile(r"(蓝|黄|橙|红)\s*色?\s*预警")
_PUBLISH_RE = re.compile(r"(?P<issuer>.+?)(?:继续)?发布(?P<body>.*)")


def _level_from_text(text):
    if not text:
        return None
    match = _LEVEL_RE.search(str(text))
    if match:
        return LEVEL_BY_CHAR.get(match.group(1))
    for name, lv in LEVEL_BY_NAME.items():
        if name in str(text):
            return lv
    return None


def _level_from_code(code):
    if code is None:
        return None
    value = str(code).strip().zfill(2)
    return LEVEL_BY_CODE.get(value)


def _type_from_text(text, fallback=""):
    """从 'XX气象台发布寒潮蓝色预警信号' 中取 '寒潮'。"""
    if not text:
        return fallback
    text = str(text)
    match = _PUBLISH_RE.search(text)
    body = match.group("body") if match else text
    level_match = _LEVEL_RE.search(body)
    if level_match:
        body = body[:level_match.start()]
    body = body.strip().rstrip("信号").strip("，,。;； ")
    # 去掉可能粘连的行政前缀，只保留灾害类型
    for known in KNOWN_TYPES:
        if known in body:
            return known
    return body[:12] if body else fallback


def _issuer_from_text(title):
    match = _PUBLISH_RE.search(str(title or ""))
    if not match:
        return ""
    return match.group("issuer").strip()


def _make(**kwargs):
    """构造统一的预警对象。"""
    level = kwargs.get("level") or _UNKNOWN
    alert_type = kwargs.get("alert_type") or "预警"
    title = kwargs.get("title") or ""
    issuer = kwargs.get("issuer") or _issuer_from_text(title)
    content = kwargs.get("content") or ""
    issue_time = (kwargs.get("issue_time") or "").replace("/", "-").strip()
    ident = kwargs.get("id") or hashlib.sha1(
        (title + issue_time + content[:60]).encode("utf-8")).hexdigest()[:16]
    return {
        "id": ident,
        "title": title or "%s%s预警" % (issuer, alert_type),
        "issuer": issuer,
        "type": alert_type,
        "type_code": kwargs.get("type_code") or "",
        "level": level["zh"],
        "level_key": level["key"],
        "level_rank": level["rank"],
        "level_code": level["code"],
        "level_color": level["color"],
        "level_label_id": level["label_id"],
        "level_en": level["en"],
        "issue_time": issue_time,
        "content": content,
        "source": kwargs.get("source", "nmc"),
        "url": kwargs.get("url", ""),
        "icon": icons.alert_icon(level["key"]),
    }


def from_nmc_list(item):
    """nmc.cn /rest/findAlarm → page.list[] 条目。"""
    if not isinstance(item, dict):
        return None
    title = item.get("title", "")
    if not title:
        return None
    level = _level_from_text(title)
    alert_type = _type_from_text(title)
    url = item.get("url") or ""
    if url and not url.startswith("http"):
        url = urljoin(NMC_BASE, url)
    return _make(
        id=item.get("alertid"),
        title=title,
        issuer=_issuer_from_text(title),
        alert_type=alert_type,
        level=level,
        issue_time=item.get("issuetime", ""),
        source="nmc",
        url=url,
        content="",
    )


def from_nmc_warn(warn, city=""):
    """nmc.cn /rest/weather → data.real.warn；'9999' 表示无预警。"""
    if not isinstance(warn, dict):
        return None
    if str(warn.get("alert", "9999")) == "9999" and \
       str(warn.get("issuecontent", "9999")) == "9999":
        return None
    content = "" if warn.get("issuecontent") in (None, "9999") else str(warn["issuecontent"])
    sig_type = "" if warn.get("signaltype") in (None, "9999") else str(warn["signaltype"])
    sig_level = "" if warn.get("signallevel") in (None, "9999") else str(warn["signallevel"])
    title = warn.get("title") or ""
    if not title:
        title = "%s发布%s%s预警" % (city or warn.get("city", ""), sig_type,
                                  sig_level if sig_level.endswith("色") else sig_level + "色")
    level = _level_from_text(title) or _level_from_text(sig_level) or _level_from_code(sig_level)
    alert_type = _type_from_text(title, sig_type) or sig_type
    if alert_type in ("", "9999"):
        alert_type = _find_type(content)
    url = warn.get("url") or ""
    if url and not str(url).startswith("http") and url != "9999":
        url = urljoin(NMC_BASE, url)
    return _make(
        title=title,
        issuer=_issuer_from_text(title) or (warn.get("province", "")
                                            if warn.get("province") != "9999" else ""),
        alert_type=alert_type,
        level=level,
        issue_time=warn.get("issuetime", ""),
        content=content,
        source="nmc-local",
        url=url if url != "9999" else "",
    )


def from_wcn(item, city=""):
    """weather.com.cn alarmDZ{code}.w[] 条目。

    w1 发布单位 / w4 类型码 / w5 类型名 / w6 等级码 / w7 等级名
    w8 发布时间 / w9 预警全文 / w10 唯一标识 / w11 业务编号
    """
    if not isinstance(item, dict):
        return None
    level = (_level_from_text(item.get("w7")) or
             _level_from_code(item.get("w6")) or
             _level_from_text(item.get("w9")))
    alert_type = (item.get("w5") or "").strip() or _find_type(item.get("w9", ""))
    issuer = (item.get("w1") or "").strip() or city
    lv_name = level["zh"] if level else "预警"
    title = "%s发布%s%s预警" % (issuer, alert_type, lv_name)
    return _make(
        id=item.get("w10") or item.get("w11"),
        title=title,
        issuer=issuer,
        alert_type=alert_type or "预警",
        type_code=(item.get("w4") or "").strip(),
        level=level,
        issue_time=item.get("w8", ""),
        content=item.get("w9", ""),
        source="wcn",
        url="http://www.weather.com.cn/alarm/",
    )


def _find_type(text):
    for known in KNOWN_TYPES:
        if known in str(text or ""):
            return known
    return ""


def dedupe(alerts):
    """按 发布单位+类型+等级+时间 去重；同时去掉内容完全相同的重复项。"""
    seen = set()
    out = []
    for alert in alerts:
        if not alert:
            continue
        key = (alert["issuer"], alert["type"], alert["level"],
               alert["issue_time"], alert["content"][:40])
        if key in seen:
            continue
        seen.add(key)
        out.append(alert)
    return out


def sort_alerts(alerts):
    """红色 > 橙色 > 黄色 > 蓝色 > 未知；同级按发布时间倒序。"""
    return sorted(alerts, key=lambda a: (a.get("level_rank", -1),
                                         a.get("issue_time", "")), reverse=True)


def filter_by_level(alerts, min_rank=0):
    """min_rank: 0=全部 1=黄色及以上 2=橙色及以上 3=仅红色。"""
    if min_rank <= 0:
        return list(alerts)
    return [a for a in alerts if a.get("level_rank", -1) >= min_rank]


def prepare(alerts, min_rank=0, limit=30):
    return sort_alerts(filter_by_level(dedupe(alerts), min_rank))[:max(0, limit)]
