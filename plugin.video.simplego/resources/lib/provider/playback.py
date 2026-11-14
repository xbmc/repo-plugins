"""Playback sessions: device registration, roll, the licence's headers and certificate, beacons."""

import base64
import hashlib
import json
import re
import time
import uuid
from urllib.parse import parse_qsl
from urllib.parse import quote
from urllib.parse import urlencode

from resources.lib.provider import core
from resources.lib.provider import errors
from resources.lib.provider import servicecert
from resources.lib.util import isotime

# Full HD (see _ask_full_hd).
FULL_HD_DEVICE_CLASS = "AndroidSTB_wv1"
FULL_HD_REWIND = 15 * 60
FULL_HD_HORIZON = 6 * 3600
DEVICE_CLASS = re.compile(r"(mgr_(?:live|vod)_dash_[a-z]+_)[A-Za-z0-9]+_wv\d+")

# The provider's error codes the client acts on.
CODE_ADDRESS_BLOCKED = 7027
CODE_DEVICE_REMOVED = 3008
CODE_NOT_IN_ARCHIVE = 2401
CODE_CATCHUP_EXPIRED = 2425
CODE_NOT_SUBSCRIBED = 3097
CODE_STREAM_LIMIT = 2413

# Seconds between beacons when the roll names no interval.
DEFAULT_BEACON_INTERVAL = 240
# How long the Widevine service certificate is kept (seconds).
SERVICE_CERTIFICATE_KEPT = 7 * 24 * 3600

DEVICE_PROFILE = {
    "model": "Desktop",
    "osVersion": "10",
    "vendorName": "Microsoft",
    "osName": "HTML5",
    "wvLevel": "L3",
}


