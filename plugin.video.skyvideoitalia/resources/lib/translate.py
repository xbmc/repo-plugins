from resources.lib.addonutils import LANGUAGE
from resources.lib.addonutils import log

T_MAP = {
    'dirette.title': 32001,
    'playlist.title': 32002,
    'error.openurl': 33000,
    'error.json': 33001,
    'error.json.decode': 33002,
    'media.not.found': 33003,
    'live.not.found': 33004,
}


def translatedString(id):
    t_string = T_MAP.get(id)
    if t_string:
        return LANGUAGE(t_string)
    log(f"{id} translation ID not found.", 3)
    return 'NO TRANSLATION AVAILABLE'
