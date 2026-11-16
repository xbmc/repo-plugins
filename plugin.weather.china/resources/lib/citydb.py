# -*- coding: utf-8 -*-
"""
lib/citydb.py — 全国城市索引、中文搜索与切换、双数据源代码对齐。

索引来自两个公开来源，随插件内置（无需联网即可搜索）：
  cities_nmc.json        中央气象台 /rest/province + /rest/province/{code}
                         -> 2529 个站点，字段 code/city/province/province_code
  cities_weathercn.json  中国天气网 /textFC/{prov}.shtml
                         -> 3230 个 9 位城市码，字段 code/city/province

搜索规则：
  1. 归一化：去掉「省/市/区/县/自治区/特别行政区…」后缀再比对；
  2. 评分：精确 > 前缀 > 包含 > 所在省包含；同分按名称短者优先；
  3. 支持中文子串（如输入「朝阳」可找到北京朝阳区、辽宁朝阳市）；
  4. 额外支持常见城市拼音首字母（bj / sh / gz …）作为便捷入口；
  5. 结果按 (省, 市, 站点码) 去重，默认最多 50 条。

切换城市后写入 settings：city_name / nmc_code / wcn_code。
"""
from __future__ import unicode_literals

import json
import os
import re

from . import config, net

_RESOURCES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILTIN_DATA = os.path.join(_RESOURCES, "data")
USER_INDEX = os.path.join(config.PROFILE_PATH, "cities_nmc.json")

# 热门城市（中文名），用于「切换城市」首页快捷入口
POPULAR = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安",
    "重庆", "天津", "沈阳", "哈尔滨", "太原", "济南", "郑州", "长沙",
    "昆明", "兰州", "青岛", "石家庄", "合肥", "福州", "厦门",
]

# 常用城市 9 位码兜底表（当索引匹配失败时使用）
FALLBACK_WCODE = {
    "北京": "101010100", "上海": "101020100", "天津": "101030100",
    "重庆": "101040100", "广州": "101280101", "深圳": "101280601",
    "杭州": "101210101", "南京": "101190101", "成都": "101270101",
    "武汉": "101200101", "西安": "101110101", "青岛": "101120201",
    "太原": "101100101", "济南": "101120101", "郑州": "101180101",
    "长沙": "101250101", "沈阳": "101070101", "哈尔滨": "101050101",
    "昆明": "101290101", "兰州": "101160101", "石家庄": "101090101",
}

# 拼音首字母便捷搜索（只覆盖高频城市；主搜索仍是中文）
PINYIN = {
    "bj": "北京", "sh": "上海", "gz": "广州", "sz": "深圳", "hz": "杭州",
    "nj": "南京", "cd": "成都", "wh": "武汉", "xa": "西安", "cq": "重庆",
    "tj": "天津", "sy": "沈阳", "heb": "哈尔滨", "ty": "太原", "jn": "济南",
    "zz": "郑州", "cs": "长沙", "km": "昆明", "lz": "兰州", "qd": "青岛",
    "sjz": "石家庄", "hf": "合肥", "fz": "福州", "xm": "厦门",
}

_PROV_SUFFIX = ["维吾尔自治区", "壮族自治区", "回族自治区", "自治区",
                "特别行政区", "省", "市"]
_CITY_SUFFIX = ["特别行政区", "自治州", "自治县", "自治区", "地区", "盟",
                "市", "县", "区", "旗"]


def norm_city(name):
    value = str(name or "").strip()
    for suffix in _CITY_SUFFIX:
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[:-len(suffix)]
    return value


def norm_prov(name):
    value = str(name or "").strip()
    for suffix in _PROV_SUFFIX:
        if value.endswith(suffix) and len(value) > len(suffix):
            return value[:-len(suffix)]
    return value


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fp:
            obj = json.load(fp)
        if isinstance(obj, dict):
            return obj.get("items", [])
        return obj if isinstance(obj, list) else []
    except Exception:  # noqa: BLE001
        return []