class Playback:
    """Stream sessions, the licence's headers and certificate, and the open sessions kept in the state.

    :param state: the client's statefile.State
    :param api: the client's core.Api
    :param auth: the client's auth.Auth
    :param channels: the client's channels.Channels (the subscription a start is checked against)
    """

    def __init__(self, state, api, auth, channels):
        self._state = state
        self._api = api
        self._auth = auth
        self._channels = channels
        # The AMP registration belonged to the removed device: the next start registers again.
        auth.on_device_readded(lambda: self._state.pop("registered_token", None))

    def licence_headers(self, channel_id):
        """Return the licence request headers, with a current access token."""
        return self._amp_headers(channel_id)

    def _amp_headers(self, channel_id):
        profile = dict(DEVICE_PROFILE, deviceUUID=self._state["device_uuid"])
        return {
            "ApplicationToken": str(channel_id),
            "AuthorizationToken": self._auth.valid_access_token(),
            "AzukiIMC": core.AZUKI_IMC,
            "Content-Type": "text/plain",
            "DeviceProfile": base64.b64encode(json.dumps(profile, separators=(",", ":")).encode()).decode(),
            "Origin": core.BASE_URL,
            "Referer": core.BASE_URL + "/",
        }

    def _amp(self, path, params, body, channel_id):
        r = self._api.http.post(
            core.AMP_URL + path,
            params=params,
            data=json.dumps(body, separators=(",", ":")),
            headers=self._amp_headers(channel_id),
            timeout=core.TIMEOUT,
        )
        try:
            data = r.json()
        except ValueError:
            raise errors.ApiError("%s -> HTTP %s: %s" % (path, r.status_code, r.text[:300])) from None
        if data.get("result") != "success":
            err = data.get("response") or {}
            msg = "%s -> HTTP %s, code %s: %s" % (path, r.status_code, err.get("code"), err.get("message"))
            if err.get("code") == CODE_ADDRESS_BLOCKED:
                raise errors.GeoBlockedError(msg)
            raise errors.ApiError(msg, code=err.get("code"))
        return data.get("response") or {}

    def _register_device(self, channel_id):
        self._amp("/v1/client/registrations", {"ownerUid": core.OWNER_UID}, {}, channel_id)
        self._state["registered_token"] = self._registration_mark()
        self._state["registered_channel"] = channel_id  # for get_ready
        self._state.save()

    def get_ready(self, ahead):
        """Renew in the background what the next channel start would otherwise wait for.

        The startup page (a 5 MB download) and the login are renewed if they expire within
        `ahead` seconds, and the device re-registered for a new token.
        """
        st = self._state
        if st.get("config_at", 0) + core.CONFIG_TTL - ahead < time.time():
            self._api.bootstrap(force=True)
        if not self._auth.authed:
            return
        if st.get("registered_channel") and st.get("registered_token") != self._registration_mark(ahead):
            self._register_device(st["registered_channel"])

    def _registration_mark(self, ahead=core.TOKEN_SKEW):
        """Return a hash of the access token and profile the device is registered for."""
        token = self._auth.valid_access_token(ahead) + json.dumps(DEVICE_PROFILE, sort_keys=True)
        return hashlib.sha256(token.encode()).hexdigest()

    def play_live(self, channel, programme=None, laps=None, full_hd=False):
        """Open a live session.

        :param channel: an entry of channels.Channels.list
        :param programme: (guidedata.from_param) play it from its beginning: restarted in
            the live session if still on air, else a catch-up session for its start time
        :param laps: laps(step) after each step (see resources.lib.util.laps)
        :param full_hd: ask for the Full HD (1080p) profile, the web one kept as the fallback (see _ask_full_hd)
        :return: manifest URL, type and Widevine licence details; window_end: when a live window
            ends (a timestamp), None if it has none (see windowrenewal)
        """
        laps = laps or (lambda step: None)
        programme, restart = self._playable(channel, programme)
        self._api.bootstrap()
        # Once per access token (and profile), like the web client.
        if self._state.get("registered_token") != self._registration_mark():
            self._register_device(channel["id"])
        laps("login")
        session_id = str(uuid.uuid4())
        params = {
            "mediaId": channel["media_id"],
            "ownerUid": core.OWNER_UID,
            "sessionId": session_id,
            "enablelowlatency": "false",
        }
        if programme and not restart:
            body = {"roll": {"isLive": False, "rightsMode": "VOD_STREAMING", "startTime": programme["start"], "inhome": "yes"}}
        else:
            body = {"roll": {"isLive": True, "rightsMode": "LIVE", "inhome": "yes"}}
        roll = self._roll(channel, programme, params, body)
        laps("roll")
        session = {
            "channel_id": channel["id"],
            "media_id": channel["media_id"],
            "session_id": session_id,
            "interval": int(roll.get("beacon_interval") or DEFAULT_BEACON_INTERVAL),
        }
        # Recorded so a crash or failed start does not leave it counting against the stream limit.
        self._state.change(lambda st: st.update(open_sessions=(st.get("open_sessions") or []) + [session]))
        laps("kept")
        cdn = (roll.get("cdns") or {}).get("cdn") or []
        if not cdn or not roll.get("manifest_uri"):
            raise errors.ApiError("roll response has no manifest: %s" % json.dumps(roll)[:500])
        web_manifest = cdn[0]["base_uri"].rstrip("/") + "/" + roll["manifest_uri"].lstrip("/")
        if restart:
            web_manifest = web_manifest.replace("start=LIVE", "start=" + programme["start"], 1)
        manifest, window_end = _ask_full_hd(web_manifest, programme) if full_hd else (web_manifest, None)
        lic_params = "mediaId=%s&ownerUid=%s&sessionId=%s&enablelowlatency=false" % (
            quote(channel["media_id"], safe=""),
            core.OWNER_UID,
            session_id,
        )
        license_url = core.AMP_URL + "/v1/client/get-widevine-license?" + lic_params
        license_headers = self._amp_headers(channel["id"])
        certificate = self._service_certificate(license_url, license_headers)
        laps("certificate")
        return {
            "manifest": manifest,
            "manifest_fallback": web_manifest if full_hd else None,
            "type": (roll.get("package_type") or "dash").lower(),
            "license_url": license_url,
            "license_headers": license_headers,
            "server_certificate": certificate,
            "user_agent": core.USER_AGENT,
            "session": session,
            "from_start": restart,
            "window_end": window_end,
        }

    def _playable(self, channel, programme):
        """Return (programme, restart) for play_live, after the web player's own checks.

        :raises errors.NotSubscribedError: the channel is outside the subscription
        :raises errors.RestartNotAllowedError: the programme on air may not restart ("rn")
        :raises errors.ArchiveUnavailableError: the programme is not in the archive ("ct")
        """
        subscribed = self._channels.subscribed_ids(fetch=False)
        if subscribed is not None and channel["id"] not in subscribed:
            raise errors.NotSubscribedError("channel %s is not in the subscription" % channel["id"])
        if programme and programme["start"] > isotime.iso():
            programme = None  # not on yet: play live
        restart = bool(programme) and programme["end"] > time.time()
        if restart and "rn" in programme["flags"]:
            raise errors.RestartNotAllowedError("restart not allowed for %s" % programme["start"])
        if programme and not restart and "ct" not in programme["flags"]:
            raise errors.ArchiveUnavailableError("no catch-up for %s" % programme["start"])
        return programme, restart

    def _roll(self, channel, programme, params, body):
        """Open the stream session ("roll"), retrying once after a recoverable error.

        :raises errors.ArchiveUnavailableError: the archive has not got it
        :raises errors.CatchupExpiredError: its catch-up time is over (when varies by channel, see continuelist)
        :raises errors.NotSubscribedError: the channel is outside the subscription
        """
        try:
            return self._amp("/v1/client/roll", params, body, channel["id"])
        except errors.ApiError as e:
            if e.code == CODE_DEVICE_REMOVED:
                self._auth.readd_device()
                self._register_device(channel["id"])
            elif e.code == CODE_NOT_IN_ARCHIVE and programme:
                raise errors.ArchiveUnavailableError(str(e)) from e
            elif e.code == CODE_CATCHUP_EXPIRED and programme:
                raise errors.CatchupExpiredError(str(e)) from e
            elif e.code == CODE_NOT_SUBSCRIBED:
                raise errors.NotSubscribedError(str(e)) from e
            elif e.code == CODE_STREAM_LIMIT:
                # Stream limit: leftover sessions still count. Closed only here, not on
                # every start, to save a round trip per channel switch.
                self.close_stale_sessions()
            else:
                raise
        return self._amp("/v1/client/roll", params, body, channel["id"])

    def _service_certificate(self, license_url, headers):
        """Return the Widevine service certificate as base64 (kept a week); None if the server gave none.

        Kodi's CDM only encrypts its client ID (privacy mode, as the web player) when given it.
        """
        st = self._state
        if st.get("wv_service_cert") and st.get("wv_cert_at", 0) + SERVICE_CERTIFICATE_KEPT > time.time():
            return st["wv_service_cert"]
        try:
            r = self._api.http.post(license_url, data=servicecert.REQUEST, headers=headers, timeout=core.TIMEOUT)
            cert = servicecert.unwrap(r.content) if r.ok else None
            if cert:
                st["wv_service_cert"] = base64.b64encode(cert).decode()
                st["wv_cert_at"] = time.time()
                self._state.save()
                return st["wv_service_cert"]
        except errors.ApiError:  # a network failure
            pass
        return None

    def beacon(self, session, complete=False):
        """Keep a playback session alive, or close it with complete=True.

        An uncompleted session counts against the concurrent-stream limit (2413)
        until the server times it out.
        """
        params = {"mediaId": session["media_id"], "ownerUid": core.OWNER_UID, "sessionId": session["session_id"]}
        resp = self._amp(
            "/v1/client/beacons",
            params,
            {"beacon": {"isLive": True, "complete": complete, "inhome": "yes"}},
            session["channel_id"],
        )
        if complete:
            self._forget_session(session)
        return resp

    def _forget_session(self, session):
        # On the file's copy (see State.change): another invocation may have added its session meanwhile.
        gone = session["session_id"]
        self._state.change(
            lambda st: st.update(open_sessions=[s for s in st.get("open_sessions") or [] if s["session_id"] != gone])
        )

    def close_stale_sessions(self, keep=None):
        """Complete every session still on record, except the one with id `keep`."""
        for s in list(self._state.on_disk().get("open_sessions") or []):
            if s["session_id"] == keep:
                continue
            try:
                self.beacon(s, complete=True)
            except errors.ApiError:
                # Already gone server-side.
                self._forget_session(s)


def _ask_full_hd(manifest, programme):
    """Return (the manifest URL for Full HD (1080p), when its live window ends or None); as it is without a device profile."""
    base, _, query = manifest.partition("?")
    params = dict(parse_qsl(query))
    if not DEVICE_CLASS.search(params.get("device", "")):
        return manifest, None
    now = time.time()
    if programme and programme["end"] <= now:
        start, end, window_end = programme["start"], isotime.iso(programme["end"]), None
    else:
        window_end = now + FULL_HD_HORIZON
        start = programme["start"] if programme else isotime.iso(now - FULL_HD_REWIND)
        end = isotime.iso(window_end)
    params["device"] = DEVICE_CLASS.sub(r"\g<1>" + FULL_HD_DEVICE_CLASS, params["device"])
    params["start"], params["end"] = start, end
    return base + "?" + urlencode(params, safe=":"), window_end
