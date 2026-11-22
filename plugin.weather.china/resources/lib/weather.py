# -*- coding: utf-8 -*-
"""
lib/weather.py — 多源聚合与「输出/处理规则」的执行层。

职责：
  * 按设置决定主源（中央气象台 / 中国天气网 / 自动）；
  * 失败自动降级到另一数据源；两源都成功时按字段补缺合并（mixed）；
  * 7 天预报不足时从中国天气网 HTML 页补足；
  * 预警合并、去重、等级过滤、排序、条数限制；
  * 统一裁剪预报天数、标注缓存/离线状态，永远返回结构完整的 dict。

上层（ui.py / windowprops.py / service.py）只消费这里的标准结构，
不再关心任何一家接口的原始字段。
"""
from __future__ import unicode_literals

import time

from . import alerts, config, net, nmc, weathercn
from .citydb import CityDB


def _fill(target, source):
    """把 source 中非空的字段补进 target 的 None/空字段（递归一层）。"""
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        if key not in target:
            target[key] = value
            continue
        old = target[key]
        if isinstance(old, dict) and isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if old.get(sub_key) in (None, ""):
                    old[sub_key] = sub_value
        elif old in (None, "") and value not in (None, ""):
            target[key] = value


def merge(base, extra):
    """把备用源的数据补进主源骨架。"""
    if not extra:
        return base
    _fill(base["current"], extra["current"])
    # condition 为 unknown 时优先用另一源的明确天气现象
    if base["current"].get("condition_key") == "unknown" and \
       extra["current"].get("condition_key") not in (None, "unknown"):
        for key in ("condition", "condition_key", "condition_icon"):
            base["current"][key] = extra["current"].get(key)

    by_date = {}
    for item in base["forecast"]:
        if item.get("date"):
            by_date.setdefault(item["date"], item)
    for item in extra["forecast"]:
        date = item.get("date")
        if not date:
            continue
        if date in by_date:
            _fill(by_date[date], item)
        else:
            base["forecast"].append(item)
    base["forecast"].sort(key=lambda x: x.get("date", ""))

    base["alerts"].extend(extra.get("alerts", []))
    if not base["indices"]:
        base["indices"] = list(extra.get("indices", []))
    if not base["updated"]:
        base["updated"] = extra.get("updated", "")
    base["cached"] = bool(base["cached"] or extra.get("cached"))
    base["stale"] = bool(base["stale"] or extra.get("stale"))
    base["source_list"] = list(dict.fromkeys(
        list(base.get("source_list", [])) + list(extra.get("source_list", []))))
    return base


