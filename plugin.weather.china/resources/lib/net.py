# -*- coding: utf-8 -*-
"""
lib/net.py — HTTP 抓取、UTF-8 解码、文件缓存与降级。

处理规则（与 docs/DATA_SOURCE.md 一致）：
1. 所有响应按 UTF-8 解码（errors="replace"），缓存文件亦为 UTF-8 / 无 BOM。
2. 请求携带 UA / Referer / Accept-Language；默认 2 次重试 + 线性退避。
3. 缓存按 URL 的 sha1 分文件，TTL 内直接命中。
4. 网络失败时允许返回「过期缓存」并置 stale=True（stale-while-error），
   保证断网也不会让插件崩溃；过期上限 24 小时。
5. 任何异常都被吞掉并转成 (None, meta)，由上层决定降级到备用数据源。
"""
from __future__ import unicode_literals

import hashlib
import json
import os
import time
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

STALE_MAX_AGE = 24 * 3600


class FetchResult(object):
    """一次抓取的结果。text 为 None 表示彻底失败。"""

    __slots__ = ("text", "cached", "stale", "error", "age")

    def __init__(self, text=None, cached=False, stale=False, error=None, age=0):
        self.text = text
        self.cached = cached
        self.stale = stale
        self.error = error
        self.age = age

    @property
    def ok(self):
        return self.text is not None

    def __repr__(self):
        return "<FetchResult ok=%s cached=%s stale=%s error=%r>" % (
            self.ok, self.cached, self.stale, self.error)


class Fetcher(object):
    def __init__(self, cache_dir, timeout=10, ttl=600, retries=2, debug=None):
        self.cache_dir = cache_dir
        self.timeout = max(1, int(timeout))
        self.ttl = max(0, int(ttl))
        self.retries = max(0, int(retries))
        self._debug = debug or (lambda msg: None)
        try:
            if cache_dir and not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------ 缓存
    def _cache_file(self, url):
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, key + ".json")

    def _read_cache(self, url):
        path = self._cache_file(url)
        try:
            with open(path, "r", encoding="utf-8") as fp:
                obj = json.load(fp)
            return obj.get("text"), float(obj.get("ts", 0))
        except Exception:  # noqa: BLE001
            return None, 0.0

    def _write_cache(self, url, text):
        path = self._cache_file(url)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as fp:
                json.dump({"url": url, "ts": time.time(), "text": text},
                          fp, ensure_ascii=False)
            if os.path.exists(path):
                os.remove(path)
            os.rename(tmp, path)
        except Exception as exc:  # noqa: BLE001
            self._debug("cache write failed: %s" % exc)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------ 请求
    def _request(self, url, referer):
        headers = {
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Charset": "UTF-8,*;q=0.5",
        }
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read()
        # 目标接口/页面均为 UTF-8；个别页面声明 gb2312 但实体已是 UTF-8
        return raw.decode("utf-8", "replace")

    def get(self, url, referer=None, ttl=None, force=False):
        """返回 FetchResult。ttl 为 None 时使用实例默认值。"""
        ttl = self.ttl if ttl is None else max(0, int(ttl))
        cached_text, ts = self._read_cache(url)
        age = time.time() - ts if ts else 0.0

        if cached_text is not None and not force and ts and age <= ttl:
            self._debug("cache HIT %s (age=%ds)" % (url, int(age)))
            return FetchResult(cached_text, cached=True, stale=False, age=age)

        last_error = None
        for attempt in range(self.retries + 1):
            try:
                self._debug("HTTP %s (attempt %d)" % (url, attempt + 1))
                text = self._request(url, referer)
                if not text:
                    raise ValueError("empty response")
                self._write_cache(url, text)
                return FetchResult(text, cached=False, stale=False)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self._debug("HTTP fail %s -> %s" % (url, exc))
                if attempt < self.retries:
                    time.sleep(0.5 * (attempt + 1))

        # 降级：返回过期缓存（最多 24 小时）
        if cached_text is not None and 0 < age <= STALE_MAX_AGE:
            self._debug("stale fallback %s (age=%ds)" % (url, int(age)))
            return FetchResult(cached_text, cached=True, stale=True,
                               error=str(last_error), age=age)
        return FetchResult(None, cached=False, stale=False,
                           error=str(last_error) if last_error else "unknown error")

    def get_json(self, url, referer=None, ttl=None, force=False):
        result = self.get(url, referer=referer, ttl=ttl, force=force)
        if not result.ok:
            return None, result
        try:
            return json.loads(result.text), result
        except Exception as exc:  # noqa: BLE001
            result.error = "JSON decode: %s" % exc
            result.text = None
            return None, result

    def clear(self):
        """清空缓存（插件菜单「刷新」时调用）。"""
        try:
            for name in os.listdir(self.cache_dir):
                if name.endswith(".json") or name.endswith(".tmp"):
                    os.remove(os.path.join(self.cache_dir, name))
            return True
        except Exception:  # noqa: BLE001
            return False
