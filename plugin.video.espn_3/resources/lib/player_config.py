import os
import base64

import util
from globals import ADDON_PATH_PROFILE

# 1 hour
TIME_DIFFERENCE = 60 * 60

PLAYER_CONFIG_FILE = 'player_config.xml'
PLAYER_CONFIG_FILE = os.path.join(ADDON_PATH_PROFILE, PLAYER_CONFIG_FILE)
PLAYER_CONFIG_URL = base64.b64decode('aHR0cHM6Ly9lc3BuLmdvLmNvbS93YXRjaGVzcG4vcGxheWVyL2NvbmZpZw==')

USER_DATA_FILE = 'user_data.json'
USER_DATA_FILE = os.path.join(ADDON_PATH_PROFILE, USER_DATA_FILE)
USER_DATA_URL = base64.b64decode(
    'aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi91c2VyRGF0YT9mb3JtYXQ9anNvbg==')

PROVIDERS_FILE = 'providers.xml'
PROVIDERS_FILE = os.path.join(ADDON_PATH_PROFILE, PROVIDERS_FILE)

CHECK_RIGHTS_URL = base64.b64decode('aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL2VzcG5uZXR3b3Jrcy91c2Vy')


def get_config_soup():
    return util.get_url_as_xml_soup_cache(PLAYER_CONFIG_URL, PLAYER_CONFIG_FILE, TIME_DIFFERENCE)


def get_user_data():
    return util.get_url_as_json_cache(USER_DATA_URL, USER_DATA_FILE, TIME_DIFFERENCE)


def can_access_free_content():
    return get_user_data()['affvalid'] == 'true'


def get_timezone():
    return get_user_data()['timezone']


def get_dma():
    return get_user_data()['dma']


def get_can_sso():
    return get_user_data()['canaddsso']


def get_sso_abuse():
    return get_user_data()['ssoabuse']


def get_networks():
    networks = get_config_soup().findall('.//network')
    return networks


# Handle elementtree 1.2.8 which doesn't support [@ xpath notation
def select_feed_by_id(feed_id):
    try:
        return get_config_soup().find('.//feed[@id=\'' + feed_id + '\']').text
    except:
        feeds = get_config_soup().findall('.//feed')
        for feed in feeds:
            if feed.get('id') == feed_id:
                return feed.text
    return None


def get_live_event_url():
    return select_feed_by_id('liveEvent')


def get_replay_event_url():
    return select_feed_by_id('replayEvent')


def get_upcoming_event_url():
    return select_feed_by_id('upcomingEvent')


def get_network_name(network_id):
    network = get_network(network_id)
    if network is None:
        return 'Unknown network %s' % network_id
    else:
        return network.get('name')


def get_network(network_id):
    networks = get_networks()
    for network in networks:
        if network.get('id') == network_id:
            return network
    return None
