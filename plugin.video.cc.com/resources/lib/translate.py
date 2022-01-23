from resources.lib.addonutils import LANGUAGE
from resources.lib.addonutils import log

T_MAP = {
    'shows': 32001,
    'full.episodes': 32002,
    'standup': 32003,
    'digital.original': 32004,
    'load.more': 32005,
    'error.openurl': 33001,
    'error.no.json': 33002,
    'error.no.video': 33003,
    'error.generic': 33004,
    'error.wrong.type': 33005,
}


def translatedString(id):
    t_string = T_MAP.get(id)
    if t_string:
        return LANGUAGE(t_string)
    log(f"{id} translation ID not found.", 3)
    return 'NO TRANSLATION AVAILABLE'
