from __future__ import (absolute_import, unicode_literals)
from builtins import str
from kodi_six import xbmc
from . import api_keys, url

API_BASE_URL = api_keys.NHK_API_BASE_URL
NHK_BASE_URL = api_keys.NHK_BASE_URL
API_LANGUAGE = 'en'
API = {}


def create_command(prefix, resource):
    return ('{0}_{1}'.format(prefix, resource))


def get_API_from_NHK():
    xbmc.log("nhk_api_parser.py: Getting API from NHK")
    raw_API_json = url.get_json(
        'https://www3.nhk.or.jp/nhkworld/assets/api_sdk/api.json')
    nhk_api = {}
    for row in raw_API_json['api']:
        prefix = row['prefix']
        version = row['version']
        for resource in row['resources']:
            command = create_command(prefix, resource)
            params = row['resources'][resource]
            nhk_api.update({command: {'version': version, 'params': params}})

    return (nhk_api)


def get_location_params_values(locationParams):
    """ Get a parameter dictionary from the location params node """
    values = {}
    for row in locationParams:
        if ('default' in row):
            key = row['paramName']
            values[key] = row['default']
    return (values)


def get_full_API_url(path):
    return (API_BASE_URL + path)


def get_full_NHK_url(path):
    return (NHK_BASE_URL + path)


def replace_path_parameters_version_language(path, version, language):
    path = path.replace('{version}', version)
    path = path.replace('{lang}', language)
    return (path)


def get_homepage_ondemand_url():
    command = create_command('vod', 'RecommendListFetch')
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = get_full_API_url(path)
    return (path)


def get_homepage_news_url():
    command = create_command('news', 'ListFetch')
    params = API[command]['params']
    path = str(params['path'])
    path = get_full_NHK_url(path)
    return (path)


def get_livestream_url():
    command = create_command('tv', 'EPGFetch')
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = path.replace('{version}', version)
    path = path.replace('{region}', 'world')
    path = path.replace('{Time}', 'now')
    path = get_full_API_url(path)
    return (path)


def get_programs_url():
    command = create_command('vod', 'ProgramListFetch')
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{l_mode}', 'voice')
    path = get_full_API_url(path)
    return (path)


# "episode by program id"
def get_programs_episode_list_url():
    command = create_command('vod', 'EpisodeByProgramListFetch')
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{l_mode}', 'all')
    path = path.replace('pgm_gr_id', '0')
    path = get_full_API_url(path)
    return (path)


#  "category list"
def get_categories_url():
    command = create_command('vod', 'CategoryListFetch')
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{mode}', 'all')
    path = path.replace('{content_type}', 'ondemand')
    path = get_full_API_url(path)
    return (path)


#  "episode list by category."
def get_categories_episode_list_url():
    command = create_command('vod', 'EpisodeByCategoryListFetch')
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{l_mode}', 'all')
    path = path.replace('Id', '0')
    path = get_full_API_url(path)
    return (path)


# "vod play list
def get_playlists_url():
    command = create_command('vod', 'PlayListFetch')
    params = API[command]['params']
    locationParams = get_location_params_values(params['locationParams'])
    mode = str(locationParams['mode'])
    version = str(locationParams['version'])
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{playlist_id}', 'all')
    path = path.replace('{mode}', mode)
    path = get_full_API_url(path)
    return (path)


# "vod play list by playlist Id"
def get_playlists_episode_list_url():
    command = create_command('vod', 'PlayListFetch')
    params = API[command]['params']
    path = str(params['path'])
    locationParams = get_location_params_values(params['locationParams'])
    mode = str(locationParams['mode'])
    version = str(locationParams['version'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{playlist_id}', '{0}')
    path = path.replace('{mode}', mode)
    path = get_full_API_url(path)
    return (path)


# All episodes (can limit to latest since this list is ordered by date)
def get_all_episodes_url(limit):
    command = create_command('vod', 'EpisodeListFetch')
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{mode}', 'all')
    path = path.replace('{key}', 'all')
    path = path.replace('{l_mode}', 'all')
    path = path.replace('{limit}', limit)
    path = get_full_API_url(path)
    return (path)


# Most watched episodes
def get_most_watched_episodes_url():
    command = create_command('vod', 'EpisodeByMostWatchedListFetch')
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{l_mode}', 'all')
    path = get_full_API_url(path)
    return (path)


# All episodes (can limit to latest since this list is ordered by date)
def get_episode_detail_url():
    command = create_command('vod', 'EpisodeListFetch')
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace('{mode}', 'vod_id')
    path = path.replace('{key}', '{0}')
    path = path.replace('{l_mode}', 'all')
    path = path.replace('{limit}', '1')
    path = get_full_API_url(path)
    return (path)


API = get_API_from_NHK()
