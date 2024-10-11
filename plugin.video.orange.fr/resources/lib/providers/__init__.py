"""List all available providers and return the provider selected by the user."""

import xbmc

from lib.utils.kodi import get_addon_setting, log

from .abstract_provider import AbstractProvider
from .fr import OrangeCaraibeProvider, OrangeFranceProvider, OrangeReunionProvider

_PROVIDERS = {
    "France.Orange": OrangeFranceProvider,
    "France.Orange Caraïbe": OrangeCaraibeProvider,
    "France.Orange Réunion": OrangeReunionProvider,
}

_PROVIDER_NAME = get_addon_setting("provider.name")
_PROVIDER_COUNTRY = get_addon_setting("provider.country")
_PROVIDER_KEY = f"{_PROVIDER_COUNTRY}.{_PROVIDER_NAME}"

_PROVIDER = _PROVIDERS[_PROVIDER_KEY]() if _PROVIDERS.get(_PROVIDER_KEY) is not None else None

if not _PROVIDER:
    log(f"Cannot instanciate provider: {_PROVIDER_KEY}", xbmc.LOGERROR)


def get_provider() -> AbstractProvider:
    """Return the selected provider."""
    return _PROVIDER
