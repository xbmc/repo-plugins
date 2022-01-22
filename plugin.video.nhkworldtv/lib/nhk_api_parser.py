"""
Dynamic NHK API Parser
"""

from builtins import str

import xbmc

from . import api_keys, url

API_BASE_URL = api_keys.NHK_API_BASE_URL
NHK_BASE_URL = api_keys.NHK_BASE_URL
API_LANGUAGE = "en"
API = {}

L_MODE = "{l_mode}"
MODE = "{mode}"


def create_command(prefix, resource):
    """
    Generates an API command
    """
    return f"{prefix}_{resource}"


def get_api_from_nhk():
    """
    Retrieves and parses the base API from NHK
    """
    xbmc.log("nhk_api_parser.py: Getting API from NHK")
    raw_api_json = url.get_json(
        "https://www3.nhk.or.jp/nhkworld/assets/api_sdk/api.json")
    nhk_api = {}
    for row in raw_api_json['api']:
        prefix = row['prefix']
        version = row['version']
        for resource in row['resources']:
            command = create_command(prefix, resource)
            params = row['resources'][resource]
            nhk_api.update({command: {'version': version, 'params': params}})

    return nhk_api


def get_location_params_values(location_params):
    """ Get a parameter dictionary from the location params node """
    values = {}
    for row in location_params:
        if "default" in row:
            key = row['paramName']
            values[key] = row['default']
    return values


def get_full_api_url(path):
    """
    Returns the full API url
    """
    return API_BASE_URL + path


def get_full_nhk_url(path):
    """
    Returns the full NHK url
    """
    return NHK_BASE_URL + path


def replace_path_parameters_version_language(path, version, language):
    """
    Replaces parametes in the path with the actual values
    """
    path = path.replace("{version}", version)
    path = path.replace("{lang}", language)
    return path


def get_homepage_ondemand_url():
    """
    Returns the url for the on-demand homepage content
    """
    command = create_command("vod", "RecommendListFetch")
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = get_full_api_url(path)
    return path


def get_homepage_news_url():
    """
    Returns the url for the News programs homepage content
    """
    command = create_command("news", "ListFetch")
    params = API[command]['params']
    path = str(params['path'])
    path = get_full_nhk_url(path)
    return path


def get_livestream_url():
    """
    Returns the live stream url
    """
    command = create_command("tv", "EPGFetch")
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = path.replace("{version}", version)
    path = path.replace("{region}", "world")
    path = path.replace("{Time}", "now")
    path = get_full_api_url(path)
    return path


def get_programs_url():
    """
    Returns the program url
    """
    command = create_command("vod", "ProgramListFetch")
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(L_MODE, "voice")
    path = get_full_api_url(path)
    return path


def get_programs_episode_list_url():
    """
    Gets the episodes list for a program url
    """
    command = create_command("vod", "EpisodeByProgramListFetch")
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(L_MODE, "all")
    path = path.replace("pgm_gr_id", "0")
    path = get_full_api_url(path)
    return path


def get_categories_url():
    """
    Gets the category list url
    """
    command = create_command("vod", "CategoryListFetch")
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(MODE, "all")
    path = path.replace("{content_type}", "ondemand")
    path = get_full_api_url(path)
    return path


def get_categories_episode_list_url():
    """
    Gets the episode list by category url
    """
    command = create_command("vod", "EpisodeByCategoryListFetch")
    params = API[command]['params']
    version = API[command]['version']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(L_MODE, "all")
    path = path.replace("Id", "0")
    path = get_full_api_url(path)
    return path


def get_playlists_url():
    """
    Gets the vod play list url
    """
    command = create_command("vod", "PlayListFetch")
    params = API[command]['params']
    location_params = get_location_params_values(params['locationParams'])
    mode = str(location_params['mode'])
    version = str(location_params['version'])
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace("{playlist_id}", "all")
    path = path.replace(MODE, mode)
    path = get_full_api_url(path)
    return path


def get_playlists_episode_list_url():
    """
    Gets vod play list by playlist Id url
    """
    command = create_command("vod", "PlayListFetch")
    params = API[command]['params']
    path = str(params['path'])
    location_params = get_location_params_values(params['locationParams'])
    mode = str(location_params['mode'])
    version = str(location_params['version'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace("{playlist_id}", "{0}")
    path = path.replace(MODE, mode)
    path = get_full_api_url(path)
    return path


def get_all_episodes_url(limit):
    """
    All episodes (can limit to latest since this list is ordered by date)
    """
    command = create_command("vod", "EpisodeListFetch")
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(MODE, "all")
    path = path.replace("{key}", "all")
    path = path.replace(L_MODE, "all")
    path = path.replace("{limit}", limit)
    path = get_full_api_url(path)
    return path


def get_most_watched_episodes_url():
    """
    Most watched episodes
    """
    command = create_command("vod", "EpisodeByMostWatchedListFetch")
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(L_MODE, "all")
    path = get_full_api_url(path)
    return path


def get_episode_detail_url():
    """
    All episodes (can limit to latest since this list is ordered by date)
    """
    command = create_command("vod", "EpisodeListFetch")
    version = API[command]['version']
    params = API[command]['params']
    path = str(params['path'])
    path = replace_path_parameters_version_language(path, version,
                                                    API_LANGUAGE)
    path = path.replace(MODE, "vod_id")
    path = path.replace("{key}", "{0}")
    path = path.replace(L_MODE, "all")
    path = path.replace('{limit}', "1")
    path = get_full_api_url(path)
    return path


# Parse the API
API = get_api_from_nhk()
