"""Typed access to addon settings, and the hidden-settings credential store.

Hidden level-4 keys (see resources/settings.xml) hold the credentials;
:class:`Credentials` is the sole writer of those keys.
"""

import uuid
from typing import Optional

import xbmc
import xbmcaddon
import xbmcvfs

from kofin.core import auth, log

LOG = log.Logger(__name__)

ADDON_ID = "plugin.video.kofin"


def get_addon() -> Optional[xbmcaddon.Addon]:
    """This addon's ``Addon``, or None while Kodi has it unregistered.

    A fresh Addon per call: with reuselanguageinvoker a cached instance can
    serve stale values after another process wrote the settings.

    ``xbmcaddon.Addon()`` raises ``RuntimeError: Unknown addon id`` for as
    long as Kodi has the addon unloaded, and every update opens that window:
    ``CAddonInstallJob::DoWork`` unloads unconditionally before replacing any
    file, while every thread the addon started keeps running.

    So the lookup answers None and the accessors below degrade to their
    type's empty value. An empty read then means "the store is unavailable"
    as often as it means "the user cleared it", so anything destructive keyed
    on an emptied setting must corroborate it before acting
    (``service/settings_apply``'s ``LOAD_CANARY``). A *write* is silently
    dropped.
    """
    try:
        return xbmcaddon.Addon(ADDON_ID)
    except RuntimeError as error:
        # Per failed lookup, not once per window: a per-item read path can
        # make this a few hundred lines during a reinstall, which is the
        # right trade for an event that is otherwise invisible.
        LOG.warning("settings unavailable: %s", error)
        return None


def available() -> bool:
    """Whether the settings store can be read at all (see :func:`get_addon`)."""
    return get_addon() is not None


def get_str(setting_id: str) -> str:
    addon = get_addon()
    return addon.getSetting(setting_id) if addon is not None else ""


def set_str(setting_id: str, value: str) -> None:
    addon = get_addon()
    if addon is None:
        # Named, because a write that did not stick is harder to reason back
        # from than a read that came up empty.
        LOG.warning("dropped write of %s: settings unavailable", setting_id)
        return
    addon.setSetting(setting_id, value)


def get_bool(setting_id: str) -> bool:
    addon = get_addon()
    return addon.getSettingBool(setting_id) if addon is not None else False


def set_bool(setting_id: str, value: bool) -> None:
    addon = get_addon()
    if addon is None:
        LOG.warning("dropped write of %s: settings unavailable", setting_id)
        return
    addon.setSettingBool(setting_id, value)


def get_int(setting_id: str) -> int:
    addon = get_addon()
    return addon.getSettingInt(setting_id) if addon is not None else 0


def get_float(setting_id: str) -> float:
    """A numeric setting that may be fractional.

    Read as a string, because Kodi's ``integer`` type cannot express the
    sub-1 Mbit/s bitrate options and its ``number`` type is a slider. An
    unparseable or empty value reads as 0, which every caller already
    treats as "unlimited".
    """
    try:
        return float(get_str(setting_id) or 0)
    except ValueError:
        return 0.0


def get_list(setting_id: str) -> list[str]:
    raw = get_str(setting_id)
    return [part for part in (piece.strip() for piece in raw.split(",")) if part]


def _addon_info(field: str) -> str:
    addon = get_addon()
    return addon.getAddonInfo(field) if addon is not None else ""


def addon_version() -> str:
    return _addon_info("version")


def addon_path() -> str:
    """The installed addon directory, or "" while it is unregistered.

    Callers join media filenames onto this, so an empty answer yields a
    relative path that fails to open rather than one that opens the wrong
    file.
    """
    return _addon_info("path")


def addon_data_path() -> str:
    """The profile's addon_data directory for kofin."""
    return xbmcvfs.translatePath("special://profile/addon_data/" + ADDON_ID + "/")


def addon_name() -> str:
    return _addon_info("name")


def localized(string_id: int) -> str:
    addon = get_addon()
    return addon.getLocalizedString(string_id) if addon is not None else ""


def device_name() -> str:
    """How this device names itself to Jellyfin: Kodi's own friendly name
    (services.devicename, or "Kodi (host)" by default), matching pvr.kofin."""
    return xbmc.getInfoLabel("System.FriendlyName") or "Kodi"


def user_agent() -> str:
    """The User-Agent of every request and websocket handshake: Kodi's own,
    the one Kodi's player sends when it fetches the streams. Left to the
    libraries, the plugin's ``http.client`` and websocket-client send none and
    the service's requests sends ``python-requests/<version>``, and
    Cloudflare's Browser Integrity Check, on by default, challenges a request
    with no User-Agent or a non-standard one."""
    return xbmc.getUserAgent()


