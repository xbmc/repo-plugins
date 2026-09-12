import json
import os
import tempfile
import threading
import time
import urllib.parse

import requests
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

from resources.lib import sync_state

MDBLIST_CLIENT_ID = "Jfx43IWpbKcEOoRdnjgZ00eBpcKCRM4mVHALZSc4"

DEVICE_AUTH_URL = "https://api.mdblist.com/oauth/device-authorization/"
TOKEN_URL = "https://api.mdblist.com/oauth/token/"
REVOKE_URL = "https://api.mdblist.com/oauth/revoke_token/"
DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

REQUEST_TIMEOUT = 10


def _addon():
    return xbmcaddon.Addon()


def _token_path():
    profile = xbmcvfs.translatePath(_addon().getAddonInfo("profile"))
    return os.path.join(profile, "oauth_tokens.json")


def _load_tokens():
    try:
        with open(_token_path(), "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_tokens(data):
    path = _token_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def get_access_token():
    return _load_tokens().get("access_token", "")


def get_refresh_token():
    return _load_tokens().get("refresh_token", "")


def _get_token_expires_at():
    try:
        return float(_load_tokens().get("expires_at", 0))
    except (ValueError, TypeError):
        return 0.0


def save_tokens(access_token, refresh_token, expires_at):
    _write_tokens({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(expires_at),
    })
    _addon().setSettingString("oauth_status", "Connected")


def clear_tokens():
    try:
        os.remove(_token_path())
    except Exception:
        pass
    _addon().setSettingString("oauth_status", "Not connected")


def _try_refresh():
    refresh_tok = get_refresh_token()
    if not refresh_tok:
        return False
    try:
        r = requests.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_tok,
            "client_id": MDBLIST_CLIENT_ID,
        }, timeout=REQUEST_TIMEOUT)
        data = r.json()
        if data.get("access_token"):
            expires_at = time.time() + data.get("expires_in", 2592000)
            save_tokens(data["access_token"], data.get("refresh_token", refresh_tok), expires_at)
            xbmc.log("MDBList Scrobbler: OAuth token refreshed", level=xbmc.LOGDEBUG)
            return True
    except Exception as e:
        xbmc.log("MDBList Scrobbler: Token refresh failed - {}".format(e), level=xbmc.LOGERROR)
    return False


def ensure_valid_token():
    """Return a valid access token, refreshing if near expiry. Returns '' if not OAuth-authenticated."""
    tokens = _load_tokens()
    access_token = tokens.get("access_token", "")
    if not access_token:
        return ""
    try:
        expires_at = float(tokens.get("expires_at", 0) or 0)
    except (ValueError, TypeError):
        expires_at = 0.0
    if expires_at and time.time() > expires_at - 300:
        if _try_refresh():
            access_token = _load_tokens().get("access_token", "")
    return access_token


