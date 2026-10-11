# -*- coding: utf-8 -*-
"""AudioAddict/JazzRadio API client used by the Kodi add-on.

The V1 client deliberately exposes only the functionality required by the
linear radio experience: authentication, channel discovery, favourites,
Now Playing metadata and Premium stream resolution.

Interactive routine/vote/skip endpoints explored during development are
intentionally not part of the V1 code path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import requests
import tempfile
import xbmc
import xbmcaddon
import xbmcvfs
import hashlib

ADDON_ID = "plugin.audio.jazzradio"


class AudioAddictError(RuntimeError):
    """Expected API/network error suitable for presentation to the user."""


class AudioAddictClient:
    """Small synchronous client for the AudioAddict API used by JazzRadio."""

    API = "https://api.audioaddict.com/v1"
    NETWORK = "jazzradio"
    DOMAIN = "jazzradio.com"

    # Credentials used by AudioAddict's own public-facing stream clients.
    # This is not the user's account credential.
    BASIC_USER = "streams"
    BASIC_PASSWORD = "diradio"

    QUALITY_MAP = {
        "Medium": "premium_medium",  # AAC-HE 64 kb/s
        "High": "premium",           # AAC 128 kb/s
        "Ultra": "premium_high",     # MP3 320 kb/s
    }

    def __init__(self):
        self.addon = xbmcaddon.Addon(ADDON_ID)
        profile = xbmcvfs.translatePath(self.addon.getAddonInfo("profile"))
        os.makedirs(profile, exist_ok=True)

        self.session_path = Path(profile) / "session.json"
        self.http = requests.Session()
        version = self.addon.getAddonInfo("version")
        self.http.headers.update({
            "User-Agent": f"Kodi JazzRadio/{version}",
            "Accept": "application/json, */*",
        })
        self._session = self._load_session()

    def _t(self, string_id):
        """Return a localized add-on string."""
        return self.addon.getLocalizedString(string_id)

    @staticmethod
    def _log(message, level=xbmc.LOGDEBUG):
        xbmc.log(f"[plugin.audio.jazzradio] {message}", level)


    @staticmethod
    def _safe_url_for_log(url):
        """Return a URL representation without query parameters or fragments."""
        try:
            parts = urlsplit(str(url))
            return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        except Exception:
            return "<unparseable-url>"

    def has_credentials(self):
        """Whether account credentials are configured in Kodi settings."""
        return bool(
            self.addon.getSetting("email").strip()
            and self.addon.getSetting("password")
        )

    def _credentials_fingerprint(self):
        email = self.addon.getSetting("email").strip().lower()
        password = self.addon.getSetting("password")
        value = f"{email}\0{password}".encode("utf-8")
        return hashlib.sha256(value).hexdigest()


    def _load_session(self):
        """Load the cached API session from the add-on profile."""
        try:
            if self.session_path.exists():
                data = json.loads(
                    self.session_path.read_text(encoding="utf-8")
                )
                if data.get("session_key") and data.get("user_id"):
                    return data
        except Exception as exc:
            self._log(f"Unable to read session cache: {exc}")
        return None

    def _save_session(self, data):
        """Persist a successful login atomically with private permissions."""
        temp_path = None
        try:
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{self.session_path.name}.",
                suffix=".tmp",
                dir=self.session_path.parent,
            )
            temp_path = Path(temp_name)

            try:
                os.fchmod(fd, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(data, handle, indent=2)
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise

            os.replace(temp_path, self.session_path)
            temp_path = None

        except Exception as exc:
            self._log(f"Unable to write session cache: {exc}", xbmc.LOGWARNING)
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass
                except Exception as exc:
                    self._log(
                        f"Unable to remove temporary session cache: {exc}",
                        xbmc.LOGDEBUG,
                    )

    def _clear_session(self):
        """Forget an invalid/expired session; account credentials are retained."""
        self._session = None
        try:
            if self.session_path.exists():
                self.session_path.unlink()
        except Exception as exc:
            self._log(
                f"Unable to remove session cache: {exc}",
                xbmc.LOGWARNING,
            )

    def _login(self):
        """Create and cache a fresh AudioAddict member session."""
        email = self.addon.getSetting("email").strip()
        password = self.addon.getSetting("password")

        if not email or not password:
            raise AudioAddictError(self._t(32100))

        url = f"{self.API}/{self.NETWORK}/member_sessions"
        try:
            response = self.http.post(
                url,
                json={
                    "member_session": {
                        "username": email,
                        "password": password,
                    }
                },
                auth=(self.BASIC_USER, self.BASIC_PASSWORD),
                timeout=20,
            )
        except requests.RequestException:
            raise AudioAddictError(self._t(32101))

        if response.status_code == 429:
            retry = response.headers.get("Retry-After")
            message = self._t(32102)
            if retry:
                message = f"{message} {self._t(32103).format(retry=retry)}"
            raise AudioAddictError(message)

        if response.status_code not in (200, 201):
            raise AudioAddictError(
                self._t(32104).format(code=response.status_code)
            )

        try:
            body = response.json()
        except ValueError:
            raise AudioAddictError(self._t(32105))

        member = (
            body.get("member")
            if isinstance(body.get("member"), dict)
            else {}
        )
        data = {
            "user_id": body.get("member_id"),
            "session_key": body.get("key"),
            "listen_key": member.get("listen_key"),
        }

        if not all(
            (
                data["user_id"],
                data["session_key"],
                data["listen_key"],
            )
        ):
            raise AudioAddictError(self._t(32106))

        data["credentials_fingerprint"] = self._credentials_fingerprint()

        self._save_session(data)
        self._log("New AudioAddict session created and cached")
        return data

    def _ensure_session(self):
        """Reuse a cached session only for the currently configured credentials."""

        fingerprint = self._credentials_fingerprint()

        if (
            self._session
            and self._session.get("session_key")
            and self._session.get("credentials_fingerprint") == fingerprint
        ):
            return self._session

        if self._session:
            self._clear_session()

        return self._login()

    def _get(self, path, authenticated=True, timeout=20):
        """GET JSON, retrying once after an expired authenticated session."""
        headers = {}

        if authenticated:
            session = self._ensure_session()
            headers["X-Session-Key"] = session["session_key"]

        url = (
            path
            if path.startswith("http")
            else f"{self.API}/{self.NETWORK}{path}"
        )

        try:
            response = self.http.get(
                url,
                headers=headers,
                timeout=timeout,
            )
        except requests.RequestException:
            raise AudioAddictError(self._t(32107))

        if authenticated and response.status_code in (401, 403):
            self._clear_session()
            session = self._login()
            headers["X-Session-Key"] = session["session_key"]
            try:
                response = self.http.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                )
            except requests.RequestException:
                raise AudioAddictError(self._t(32107))

        if response.status_code != 200:
            raise AudioAddictError(
                self._t(32108).format(code=response.status_code)
            )

        try:
            return response.json()
        except ValueError:
            raise AudioAddictError(self._t(32109))

    def _write(self, method, path, payload=None):
        """Authenticated write request used for favourite synchronisation."""
        session = self._ensure_session()
        url = f"{self.API}/{self.NETWORK}{path}"
        headers = {"X-Session-Key": session["session_key"]}

        try:
            response = self.http.request(
                method,
                url,
                headers=headers,
                json=payload,
                timeout=20,
            )
        except requests.RequestException:
            raise AudioAddictError(self._t(32107))

        if response.status_code in (401, 403):
            self._clear_session()
            session = self._login()
            headers["X-Session-Key"] = session["session_key"]
            try:
                response = self.http.request(
                    method,
                    url,
                    headers=headers,
                    json=payload,
                    timeout=20,
                )
            except requests.RequestException:
                raise AudioAddictError(self._t(32107))

        if response.status_code not in (200, 201, 204):
            raise AudioAddictError(
                self._t(32108).format(code=response.status_code)
            )

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return None

    def channel_filters(self):
        """Return AudioAddict's current JazzRadio navigation filters/channels."""
        return self._get("/channel_filters")

    def favorite_channel_ids(self):
        """Return the current user's favourite JazzRadio channel IDs."""
        session = self._ensure_session()
        favourites = self._get(
            f"/members/{session['user_id']}/favorites/channels"
        )
        ids = set()

        for item in favourites if isinstance(favourites, list) else []:
            if not isinstance(item, dict):
                continue
            channel_id = item.get("channel_id", item.get("id"))
            if channel_id is not None:
                ids.add(str(channel_id))

        return ids

    def favorite_channels(self):
        """Return rich channel objects for the user's favourites."""
        ids = self.favorite_channel_ids()
        channels = self._get("/channels", authenticated=False)
        by_id = {
            str(channel.get("id")): channel
            for channel in channels
            if isinstance(channel, dict) and channel.get("id") is not None
        }
        return [
            by_id[channel_id]
            for channel_id in ids
            if channel_id in by_id
        ]

    def add_favorite(self, channel_id):
        """Synchronise a newly-added favourite to the AudioAddict account."""
        session = self._ensure_session()
        return self._write(
            "POST",
            (
                f"/members/{session['user_id']}"
                f"/favorites/channel/{channel_id}"
            ),
            {"id": channel_id},
        )

    def remove_favorite(self, channel_id):
        """Synchronise favourite removal to the AudioAddict account."""
        session = self._ensure_session()
        return self._write(
            "DELETE",
            (
                f"/members/{session['user_id']}"
                f"/favorites/channel/{channel_id}"
            ),
        )

    def current_track(self, channel_key, known_track_id=None):
        """Return Now Playing metadata for one linear JazzRadio channel.

        The lightweight `/currently_playing` response is always sufficient to
        detect a track change.  Rich `/tracks/{id}` metadata is fetched only
        when the track differs from ``known_track_id`` (or when no known ID is
        supplied, as during initial playback).
        """
        try:
            now_playing = self._get("/currently_playing")
        except AudioAddictError as exc:
            self._log(
                f"Unable to retrieve currently playing metadata: {exc}",
                xbmc.LOGDEBUG,
            )
            return None

        if not isinstance(now_playing, list):
            return None

        for item in now_playing:
            if not (
                isinstance(item, dict)
                and item.get("channel_key") == channel_key
            ):
                continue

            track = item.get("track")
            if not isinstance(track, dict):
                return None

            result = dict(track)
            result["channel_id"] = item.get("channel_id")

            track_id = track.get("id")
            if track_id and track_id != known_track_id:
                try:
                    details = self._get(f"/tracks/{track_id}")
                    if isinstance(details, dict):
                        result.update(details)
                except AudioAddictError as exc:
                    # Basic Now Playing metadata is still useful if the
                    # secondary rich-track lookup fails.
                    self._log(
                        f"Unable to retrieve detailed metadata for track "
                        f"{track_id}: {exc}",
                        xbmc.LOGDEBUG,
                    )

            return result

        return None

    def _quality_variant(self):
        quality = self.addon.getSetting("quality") or "Ultra"
        return self.QUALITY_MAP.get(quality, "premium_high")

    def _playlist_servers(self, channel_key):
        """Resolve the PLS playlist for the selected Premium quality."""
        session = self._ensure_session()
        listen_key = session["listen_key"]
        variant = self._quality_variant()

        url = (
            f"https://listen.{self.DOMAIN}/{variant}/"
            f"{quote(channel_key)}.pls"
            f"?listen_key={quote(listen_key)}"
        )

        try:
            response = self.http.get(url, timeout=15)
        except requests.RequestException:
            raise AudioAddictError(self._t(32110))

        if response.status_code != 200:
            raise AudioAddictError(
                self._t(32111).format(code=response.status_code)
            )

        servers = []
        for raw_line in response.text.splitlines():
            line = raw_line.strip()
            if line.lower().startswith("file") and "=" in line:
                candidate = line.split("=", 1)[1].strip()
                if candidate.startswith("http"):
                    servers.append(candidate)

        if not servers:
            raise AudioAddictError(self._t(32112))

        return servers

    def resolve_stream(self, channel_key):
        """Return a playable linear stream URL, with conservative fallback."""
        servers = self._playlist_servers(channel_key)

        # Keep startup responsive: probe at most the first two playlist
        # candidates with short streamed GET requests. A network error or
        # timeout is inconclusive, so Kodi is still allowed to try that URL.
        # An explicit HTTP rejection is treated as a negative result.
        probe_limit = min(len(servers), 2)
        inconclusive = []

        for server in servers[:probe_limit]:
            response = None
            safe_server = self._safe_url_for_log(server)

            try:
                response = self.http.get(
                    server,
                    headers={"Icy-MetaData": "1"},
                    allow_redirects=True,
                    stream=True,
                    timeout=(2, 2),
                )

                if 200 <= response.status_code < 400:
                    return server, len(servers)

                self._log(
                    f"Stream probe rejected {safe_server} "
                    f"(HTTP {response.status_code})"
                )

            except requests.RequestException as exc:
                inconclusive.append(server)
                self._log(
                    f"Stream probe inconclusive for {safe_server}: "
                    f"{type(exc).__name__}"
                )

            finally:
                if response is not None:
                    response.close()

        # A timeout/connection failure does not prove that Kodi cannot play
        # the stream. Let Kodi try the first inconclusive candidate.
        if inconclusive:
            fallback = inconclusive[0]
            self._log(
                "Using an inconclusive stream candidate after bounded probing: "
                f"{self._safe_url_for_log(fallback)}",
                xbmc.LOGDEBUG,
            )
            return fallback, len(servers)

        # If the probed candidates were explicitly rejected but the playlist
        # contains further servers, avoid probing the entire list serially and
        # let Kodi try the next unprobed candidate directly.
        if len(servers) > probe_limit:
            fallback = servers[probe_limit]
            self._log(
                "Using an unprobed stream candidate after bounded probing: "
                f"{self._safe_url_for_log(fallback)}",
                xbmc.LOGDEBUG,
            )
            return fallback, len(servers)

        self._log(
            "All probed streaming servers were explicitly rejected",
            xbmc.LOGWARNING,
        )
        raise AudioAddictError(self._t(32110))

