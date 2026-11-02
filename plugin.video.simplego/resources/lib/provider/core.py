"""The client's core: the provider's addresses and constants, the startup page, bifrost calls."""

import contextlib
import json
import os
import re
import time

from resources.lib.provider import errors
from resources.lib.util import atomicfile

BASE_URL = "https://player.telekomtvgo.hu"
STARTUP_PAGE = BASE_URL + "/epg"
SSO_REDIRECT_URI = BASE_URL + "/"
PHONE_REDIRECT_URI = BASE_URL + "/robots.txt"
LANGUAGE = "hu"
NATCO = "hu"
OWNER_UID = "hu001"
# The web client calls AMP with a double slash ("...com//v1/client/roll"); keep
# it byte-identical rather than find out whether the gateway minds.
AMP_URL = "https://ottapp-appgw-amp-a.proda.dtp.tv3cloud.com/"
AZUKI_IMC = "IMC7.5.0_XX_Dx.x.x_Sx"
DEFAULT_STS_SLOT = "Green"

BROWSER = "Chrome"
BROWSER_VERSION = "141"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/%s.0.0.0 Safari/537.36" % BROWSER_VERSION
)
# The web client's device name: the add-on logs in as the web player does.
DEVICE_NAME = "Windows - Chrome"
# Fallbacks for window.APP_CONSTANTS; they rotate with web-client releases, so the live page wins.
DEFAULT_CONSTANTS = {
    "BFF_BASE_URL": "https://tv-hu-prod.yo-digital.com/bifrost",
    "NATCO_KEY": "Tydx7H7fJO6HxgjvJok0ZhVWFmX3om0P",
    "CMS_CONFIGURATION_API_KEY": "exSJHBiSAN6wAAeqdWLdTUfdTi2PNark",
    "APP_VERSION": "02.0.1470",
}

TIMEOUT = 20
CONFIG_TTL = 24 * 3600
ACCOUNT_TTL = 6 * 3600
STATE_FILE = "session.json"
CHANNELS_TTL = 3600
# Line-ups change only with the account's channel map; favourites and order (editable in
# the provider's apps) keep CHANNELS_TTL.
LINEUP_TTL = 12 * 3600
# Favourite programmes and resume positions, kept while browsing (see Personal._kept).
LIST_TTL = 5 * 60
POSITIONS_TTL = 90
# Renew early so a stream started at the edge still gets a valid licence.
TOKEN_SKEW = 600


def has_login(profile_dir):
    """Return whether profile_dir holds a refresh token; cheaper than building a client for menus."""
    state = atomicfile.read_json(os.path.join(profile_dir, STATE_FILE), {})
    return isinstance(state, dict) and bool(state.get("refresh_token"))


def token_expiry(token):
    """Return when a JWT runs out (its "exp", Unix time); None if it is not one."""
    try:
        payload = token.split(".")[1]
        import base64  # here: see _headers

        return int(json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["exp"])
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return None


def extract_refresh_token(text):
    """Return the refresh token in text, a bare token or a pasted URL holding one; "" if there is none."""
    text = (text or "").strip().strip("\"'")
    m = re.search(r"refresh_token=([^&#\s]+)", text)
    if m:
        text = m.group(1)
    return text if re.match(r"^[\w-]+\.[\w-]+\.[\w-]+$", text) else ""


