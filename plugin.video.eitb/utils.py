import requests

API_URL = "https://eitbapi.erral.workers.dev"
TV_PROGRAM_LIST = "{0}/tv/programs".format(API_URL)

# a = '%s' % 'Zital'
# b = '{0}'.format('Zital')
# c = '{1} - {0}'.format('erral', 'zital')
# d = '{name} - {surname}'.format(name='erral', surname='zital')
# name = "erral"
# surname = 'zital'
# e = f'{name} - {surname}'
# f = `${name} ${surname}`

VIDEO_PLAYLIST_URL = "{0}/playlist".format(API_URL)
LAST_BROADCAST_VIDEO_PLAYLIST_URL = "{0}/last-broadcast-list".format(API_URL)
RADIO_STATION_LIST = "{0}/radios".format(API_URL)
RADIO_PLAYLIST_URL = "{0}/radio".format(API_URL)
PROGRAM_TYPES_URL = "{0}/tv".format(API_URL)
PROGRAM_TYPES_PLAYLIST_URL = "{0}/type-playlist".format(API_URL)


def get_programs():
    data = requests.get(TV_PROGRAM_LIST)
    return data.json().get("member")


def get_programs_types():
    data = requests.get(PROGRAM_TYPES_URL)
    return data.json().get("member")


def get_programs_types_playlist(url):
    data = requests.get(url)
    return data.json().get("member")


def get_last_broadcast(items):
    data = requests.get(
        "{0}?items={1}".format(LAST_BROADCAST_VIDEO_PLAYLIST_URL, items)
    )
    return data.json().get("member")


def get_episodes(url):
    data = requests.get(url)
    return data.json().get("member")


def get_videos(url):
    data = requests.get(url)
    return data.json()


def get_playlists(url):
    data = requests.get(url)
    return data.json().get("member", [])


def get_radios():
    data = requests.get(RADIO_STATION_LIST)
    return data.json().get("member", [])


def get_radio_programs(url):
    data = requests.get(url)
    return data.json().get("member")


def get_program_audios(url):
    data = requests.get(url)
    return data.json()


def get_program_seasons(url):
    data = requests.get(url)
    return data.json().get("member")


def get_program_season_chapters(url):
    data = requests.get(url)
    return data.json().get("member")


import xbmcaddon
import xbmc


def get_local_string(string):

    """Get add-on string. Returns in unicode."""
    # if type(string) != int:
    #     string = STRINGS[string]

    result = xbmcaddon.Addon("plugin.video.eitb").getLocalizedString(string)

    # Plugin-aren itzulpena ez bada, kodi sistemakoa lortu
    if not result:
        result = xbmc.getLocalizedString(string)

    return result