class WeatherService(object):
    def __init__(self, debug=None):
        self._debug = debug or config.debug
        self.fetcher = net.Fetcher(
            config.CACHE_PATH,
            timeout=config.get_int("timeout", 10, 1, 60),
            ttl=config.get_int("cache_ttl", 10, 1, 1440) * 60,
            retries=2, debug=self._debug)
        self.nmc = nmc.NMCSource(self.fetcher, self._debug)
        self.wcn = weathercn.WCNSource(self.fetcher, self._debug)

    # ------------------------------------------------------------ 主流程
    def fetch_all(self, force=False, location=None):
        # 天气服务（xbmc.python.weather）可为不同地点传入自己的城市三元组；
        # 插件菜单 / 后台服务不传，沿用主设置里的当前城市。
        location = location or config.current_location()
        primary = config.get("primary_source", "auto")
        use_wcn = config.get_bool("enable_wcn", True)
        days = config.get_int("forecast_days", 7, 3, 7)
        result = nmc.blank(location)
        errors = []

        nmc_data = None
        wcn_data = None

        if primary in ("auto", "nmc"):
            nmc_data, meta = self.nmc.weather(location["nmc_code"], location, force)
            if nmc_data is None:
                errors.append("NMC: %s" % (meta.error if meta else "no data"))

        want_wcn = (primary == "wcn" or
                    (use_wcn and location["wcn_code"]) or
                    (primary == "auto" and nmc_data is None))
        if want_wcn and location["wcn_code"]:
            wcn_data, meta = self.wcn.index(location["wcn_code"], location, force)
            if wcn_data is None:
                errors.append("WCN: %s" % (meta.error if meta else "no data"))

        # 降级：主源失败时强制启用另一源（不受 enable_wcn 限制）
        if nmc_data is None and primary in ("auto", "nmc") and location["wcn_code"]:
            if wcn_data is None:
                wcn_data, _ = self.wcn.index(location["wcn_code"], location, force)
        if wcn_data is None and primary == "wcn" and location["nmc_code"]:
            nmc_data, _ = self.nmc.weather(location["nmc_code"], location, force)

        if primary == "wcn":
            base, extra = (wcn_data or nmc_data), (nmc_data if wcn_data else None)
        else:
            base, extra = (nmc_data or wcn_data), (wcn_data if nmc_data else None)

        if base is None:
            result["errors"] = errors
            result["notes"].append("all-sources-failed")
            self._debug("all sources failed: %s" % errors)
            return result

        result = base
        if extra is not None:
            merge(result, extra)
        result["ok"] = True
        result["source"] = ("mixed" if len(result["source_list"]) > 1
                            else (result["source_list"] or ["unknown"])[0])
        result["errors"] = errors
        result["fetched_at"] = int(time.time())

        # 预报天数不足时，用中国天气网 7 天页面补足
        if len(result["forecast"]) < days and location["wcn_code"]:
            seven, meta = self.wcn.seven_day(location["wcn_code"], force)
            if seven:
                merge(result, {"current": {}, "forecast": seven, "alerts": [],
                               "indices": [], "source_list": ["wcn"],
                               "updated": "", "cached": False, "stale": False})

        if config.get_bool("enable_alerts", True):
            self._attach_alerts(result, location, force)

        result["forecast"] = result["forecast"][:days]
        if result["stale"]:
            result["notes"].append("stale")
        elif result["cached"]:
            result["notes"].append("cached")
        return result

    # ------------------------------------------------------------ 预警
    def _attach_alerts(self, result, location, force=False):
        # 中国天气网 dingzhi 接口的预警更及时，作为本地预警补充
        if location["wcn_code"] and config.get_bool("enable_wcn", True):
            extra, meta = self.wcn.dingzhi(location["wcn_code"], location, force)
            result["alerts"].extend(extra or [])

        scope = config.get("alert_scope", "all")
        if scope in ("national", "all"):
            national, meta = self.nmc.national_alerts(
                limit=config.get_int("national_limit", 30, 5, 100), force=force)
            province = _region_key(location["name"], result["location"])
            city = location["name"].replace("市", "").replace("区", "")
            related = [a for a in (national or [])
                       if (province and province in a["title"]) or
                       (city and city in a["title"])]
            result["alerts"].extend(related)
            result["national_count"] = len(national or [])

        min_rank = config.get_int("alert_min_level", 0, 0, 3)
        result["alerts"] = alerts.prepare(
            result["alerts"], min_rank=min_rank,
            limit=config.get_int("national_limit", 30, 5, 100) * 2)

    def national_alerts(self, force=False):
        """独立的「全国预警」视图数据源。"""
        limit = config.get_int("national_limit", 30, 5, 100)
        raw, meta = self.nmc.national_alerts(limit=limit, force=force)
        min_rank = config.get_int("alert_min_level", 0, 0, 3)
        return alerts.prepare(raw or [], min_rank=min_rank, limit=limit), meta

    # ------------------------------------------------------------ 辅助
    def clear_cache(self):
        return self.fetcher.clear()

    def refresh_cities(self, force=True):
        return CityDB(fetcher=self.fetcher, debug=self._debug).refresh_online(force)


def _region_key(city_name, location):
    """从城市/省份名中取一个可用于在全国预警标题里匹配的关键词。"""
    name = str(city_name or "").strip()
    for suffix in ("特别行政区", "自治区", "自治州", "省", "市", "区", "县"):
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[:-len(suffix)]
            break
    return name[:2] if len(name) > 2 else name
