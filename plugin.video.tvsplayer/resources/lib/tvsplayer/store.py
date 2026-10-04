# -*- coding: utf-8 -*-
"""Local storage (JSON files in the add-on's profile folder). No Kodi dependencies.

playlists.json      [{id, name, source, kind, type_mode, count, updated}]
entries_<id>.json   [{name, logo, group, url, type}]   (channels of one playlist)
favorites.json      [{name, logo, group, url, type}]
"""
import io
import json
import os
import tempfile
import time
import uuid

KIND_URL = "url"
KIND_FILE = "file"
KIND_RADIO = "radiobrowser"


class Store(object):

    def __init__(self, data_dir):
        self.dir = data_dir
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

    # ── files ────────────────────────────────────────────────────────────
    def _path(self, name):
        return os.path.join(self.dir, name)

    def _load(self, name, default):
        try:
            with io.open(self._path(name), "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, OSError, ValueError):
            return default

    def _save(self, name, data):
        """Write to a unique temporary file, then replace the old file in one step: an interrupted
        save never leaves the data missing."""
        fd, tmp = tempfile.mkstemp(prefix=name + ".", suffix=".tmp", dir=self.dir)
        try:
            with io.open(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False))
            os.replace(tmp, self._path(name))
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    # ── playlists ────────────────────────────────────────────────────────
    def playlists(self):
        return self._load("playlists.json", [])

    def playlist(self, playlist_id):
        return next((p for p in self.playlists() if p["id"] == playlist_id), None)

    def add_playlist(self, name, source, kind, type_mode):
        playlist = {"id": uuid.uuid4().hex[:12], "name": name, "source": source, "kind": kind,
                    "type_mode": type_mode, "count": 0, "updated": 0}
        self._save("playlists.json", self.playlists() + [playlist])
        return playlist

    def save_entries(self, playlist_id, entries):
        self._save("entries_%s.json" % playlist_id, entries)
        playlists = self.playlists()
        for p in playlists:
            if p["id"] == playlist_id:
                p["count"] = len(entries)
                p["updated"] = int(time.time())
        self._save("playlists.json", playlists)

    def delete_playlist(self, playlist_id):
        self._save("playlists.json", [p for p in self.playlists() if p["id"] != playlist_id])
        try:
            os.remove(self._path("entries_%s.json" % playlist_id))
        except OSError:
            pass

    def entries(self, playlist_id):
        return self._load("entries_%s.json" % playlist_id, [])

    # ── channels (entries merged across playlists) ───────────────────────
    def channels(self, stream_type, group=None, query=None):
        """Entries with the same name and category = one channel with several links (fallback)."""
        merged = {}
        order = []
        query = (query or "").lower()
        for p in self.playlists():
            for e in self.entries(p["id"]):
                if e["type"] != stream_type:
                    continue
                if group is not None and e["group"] != group:
                    continue
                if query and query not in e["name"].lower():
                    continue
                key = (e["group"], e["name"])
                channel = merged.get(key)
                if channel is None:
                    channel = {"name": e["name"], "group": e["group"], "logo": e["logo"],
                               "type": stream_type, "links": []}
                    merged[key] = channel
                    order.append(key)
                if not channel["logo"] and e["logo"]:
                    channel["logo"] = e["logo"]
                if e["url"] not in channel["links"]:
                    channel["links"].append(e["url"])
        return [merged[k] for k in order]

    def channel(self, stream_type, group, name):
        return next((c for c in self.channels(stream_type, group) if c["name"] == name), None)

    def groups(self, stream_type):
        """[(group, channel_count)] in playlist order."""
        counts = {}
        order = []
        for c in self.channels(stream_type):
            if c["group"] not in counts:
                counts[c["group"]] = 0
                order.append(c["group"])
            counts[c["group"]] += 1
        return [(g, counts[g]) for g in order]

    def has_channels(self):
        return any(p.get("count") for p in self.playlists())

    # ── favorites ────────────────────────────────────────────────────────
    def favorites(self):
        return self._load("favorites.json", [])

    def add_favorite(self, item):
        favorites = [f for f in self.favorites() if f["url"] != item["url"]]
        self._save("favorites.json", favorites + [item])

    def remove_favorite(self, url):
        self._save("favorites.json", [f for f in self.favorites() if f["url"] != url])

    def move_favorite(self, url, offset):
        favorites = self.favorites()
        i = next((n for n, f in enumerate(favorites) if f["url"] == url), None)
        if i is None:
            return
        j = max(0, min(len(favorites) - 1, i + offset))
        favorites.insert(j, favorites.pop(i))
        self._save("favorites.json", favorites)
