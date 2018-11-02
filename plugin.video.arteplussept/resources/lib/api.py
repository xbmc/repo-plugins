from collections import OrderedDict
import requests

from addon import PluginInformation

_base_api_url = 'http://www.arte.tv/hbbtvv2/services/web/index.php'
_base_headers = {
    'user-agent': PluginInformation.name + '/' + PluginInformation.version
}
_endpoints = {
    'categories': '/EMAC/teasers/categories/v2/{lang}',
    'category': '/EMAC/teasers/category/v2/{category_code}/{lang}',
    'subcategory': '/OPA/v3/videos/subcategory/{sub_category_code}/page/1/limit/100/{lang}',
    'magazines': '/OPA/v3/magazines/{lang}',
    'collection': '/OPA/v3/videos/collection/{kind}/{collection_id}/{lang}',
    'streams': '/OPA/v3/streams/{program_id}/{kind}/{lang}',


    'daily': '/OPA/v3/programs/{date}/{lang}'
}


def categories(lang):
    url = _endpoints['categories'].format(lang=lang)
    return _load_json(url).get('categories', {})


def magazines(lang):
    url = _endpoints['magazines'].format(lang=lang)
    return _load_json(url).get('magazines', {})


def category(category_code, lang):
    url = _endpoints['category'].format(category_code=category_code, lang=lang)
    return _load_json(url).get('category', {})


def subcategory(sub_category_code, lang):
    url = _endpoints['subcategory'].format(
        sub_category_code=sub_category_code, lang=lang)
    return _load_json(url).get('videos', {})


def collection(kind, collection_id, lang):
    url = _endpoints['collection'].format(kind=kind,
                                          collection_id=collection_id, lang=lang)
    return _load_json(url).get('videos', [])


def streams(kind, program_id, lang):
    url = _endpoints['streams'] .format(
        kind=kind, program_id=program_id, lang=lang)
    return _load_json(url).get('videoStreams', [])


def daily(date, lang):
    url = _endpoints['daily'].format(date=date, lang=lang)
    return _load_json(url).get('programs', [])


def _load_json(url, params=None, headers=_base_headers):
    r = requests.get(_base_api_url + url, params=params, headers=headers)
    return r.json(object_pairs_hook=OrderedDict)
