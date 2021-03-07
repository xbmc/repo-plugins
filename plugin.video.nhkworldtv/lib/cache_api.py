from __future__ import (absolute_import, unicode_literals)
from kodi_six import xbmc
from . import api_keys, url
# Cache backend (Azure Functions) API

rest_url = {
    'cache_get_program_list':
    api_keys.CACHE_API_BASE_URL + '/Program/v2/List/{0}',
}

base_url = "https://nhkw-mzvod.akamaized.net/www60/mz-nhk10/_definst_/mp4:mm/flvmedia/5905"


def get_program_metdadata_cache(max_items):
    """Use NHK World TV Cloud Service to speed-up episode URLlookup.
    The service runs on Azure in West Europe but should still speed up
    the lookup process dramatically since it uses a pre-loaded cache

    Arguments:
        max_items {int} -- Amount of items to retrieve

    Returns:
        {dict} -- A JSON dict with the cache items
    """
    cache = url.get_json(rest_url['cache_get_program_list'].format(max_items))
    xbmc.log(
        "cache_api.get_program_metdadata_cache: Got {0} episodes from Azure".
        format(len(cache)))
    return (cache)