def resume_offset() -> float:
    """Seconds a resume point is rewound by (Advanced tab, stored negative).

    Never raises: the listing and play routes call this, and a settings read
    that failed must degrade to "no offset" rather than take the item down
    with it.
    """
    try:
        return abs(float(get_int("resumeJumpBack")))
    except Exception:  # pragma: no cover - defensive
        return 0.0


def adjusted_resume(position_seconds: float, offset: Optional[float] = None) -> float:
    """``position_seconds`` pulled back by :func:`resume_offset`.

    The single rule behind the two call sites that must agree — the resume
    point a listing advertises and the position playback actually starts at.
    If they disagree, Kodi's resume prompt names one time and playback lands
    on another.

    ``offset`` is a precomputed :func:`resume_offset`, for callers stamping a
    whole listing: reading the setting builds a fresh ``Addon`` every time
    (see :func:`get_addon`). None means read the setting here.

    A position shorter than the offset is left alone rather than clamped to
    zero, so a barely-started item keeps its in-progress bookmark instead of
    reverting to unwatched.
    """
    if offset is None:
        offset = resume_offset()
    if position_seconds > offset:
        return position_seconds - offset
    return position_seconds


class Credentials:
    """The hidden-settings credential record for the single server."""

    def __init__(
        self,
        server_address: str = "",
        server_name: str = "",
        server_id: str = "",
        user_id: str = "",
        display_user: str = "",
        token: str = "",
        device_id: str = "",
        is_logged_in: bool = False,
    ) -> None:
        self.server_address = server_address
        self.server_name = server_name
        self.server_id = server_id
        self.user_id = user_id
        self.display_user = display_user
        self.token = token
        self.device_id = device_id
        self.is_logged_in = is_logged_in

    @classmethod
    def load(cls) -> "Credentials":
        """The stored record, or a blank one while the store is unreadable.

        Read off a single ``Addon`` rather than through :func:`get_str` eight
        times, because the device-id mint below has to be decided on the same
        answer the reads got. Through the getters, an unregistered addon reads
        every key empty (see :func:`get_addon`) and the mint then *replaces* a
        good device id with one no ``set_str`` can store.

        A blank record reads as ``is_logged_in`` False, which callers treat
        as "not yet" rather than "logged out".
        """
        addon = get_addon()
        if addon is None:
            return cls()
        # Every client is built on the address as a sign-in stores it, and the
        # setting is put back to that: requests sends a URL's user name and
        # password as Basic auth, in place of the token's Authorization
        # header, and the settings dialog shows what the setting holds.
        stored_address = addon.getSetting("serverAddress")
        try:
            server_address = auth.normalize_address(stored_address)
        except ValueError:
            # An address no request can be made to is left as it stands, for
            # Log in to name (plugin/account.py).
            server_address = stored_address
        creds = cls(
            server_address=server_address,
            server_name=addon.getSetting("serverName"),
            server_id=addon.getSetting("serverId"),
            user_id=addon.getSetting("userId"),
            display_user=addon.getSetting("displayUser"),
            token=addon.getSetting("accessToken"),
            device_id=addon.getSetting("deviceId"),
            is_logged_in=addon.getSettingBool("isLoggedIn"),
        )
        if creds.server_address != stored_address:
            set_str("serverAddress", creds.server_address)
        if not creds.device_id:
            creds.device_id = uuid.uuid4().hex
            set_str("deviceId", creds.device_id)
        creds._register_secrets()
        return creds

    def save(self) -> None:
        set_str("serverAddress", self.server_address)
        set_str("serverName", self.server_name)
        set_str("serverId", self.server_id)
        set_str("userId", self.user_id)
        set_str("displayUser", self.display_user)
        set_str("accessToken", self.token)
        set_str("deviceId", self.device_id)
        set_bool("isLoggedIn", self.is_logged_in)
        self._register_secrets()

    @classmethod
    def clear(cls) -> None:
        """Log out: drop the session, keep the server address and device id.

        Also clears ``whoIsWatching``: additional-user membership is tied to
        this primary user on this device. A later login as someone else must
        not re-attach the previous household's co-watchers. The shortlist is
        left alone — it is a device preference about who the picker offers.
        """
        for setting_id in (
            "serverName",
            "serverId",
            "userId",
            "displayUser",
            "accessToken",
            "whoIsWatching",
        ):
            set_str(setting_id, "")
        set_bool("isLoggedIn", False)

    def _register_secrets(self) -> None:
        if self.token:
            log.register_secret(self.token)
        if self.user_id:
            log.register_secret(self.user_id, keep=6)
        if self.device_id:
            log.register_secret(self.device_id, keep=6)
