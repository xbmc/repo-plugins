# -*- coding: utf-8 -*-
"""Scraper and archive processor for Funhaus Archive (funhausarchive.com)."""

import html
import json
import logging
import random
import re
import urllib.parse
import urllib.request
from typing import List, Dict, Optional, Any

logger = logging.getLogger("plugin.video.funhausarchive.scraper")

BASE_URL = "https://funhausarchive.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Kodi/20.0"


class FunhausScraper:
    """Scrapes series and video listings from funhausarchive.com."""

    def __init__(self, cache=None):
        self.cache = cache

    def _fetch_url(self, url: str) -> str:
        """Fetches the given URL and returns the decoded string content."""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        return content

    @staticmethod
    def _js_template_unescape(s: str) -> str:
        """Unescapes JavaScript template literal escape sequences for JSON decoding."""
        def repl(m):
            esc = m.group(1)
            if esc == "\\": return "\\"
            elif esc == "`": return "`"
            elif esc == "$": return "$"
            elif esc == "n": return "\n"
            elif esc == "r": return "\r"
            elif esc == "t": return "\t"
            elif esc == "b": return "\b"
            elif esc == "f": return "\f"
            elif esc == "v": return "\v"
            elif esc == "0": return "\0"
            elif esc == '"': return '"'
            elif esc == "'": return "'"
            elif esc.startswith("u"): return chr(int(esc[1:], 16))
            elif esc.startswith("x"): return chr(int(esc[1:], 16))
            return m.group(0)
        return re.sub(r"\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)", repl, s)

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        Retrieves all 4,899+ videos from the funhausarchive data bundle.
        Results are cached locally using SimpleCache for instant subsequent loads.
        """
        cache_key = "all_videos_archive"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached and isinstance(cached, list) and len(cached) > 0:
                return cached

        logger.info("Fetching all videos archive bundle from funhausarchive.com/videos/...")
        try:
            videos_page = self._fetch_url(f"{BASE_URL}/videos/")
            # Locate script tag loading videos script
            m1 = re.search(r'src="(/_astro/videos\.astro[^"]+\.js)"', videos_page)
            if not m1:
                # Fallback search for any astro script referencing videos
                m1 = re.search(r'src="(/_astro/[^"]*videos[^"]*\.js)"', videos_page)

            if not m1:
                logger.error("Could not locate videos bundle script in HTML")
                return []

            script_url = f"{BASE_URL}{m1.group(1)}"
            js_script = self._fetch_url(script_url)

            # Locate imported data chunk: import{v as X}from"./videos.XXXXXX.js"
            m2 = re.search(r'from["\']\./(videos\.[^"]+\.js)["\']', js_script)
            if not m2:
                logger.error("Could not locate videos data chunk import in script")
                return []

            data_chunk_url = f"{BASE_URL}/_astro/{m2.group(1)}"
            chunk_content = self._fetch_url(data_chunk_url)

            # Extract raw template literal: const e=JSON.parse(`...`);
            start = chunk_content.find("`") + 1
            end = chunk_content.rfind("`")
            if start <= 0 or end <= start:
                logger.error("Could not extract JSON template string from data chunk")
                return []

            raw_str = chunk_content[start:end]
            decoded_str = self._js_template_unescape(raw_str)
            raw_videos = json.loads(decoded_str)

            normalized = []
            for item in raw_videos:
                vid_id = item.get("id")
                if not vid_id:
                    continue

                raw_date = str(item.get("uploadDate") or "")
                formatted_date = ""
                if len(raw_date) == 8 and raw_date.isdigit():
                    formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

                normalized.append({
                    "id": vid_id,
                    "title": item.get("title", f"Video {vid_id}"),
                    "upload_date": formatted_date,
                    "raw_date": raw_date if raw_date.isdigit() else "00000000",
                    "duration": int(item.get("duration") or 0),
                    "view_count": int(item.get("viewCount") or 0),
                    "like_count": int(item.get("likeCount") or 0),
                    "cast_members": item.get("castMembers") or [],
                    "cast_member_names": item.get("castMemberNames") or [],
                    "content_type": item.get("contentType") or "",
                    "content_type_name": item.get("contentTypeName") or "",
                    "series": item.get("series") or [],
                    "series_names": item.get("seriesNames") or [],
                    "description": item.get("description") or "",
                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "backdrop": f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg",
                    "playable_url": f"https://www.youtube.com/watch?v={vid_id}"
                })

            if self.cache and normalized:
                self.cache.set(cache_key, normalized)

            return normalized

        except Exception as e:
            logger.error(f"Failed to fetch and parse all videos archive: {e}")
            return []

    def get_cast_members(self) -> List[Dict[str, Any]]:
        """
        Retrieves list of cast members with appearance counts, sorted by appearances.
        """
        videos = self.get_all_videos()
        cast_map = {}
        for v in videos:
            slugs = v.get("cast_members", [])
            names = v.get("cast_member_names", [])
            for slug, name in zip(slugs, names):
                if slug not in cast_map:
                    cast_map[slug] = {"slug": slug, "name": name, "video_count": 0}
                cast_map[slug]["video_count"] += 1

        cast_list = list(cast_map.values())
        cast_list.sort(key=lambda c: c["video_count"], reverse=True)
        return cast_list

    def get_years(self) -> List[Dict[str, Any]]:
        """
        Retrieves available release years with video counts, sorted chronologically (2015 to 2024).
        """
        videos = self.get_all_videos()
        years_map = {}
        for v in videos:
            raw_date = v.get("raw_date", "")
            if len(raw_date) >= 4 and raw_date[:4].isdigit() and raw_date[:4] != "0000":
                y = raw_date[:4]
                years_map[y] = years_map.get(y, 0) + 1

        years_list = [{"year": y, "video_count": count} for y, count in sorted(years_map.items())]
        return years_list

    def get_content_types(self) -> List[Dict[str, Any]]:
        """
        Retrieves available content types (Gameplay, Podcasts, etc.) with video counts.
        """
        videos = self.get_all_videos()
        types_map = {}
        for v in videos:
            slug = v.get("content_type")
            name = v.get("content_type_name") or slug
            if slug:
                if slug not in types_map:
                    types_map[slug] = {"slug": slug, "name": name, "video_count": 0}
                types_map[slug]["video_count"] += 1

        types_list = list(types_map.values())
        types_list.sort(key=lambda t: t["video_count"], reverse=True)
        return types_list

    def filter_and_sort_videos(
        self,
        videos: Optional[List[Dict[str, Any]]] = None,
        sort_by: str = "oldest",
        year: Optional[str] = None,
        cast: Optional[str] = None,
        content_type: Optional[str] = None,
        series: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters and sorts videos according to specified criteria.

        sort_by options (matching funhausarchive.com #sort-filter):
          - 'oldest': Chronological order (Oldest First, starting in 2015)
          - 'newest': Reverse chronological order (Newest First)
          - 'most-viewed': Most views first
          - 'most-liked': Most likes first
          - 'longest': Longest duration first
          - 'shortest': Shortest duration first
          - 'title-az': Title alphabetical (A-Z)
          - 'title-za': Title alphabetical (Z-A)
          - 'random': Shuffled order
        """
        if videos is None:
            videos = self.get_all_videos()

        results = videos

        # Filter: Year
        if year:
            results = [v for v in results if v.get("raw_date", "").startswith(year)]

        # Filter: Cast
        if cast:
            results = [v for v in results if cast in v.get("cast_members", [])]

        # Filter: Content Type
        if content_type:
            results = [v for v in results if v.get("content_type") == content_type]

        # Filter: Series
        if series:
            results = [v for v in results if series in v.get("series", [])]

        # Filter: Search query
        if query:
            q_lower = query.lower()
            results = [
                v for v in results
                if q_lower in v.get("title", "").lower()
                or q_lower in v.get("description", "").lower()
                or any(q_lower in name.lower() for name in v.get("cast_member_names", []))
            ]

        # Sorting
        if sort_by == "oldest":
            # Put items with valid dates in chronological order; items with '00000000' at the end
            results = sorted(
                results,
                key=lambda v: v.get("raw_date") if (v.get("raw_date") and v.get("raw_date") != "00000000") else "99999999"
            )
        elif sort_by == "newest":
            results = sorted(results, key=lambda v: v.get("raw_date") or "00000000", reverse=True)
        elif sort_by == "most-viewed":
            results = sorted(results, key=lambda v: v.get("view_count", 0), reverse=True)
        elif sort_by == "most-liked":
            results = sorted(results, key=lambda v: v.get("like_count", 0), reverse=True)
        elif sort_by == "longest":
            results = sorted(results, key=lambda v: v.get("duration", 0), reverse=True)
        elif sort_by == "shortest":
            results = sorted(results, key=lambda v: v.get("duration", 0))
        elif sort_by == "title-az":
            results = sorted(results, key=lambda v: v.get("title", "").lower())
        elif sort_by == "title-za":
            results = sorted(results, key=lambda v: v.get("title", "").lower(), reverse=True)
        elif sort_by == "random":
            results = list(results)
            random.shuffle(results)

        return results

    def get_series(self) -> List[Dict[str, Any]]:
        """
        Retrieves all available series from /series/.
        Returns a list of dicts:
        [
            {
                "slug": "gta-5",
                "title": "GTA 5",
                "video_count": "442 videos",
                "url": "https://funhausarchive.com/series/gta-5"
            },
            ...
        ]
        """
        cache_key = "series_list"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        url = f"{BASE_URL}/series/"
        html_content = self._fetch_url(url)

        pattern = re.compile(
            r'<a\s+href="/series/([^"/]+)/?"\s+class="series-card"[^>]*>.*?'
            r'<h2[^>]*>(.*?)</h2>.*?'
            r'<span class="video-count"[^>]*>(.*?)</span>',
            re.DOTALL | re.IGNORECASE
        )

        series_list = []
        for match in pattern.finditer(html_content):
            slug = match.group(1).strip()
            title = html.unescape(match.group(2).strip())
            count = html.unescape(match.group(3).strip())
            series_list.append({
                "slug": slug,
                "title": title,
                "video_count": count,
                "url": f"{BASE_URL}/series/{slug}"
            })

        if self.cache and series_list:
            self.cache.set(cache_key, series_list)

        return series_list

    def get_series_videos(self, series_slug: str) -> List[Dict[str, Any]]:
        """
        Retrieves videos in a specific series.
        Uses the embedded data-video attributes for clean metadata.
        Returns a list of dicts with video metadata.
        """
        cache_key = f"series_videos_{series_slug}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        url = f"{BASE_URL}/series/{series_slug}/"
        html_content = self._fetch_url(url)

        videos = self._parse_videos_from_html(html_content)

        # Fallback to all_videos archive filter if series page didn't yield items
        if not videos:
            videos = self.filter_and_sort_videos(sort_by="oldest", series=series_slug)

        if self.cache and videos:
            self.cache.set(cache_key, videos)

        return videos

    def get_video_detail(self, video_id: str) -> Dict[str, Any]:
        """
        Fetches extra details for a video from /video/<id>.
        Returns a dictionary with title, description, categories, tags, etc.
        """
        cache_key = f"video_detail_{video_id}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        url = f"{BASE_URL}/video/{video_id}"
        html_content = self._fetch_url(url)

        title_match = re.search(r'<title>(.*?)\s*-\s*Funhaus Archive</title>', html_content, re.IGNORECASE)
        title = html.unescape(title_match.group(1).strip()) if title_match else f"Video {video_id}"

        desc_match = re.search(r'##\s*Description\s*```(.*?)```', html_content, re.DOTALL | re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<div class="video-description"[^>]*>(.*?)</div>', html_content, re.DOTALL | re.IGNORECASE)
        description = html.unescape(desc_match.group(1).strip()) if desc_match else ""

        detail = {
            "id": video_id,
            "title": title,
            "description": description,
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "backdrop": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            "url": url,
        }

        if self.cache:
            self.cache.set(cache_key, detail)

        return detail

    def _parse_videos_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extracts video metadata from data-video attributes or video cards."""
        videos = []

        matches = re.findall(r'data-video="([^"]+)"', html_content)
        for raw_json in matches:
            try:
                unescaped = html.unescape(raw_json)
                data = json.loads(unescaped)
                video_id = data.get("id")
                if not video_id:
                    continue

                raw_date = str(data.get("uploadDate", ""))
                formatted_date = ""
                if len(raw_date) == 8 and raw_date.isdigit():
                    formatted_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

                videos.append({
                    "id": video_id,
                    "title": data.get("title", f"Video {video_id}"),
                    "duration": int(data.get("duration", 0)),
                    "upload_date": formatted_date,
                    "raw_date": raw_date if raw_date.isdigit() else "00000000",
                    "view_count": int(data.get("viewCount", 0)),
                    "like_count": int(data.get("likeCount", 0)),
                    "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    "backdrop": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
                    "playable_url": f"https://www.youtube.com/watch?v={video_id}"
                })
            except (json.JSONDecodeError, ValueError):
                continue

        return videos
