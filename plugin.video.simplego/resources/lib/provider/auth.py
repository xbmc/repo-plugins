"""The login: refresh token, STS access token, the account and its devices, and calls made with them."""

import contextlib
import time
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import urljoin
from urllib.parse import urlsplit

from resources.lib.provider import core
from resources.lib.provider import errors

# What a logout keeps: the device's identity and the startup page's constants, for the next login.
LOGOUT_KEEPS = ("device_id", "device_uuid", "session_id", "consts", "config_at")
# How long an access token is taken to last when the STS does not say (seconds).
DEFAULT_TOKEN_LIFETIME = 3600


class Auth:
    """The login and the account; every call that needs them goes through call().

    :param state: the client's statefile.State
    :param api: the client's core.Api
    """

    def __init__(self, state, api):
        self._state = state
        self._api = api
        # Guest mode: the public channel list and guide, used when the login is missing or refused.
        self.guest = False
        self._readd_listeners = []

    def is_logged_in(self):
        """Return whether there is a refresh token, even in guest mode."""
        return bool(self._state.get("refresh_token"))

    def login_expires(self):
        """Return the refresh token's expiry (Unix time); None if not known."""
        return core.token_expiry(self._state.get("refresh_token"))

    @property
    def authed(self):
        """Return whether channel list and guide come from the account rather than the public ones."""
        return self.is_logged_in() and not self.guest

    @property
    def device_id(self):
        """Return this device's ID with the provider."""
        return self._state.get("device_id")

    def on_device_readded(self, forget):
        """Have forget() called when this device is attached to the account again: what was the old device's is void."""
        self._readd_listeners.append(forget)

    # ------------------------------------------------------------- calls

    def call(self, path, flow, step=None, params=None, method="GET", body=None, readd=True):
        """Make a bifrost call with the login and return its JSON answer.

        A refused token is renewed and a removed device attached again, once each, then the call repeated.

        :param readd: False does not attach a removed device again (the call that does it, a removal)
        :raises errors.AuthError: the login is refused even so
        """
        for attempt in (0, 1):
            account = self._state.get("account")
            r = self._api.send(path, flow, step, params, method, body, token=self.valid_access_token(), account=account)
            if r.status_code != 401 or attempt:
                break
            if "device was removed" not in r.text:
                self._renew()
            elif readd:
                self.readd_device()
            else:
                break
        if r.status_code == 401:
            raise errors.AuthError("bifrost rejected the access token")
        return core.answer(r, method, path)

    def call_as_account(self, path, flow, step=None, params=None):
        """Make a GET with the login when logged in, else a guest one (the public answer)."""
        if self.authed:
            return self.call(path, flow, step, params)
        return self._api.call(path, flow, step, params)

    # ------------------------------------------------------------- login

    def login_with_refresh_token(self, text):
        """Log in with the refresh token found in text (the address the phone sent).

        :raises errors.AuthError: no refresh token in the text, or the provider refused it
        """
        token = core.extract_refresh_token(text)
        if not token:
            raise errors.AuthError("No refresh token found in the given text")
        self._state["refresh_token"] = token
        self._state.pop("access_token", None)
        self._state.pop("account", None)
        try:
            self._renew()
            self.valid_account(force=True, fresh_login=True)
        except errors.AuthError:
            # Only a refused token is dropped: after a network failure it may already
            # have been rotated, and the new one is the only one that still works.
            self._state.pop("refresh_token", None)
            self._state.save()
            raise

    def logout(self):
        """Forget the login and free this device's slot; keep the identity for the next login."""
        if self._state.get("refresh_token"):
            # Logging out must work offline or with an already removed device too.
            with contextlib.suppress(errors.ApiError, KeyError):
                self.remove_device(self._state["device_id"])
        self._state.keep_only(LOGOUT_KEEPS)

    def _renew(self):
        """Trade the Keycloak refresh token for a new STS access token.

        The STS answers refresh_login_url with redirects ending at redirect_uri,
        the tokens in its query or fragment.
        """
        st = self._state
        if not st.get("refresh_token"):
            raise errors.AuthError("Not logged in")
        self._api.bootstrap()
        tpl = self._tenant_config().get("refresh_login_url", "")
        if not tpl:
            raise errors.ApiError("tenant config has no refresh_login_url")
        slot = (st.get("account") or {}).get("sts_slot") or st.get("sts_slot") or core.DEFAULT_STS_SLOT
        url = (
            tpl.replace("&amp;", "&")
            .replace("sts_slot", slot)
            .replace("${refreshToken}", st["refresh_token"])
            .replace("${redirectUri}", quote(core.SSO_REDIRECT_URI, safe=""))
        )
        tokens, url, r = self._follow_to_tokens(url)
        if not tokens:
            # Keycloak rotates refresh tokens; one already used elsewhere (the source
            # browser, another install) makes the STS fall back to the SSO login page.
            raise errors.AuthError(
                "STS rejected the refresh token (ended at %s, HTTP %s); "
                "it was probably already used or revoked" % (urlsplit(url).netloc, r.status_code)
            )
        st["access_token"] = tokens["access_token"]
        st["refresh_token"] = tokens.get("refresh_token") or st["refresh_token"]
        st["access_expires"] = time.time() + int(tokens.get("expires_in") or DEFAULT_TOKEN_LIFETIME)
        st["sts_slot"] = slot
        st.save()

    def _follow_to_tokens(self, url):
        """Follow the STS's redirects; return (the tokens or None, the last address, the last response)."""
        # Here, not at module level: transport loads http.client and ssl, which menus skip (see core.Api.http).
        from resources.lib.net import transport

        for _ in range(transport.MAX_REDIRECTS):
            r = self._api.http.get(url, allow_redirects=False, timeout=core.TIMEOUT)
            loc = r.headers.get("Location")
            if not loc:
                break
            url = urljoin(url, loc)
            parts = urlsplit(url)
            q = parse_qs(parts.query)
            q.update(parse_qs(parts.fragment))
            if "access_token" in q:
                return {k: v[0] for k, v in q.items()}, url, r
        return None, url, r

    def login_url(self):
        """Return the SSO login address for the phone login (see core.PHONE_REDIRECT_URI)."""
        self._api.bootstrap()
        tpl = self._tenant_config()["login_url"].replace("&amp;", "&")
        return tpl.replace("${redirectUri}", quote(core.PHONE_REDIRECT_URI, safe=""))

    def _tenant_config(self):
        st = self._state
        if not st.get("tenant_config") or st.get("tenant_config_at", 0) + core.CONFIG_TTL < time.time():
            st["tenant_config"] = self._api.call("/tenant/config", "START_UP", "CONFIG", params={"is_sso_enabled": "true"})
            st["tenant_config_at"] = time.time()
        return st["tenant_config"]

    def valid_access_token(self, ahead=core.TOKEN_SKEW):
        """Return the access token, renewed first if it runs out within `ahead` seconds."""
        st = self._state

        def expired():
            return not st.get("access_token") or st.get("access_expires", 0) - ahead < time.time()

        if expired():
            # One renewal at a time across interpreters, and none if another client renewed
            # meanwhile: the rotated-out refresh token would fail.
            with st.lock():
                st.save()
                if expired():
                    self._renew()
        return st["access_token"]

    # ------------------------------------------------------------- account

    def valid_account(self, force=False, fresh_login=False):
        """Return the account, refetched if forced or older than core.ACCOUNT_TTL."""
        st = self._state
        if force or not st.get("account") or st.get("account_at", 0) + core.ACCOUNT_TTL < time.time():
            # Dropped first so the call does not send stale account headers.
            st.pop("account", None)
            # fresh_login=true (re)adds this device to the account; with false a removed
            # device only gets 401 "This device was removed".
            st["account"] = self.call(
                "/user/account",
                "START_UP",
                "GET_USER_ACCOUNT",
                params={"fresh_login": "true" if fresh_login else "false"},
                readd=not fresh_login,
            )
            st["account_at"] = time.time()
            st.save()
        return st["account"]

    def channel_map(self):
        """Return the account's channel map id ("" if it has none)."""
        return self.valid_account().get("channelMap_id", "")

    def readd_device(self):
        """Re-attach this device after the backend dropped it from the account."""
        self.valid_account(force=True, fresh_login=True)
        for forget in self._readd_listeners:
            forget()
        self._state.save()

    def devices(self):
        """Return the account's devices (unfiltered)."""
        data = self.call("/setting/devices", "DEVICE_SETTINGS", "GET_DEVICES", params={"filter_enabled": "false"})
        return data.get("devices") or []

    def remove_device(self, device_id):
        """Take a device off the account."""
        path = "/setting/devices/%s" % quote(device_id, safe="")
        self.call(path, "DEVICE_SETTINGS", "REMOVE_DEVICE", method="DELETE", readd=False)
