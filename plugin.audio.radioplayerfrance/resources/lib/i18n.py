# i18n.py
import xbmcaddon
from resources.lib.strings_map import STRINGS

_addon = xbmcaddon.Addon()

def _(text: str) -> str:
    """
    Translate an English string into the user's language.
    Fallbacks:
      - if text not in STRINGS → return original English string
      - if translation missing → fall back to English (Kodi native behavior)
    """
    string_id = STRINGS.get(text)
    if not string_id:
        return text  # English fallback

    return _addon.getLocalizedString(string_id)
