"""
NHK Cache API - gets episode VOD information from the companion Azure service
"""
import xbmc

from . import api_keys, url

# Cache backend (Azure Functions) API

REST_URL = {
    'cache_get_program_list':
    api_keys.CACHE_API_BASE_URL + '/Program/v2/List/{0}',
}

BASE_URL = "https://nhkw-mzvod.akamaized.net/www60/mz-nhk10/_definst_/mp4:mm/flvmedia/5905"


def get_program_metdadata_cache(max_items):
    """Use NHK World TV Cloud Service to speed-up episode URLlookup.
    The service runs on Azure in West Europe but should still speed up
    the lookup process dramatically since it uses a pre-loaded cache

    Arguments:
        max_items {int} -- Amount of items to retrieve

    Returns:
        {dict} -- A JSON dict with the cache items
    """
    cache = url.get_json(REST_URL['cache_get_program_list'].format(max_items))
    xbmc.log(
        f"cache_api.get_program_metdadata_cache: Got {len(cache)} episodes from Azure"
    )
    return cache