def _fetch_qr_code(complete_url):
    """Download a QR code PNG for complete_url to a temp file. Returns the file path."""
    qr_api = "https://api.qrserver.com/v1/create-qr-code/?size=220x220&bgcolor=ffffff&color=000000&margin=10&data={}".format(
        urllib.parse.quote(complete_url, safe="")
    )
    r = requests.get(qr_api, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    path = os.path.join(tempfile.gettempdir(), "mdblist_oauth_qr.png")
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def _poll_for_token(dialog, device_code, interval, expires_in):
    """Background thread: polls MDBList token endpoint until authorized, cancelled, or expired."""
    deadline = time.time() + expires_in

    while time.time() < deadline and not dialog.cancelled:
        xbmc.sleep(interval * 1000)

        if dialog.cancelled:
            return

        try:
            r = requests.post(TOKEN_URL, data={
                "grant_type": DEVICE_GRANT_TYPE,
                "device_code": device_code,
                "client_id": MDBLIST_CLIENT_ID,
            }, timeout=REQUEST_TIMEOUT)
            poll = r.json()
        except Exception:
            continue

        if poll.get("access_token"):
            expires_at = time.time() + poll.get("expires_in", 2592000)
            save_tokens(poll["access_token"], poll.get("refresh_token", ""), expires_at)
            dialog.set_authorized()
            return

        error = poll.get("error", "")
        if error == "slow_down":
            interval += 5
        elif error in ("expired_token", "access_denied"):
            break

    if not dialog.cancelled and not dialog.authorized:
        dialog.set_status("Authorization expired. Please try again.")
        xbmc.sleep(2000)
        dialog.close()


def run_connect_flow():
    """Start OAuth device flow. Shows a Kodi dialog with QR code and polls in background."""
    try:
        r = requests.post(
            DEVICE_AUTH_URL,
            data={"client_id": MDBLIST_CLIENT_ID, "scope": "write"},
            timeout=REQUEST_TIMEOUT,
        )
        data = r.json()
    except Exception as e:
        xbmcgui.Dialog().ok("MDBList OAuth", "Failed to start authorization: {}".format(str(e)[:120]))
        return

    if not data.get("device_code"):
        msg = data.get("error_description") or data.get("error") or "Unknown error"
        xbmcgui.Dialog().ok("MDBList OAuth", "Error: {}".format(msg))
        return

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data.get("verification_uri", "https://mdblist.com/oauth/device/")
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 300)

    # Use verification_uri_complete if provided, otherwise build it
    complete_url = data.get("verification_uri_complete") or "{}?user_code={}".format(
        verification_uri, user_code
    )

    qr_path = None
    try:
        qr_path = _fetch_qr_code(complete_url)
    except Exception as e:
        xbmc.log("MDBList Scrobbler: QR code fetch failed - {}".format(e), level=xbmc.LOGWARNING)

    from resources.lib.oauth_dialog import OAuthDialog
    addon_path = _addon().getAddonInfo("path")
    dialog = OAuthDialog("oauth_dialog.xml", addon_path)
    dialog.user_code = user_code
    dialog.verification_uri = verification_uri
    dialog.qr_path = qr_path

    poll_thread = threading.Thread(
        target=_poll_for_token,
        args=(dialog, device_code, interval, expires_in),
        daemon=True,
    )
    poll_thread.start()

    dialog.doModal()
    authorized = dialog.authorized
    del dialog

    if qr_path:
        try:
            os.unlink(qr_path)
        except Exception:
            pass

    if authorized:
        xbmcgui.Dialog().notification(
            "MDBList Scrobbler", "Connected to MDBList!", xbmcgui.NOTIFICATION_INFO, 3000
        )
        xbmc.log("MDBList Scrobbler: OAuth connected", level=xbmc.LOGINFO)
        _reopen_settings()


def run_disconnect():
    """Revoke the stored OAuth token and clear credentials."""
    access_token = get_access_token()
    if access_token:
        try:
            requests.post(
                REVOKE_URL,
                data={"token": access_token, "client_id": MDBLIST_CLIENT_ID},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception:
            pass
    clear_tokens()

    # A reconnect (same or different MDBList account) must not resume
    # against the previous account's cursors/known_items -- wipe sync
    # bookkeeping so the next run is a clean full resync.
    sync_state.reset_all()
    xbmc.log("MDBList Scrobbler: cleared sync state on disconnect", level=xbmc.LOGINFO)

    xbmcgui.Dialog().notification(
        "MDBList Scrobbler", "Disconnected from MDBList", xbmcgui.NOTIFICATION_INFO, 3000
    )
    xbmc.log("MDBList Scrobbler: OAuth disconnected", level=xbmc.LOGINFO)
    _reopen_settings()


def _reopen_settings():
    """Close and reopen the addon settings so visible conditions re-evaluate with fresh state."""
    xbmc.sleep(500)
    xbmc.executebuiltin("Addon.OpenSettings(service.mdblist-scrobbler)")