class CityDB(object):
    def __init__(self, fetcher=None, debug=None):
        self.fetcher = fetcher or net.Fetcher(
            config.CACHE_PATH, timeout=config.get_int("timeout", 10, 1, 60),
            ttl=3600, debug=debug)
        self._debug = debug or (lambda msg: None)
        self.nmc_items = []
        self.wcn_items = []
        self._wcn_map = {}
        self.load()

    # ------------------------------------------------------------ 加载
    def load(self):
        # 用户在线更新过的索引优先，失败回退内置索引
        self.nmc_items = _read_json(USER_INDEX) or _read_json(
            os.path.join(BUILTIN_DATA, "cities_nmc.json"))
        self.wcn_items = _read_json(os.path.join(BUILTIN_DATA, "cities_weathercn.json"))
        self._wcn_map = {}
        for row in self.wcn_items:
            key = (norm_prov(row.get("province")), norm_city(row.get("city")))
            self._wcn_map.setdefault(key, row.get("code", ""))
        self._debug("city index: nmc=%d wcn=%d" %
                    (len(self.nmc_items), len(self.wcn_items)))
        return len(self.nmc_items)

    def wcode_for(self, province, city):
        key = (norm_prov(province), norm_city(city))
        return self._wcn_map.get(key) or FALLBACK_WCODE.get(norm_city(city), "")

    # ------------------------------------------------------------ 搜索
    def _score(self, row, keyword):
        name = norm_city(row.get("city", ""))
        prov = norm_prov(row.get("province", ""))
        raw = row.get("city", "")
        if not keyword:
            return 99
        if name == keyword or raw == keyword:
            return 0
        if name.startswith(keyword) or raw.startswith(keyword):
            return 1
        if keyword in name or keyword in raw:
            return 2
        if keyword in prov:
            return 3
        return None

    def search(self, query, limit=50):
        query = str(query or "").strip()
        if not query:
            return []
        # 纯 ASCII 视为拼音首字母
        if re.match(r"^[a-zA-Z]+$", query):
            query = PINYIN.get(query.lower(), query.lower())

        scored = []
        for row in self.nmc_items:
            score = self._score(row, query)
            if score is None:
                continue
            scored.append((score, len(row.get("city", "")),
                           row.get("province", ""), row))
        scored.sort(key=lambda x: (x[0], x[1], x[2]))

        seen = set()
        results = []
        for _score_v, _len, _prov, row in scored:
            city = row.get("city", "")
            province = row.get("province", "")
            code = row.get("code", "")
            key = (province, city, code)
            if key in seen or not code:
                continue
            seen.add(key)
            results.append({
                "name": city,
                "province": province,
                "nmc_code": code,
                "wcn_code": self.wcode_for(province, city),
                "display": ("%s · %s" % (city, province)) if province else city,
            })
            if len(results) >= limit:
                break
        return results

    def popular(self):
        out = []
        for name in POPULAR:
            hits = self.search(name, limit=1)
            if hits and norm_city(hits[0]["name"]) == norm_city(name):
                out.append(hits[0])
        return out

    def select(self, item):
        """切换当前城市，写入 Kodi 设置。"""
        config.put("city_name", item["name"])
        config.put("nmc_code", item["nmc_code"])
        config.put("wcn_code", item.get("wcn_code", ""))
        return config.current_location()

    # ------------------------------------------------------------ 在线刷新
    def refresh_online(self, force=True):
        """重新抓取 nmc.cn 全部站点，写入用户配置目录；返回站点数，0 表示失败。"""
        payload, meta = self.fetcher.get_json(
            config.NMC_PROVINCES, referer=config.NMC_REFERER,
            ttl=3600, force=force)
        if not isinstance(payload, list) or not payload:
            self._debug("refresh provinces failed: %s" % meta.error)
            return 0
        rows = []
        for prov in payload:
            code = prov.get("code") if isinstance(prov, dict) else None
            if not code:
                continue
            stations, sub = self.fetcher.get_json(
                config.NMC_STATIONS.format(code=code),
                referer=config.NMC_REFERER, ttl=3600, force=force)
            if not isinstance(stations, list):
                self._debug("refresh stations %s failed: %s" % (code, sub.error))
                continue
            for st in stations:
                if isinstance(st, dict) and st.get("code"):
                    rows.append({
                        "code": st["code"],
                        "city": st.get("city", ""),
                        "province": st.get("province", prov.get("name", "")),
                        "province_code": code,
                    })
        if not rows:
            return 0
        try:
            with open(USER_INDEX, "w", encoding="utf-8", newline="\n") as fp:
                json.dump({"count": len(rows), "items": rows}, fp,
                          ensure_ascii=False, separators=(",", ":"))
        except Exception as exc:  # noqa: BLE001
            self._debug("write user index failed: %s" % exc)
            return 0
        self.load()
        return len(self.nmc_items)