class Api:
    """The provider's web API as the web player calls it: the startup page's constants, bifrost requests.

    Knows nothing of the login: a call with the login gets its token and account from Auth (see Auth.call).

    :param state: the client's statefile.State (device identity, constants)
    :param ca_bundle: certificates to verify the web player's host with, or a callable returning their path;
        the site omits its intermediate certificate
    :param debug: debug(message), where the startup page's timing goes
    """

    def __init__(self, state, ca_bundle=None, debug=None):
        self._state = state
        self._debug = debug or (lambda message: None)
        self._ca_bundle = ca_bundle or True
        self._http = None  # see http

    @property
    def http(self):
        """Return the HTTP session, made at the first request."""
        if self._http is None:
            # Lazy: http.client and ssl cost a fifth of a second on a TV stick.
            from resources.lib.net import transport

            # Network failures become ApiErrors so a dropped connection cannot end the service.
            self._http = transport.Session(error=errors.ApiError)
            self._http.headers["User-Agent"] = USER_AGENT
            self._http.verify = self.ca_bundle
        return self._http

    @property
    def ca_bundle(self):
        """Return the CA bundle's path (True: the default roots), resolved at first use."""
        if callable(self._ca_bundle):
            self._ca_bundle = self._ca_bundle()
        return self._ca_bundle

    def bootstrap(self, force=False):
        """Fetch the startup page for the device/session cookies and client constants (once a day)."""
        st = self._state
        if not force and st.get("config_at", 0) + CONFIG_TTL > time.time() and st.get("device_id"):
            return
        began = time.time()
        r = self.http.get(STARTUP_PAGE, timeout=TIMEOUT)
        if not r.ok:
            raise errors.ApiError("startup page -> HTTP %s" % r.status_code)
        self._debug(
            "startup page: %d kB in %.2fs (encoding %s)"
            % (len(r.content) // 1024, time.time() - began, r.headers.get("Content-Encoding") or "none")
        )
        cookies = r.cookies.get_dict()
        import uuid  # here: see _headers

        st["device_id"] = st.get("device_id") or cookies.get("deviceId") or str(uuid.uuid4())
        st["session_id"] = cookies.get("sessionId") or st.get("session_id") or str(uuid.uuid4())
        st.setdefault("device_uuid", str(uuid.uuid4()))
        st["consts"] = _app_constants(r.text)
        # The key the parental lock PIN is encrypted with (see Personal.verify_pin).
        key = re.search(r'"rsaPublicKey"\s*:\s*"([^"]+)"', r.text)
        if key:
            st["pin_key"] = key.group(1).replace("\\u002F", "/").replace("\\/", "/")
        st["config_at"] = time.time()
        st.save()

    def _const(self, key):
        return self._state.get("consts", DEFAULT_CONSTANTS).get(key) or DEFAULT_CONSTANTS[key]

    def _headers(self, flow, step, token, account):
        st = self._state
        device_id, session_id = st["device_id"], st["session_id"]
        # Lazy imports (also uuid, base64 elsewhere): menus that only call has_login skip them.
        import hashlib
        import uuid

        tracking_id = str(uuid.uuid4())
        call_time = str(int(time.time() * 1000))
        h = {
            "Accept": "application/json, text/plain, */*",
            "Origin": BASE_URL,
            "Referer": BASE_URL + "/",
            "app_key": self._const("CMS_CONFIGURATION_API_KEY"),
            "app_version": self._const("APP_VERSION"),
            "Device-Id": device_id,
            "Device-Name": DEVICE_NAME,
            "Device-Density": "xhdpi",
            "tenant": "tv",
            "X-User-Agent": "web|web|%s-%s|%s|1" % (BROWSER, BROWSER_VERSION, self._const("APP_VERSION")),
            "X-Call-Type": "AUTH_USER" if token else "GUEST_USER",
            "x-tv-flow": flow,
            "x-request-session-id": session_id,
            "x-request-tracking-id": tracking_id,
            "x-call-time": call_time,
            "x-txn-id": hashlib.sha256((tracking_id + session_id + device_id + call_time).encode()).hexdigest()[:32],
            "Pragma": "akamai-x-cache-on,akamai-x-check-cacheable,akamai-x-get-cache-key",
        }
        if step:
            h["x-tv-step"] = step
        if token:
            h["bff_token"] = token
            if account:
                h["X-Channel-Map-Id"] = str(account.get("channelMap_id", ""))
                h["x-user-id"] = str(account.get("user_id", ""))
                h["x-account-details"] = account_details(account)
        return h

    def send(self, path, flow, step=None, params=None, method="GET", body=None, token=None, account=None):
        """Make a bifrost request and return its response, whatever its status (see answer).

        :param token: the access token of a call with the login; None for a guest call
        :param account: the account (see Auth.account) whose headers a call with the login carries
        """
        self.bootstrap()
        query = {"natco_key": self._const("NATCO_KEY"), "app_language": LANGUAGE, "natco_code": NATCO}
        query.update(params or {})
        url = self._const("BFF_BASE_URL") + path
        headers = self._headers(flow, step, token, account)
        return self.http.request(method, url, params=query, json=body, headers=headers, timeout=TIMEOUT)

    def call(self, path, flow, step=None, params=None, method="GET", body=None):
        """Make a guest bifrost call (no login) and return its JSON answer (see answer)."""
        return answer(self.send(path, flow, step, params, method, body), method, path)


def answer(r, method, path):
    """Return a bifrost response's JSON ({} if empty).

    :raises errors.ApiError: an error status (its `status` set), or not JSON
    """
    if not r.ok:
        e = errors.ApiError("%s %s -> HTTP %s: %s" % (method, path, r.status_code, r.text[:300]))
        e.status = r.status_code
        raise e
    try:
        return r.json() if r.content else {}
    except ValueError:
        raise errors.ApiError("%s %s -> HTTP %s, not JSON: %s" % (method, path, r.status_code, r.text[:300])) from None


def account_details(acc):
    """Return the x-account-details header: the shape the web client builds from /user/account."""
    details = {
        "accountType": acc.get("account_type"),
        "userId": acc.get("user_id"),
        "recordingEnabledDVR": acc.get("is_recording_enabled"),
        "channelMapId": acc.get("channelMap_id"),
        "rightsGroupIds": acc.get("rightsGroup_ids"),
        "releaseSlot": acc.get("release_slot"),
        "accountId": acc.get("account_id"),
    }
    vod = (acc.get("managed_settings") or {}).get("TVSOA-setting-VodEnabled")
    if vod:
        details["vodEnabled"] = vod
    return json.dumps(details, separators=(",", ":"))


def _app_constants(page):
    """Return the startup page's window.APP_CONSTANTS we use, DEFAULT_CONSTANTS where it has none."""
    consts = dict(DEFAULT_CONSTANTS)
    m = re.search(r"window\.APP_CONSTANTS\s*=\s*(\{.*?\})\s*</script>", page, re.S)
    if m:
        with contextlib.suppress(ValueError):
            live = json.loads(m.group(1))
            consts.update({k: live[k] for k in DEFAULT_CONSTANTS if live.get(k)})
    return consts
