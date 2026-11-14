"""The TV provider's client: what its web player does, without Kodi.

The web player (see core.BASE_URL) runs on a "yo-digital" OneTV front end, with
a MediaKind (tv3cloud) back end behind it:

  * bifrost (tv-hu-prod.yo-digital.com/bifrost): channel list, EPG, account.
    Every call carries x-txn-id = sha256(trackingId+sessionId+deviceId+callTime)[:32].
  * MediaKind STS (ottapp-appgw-client-a...): issues the "AuthToken1..." access
    token. The SSO login (Keycloak, with reCAPTCHA) rules out password login, so the
    add-on takes the 365-day refresh token from one browser login and renews through
    the STS refresh_login_url redirect.
  * MediaKind AMP (ottapp-appgw-amp-a...): device registration, "roll" (the
    playback session: manifest + CDN) and the Widevine licence.
"""

import importlib

from resources.lib.provider import core
from resources.lib.provider import errors

# Re-exported for short: what the add-on's other parts use.
ApiError = errors.ApiError
has_login = core.has_login
AuthError = errors.AuthError
LicenceRefusedError = errors.LicenceRefusedError
ParentalLockError = errors.ParentalLockError
CancelledError = errors.CancelledError
USER_AGENT = core.USER_AGENT

__all__ = ["Client"]


def __getattr__(name):
    """Return the client class or a submodule, imported at first use.

    Menus that only call has_login then load just core; the whole client dominated
    their start-up on a TV stick.
    """
    if name == "Client":
        from resources.lib.provider.client import Client

        globals()["Client"] = Client
        return Client
    try:
        return importlib.import_module("%s.%s" % (__name__, name))
    except ModuleNotFoundError:
        raise AttributeError(name) from None
