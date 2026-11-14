"""The TV provider's client, without Kodi.

* bifrost (see core.DEFAULT_CONSTANTS): channel list, EPG, account.
* STS: the access token, renewed from the login's refresh token.
* AMP: device registration, "roll" (the playback session: manifest and CDN) and the Widevine licence.
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
