import player_config
import util


def get_channel_list(include_premium):
    networks = player_config.get_networks()
    network_ids = []
    for network in networks:
        network_name = network.get('name')
        if include_premium or network_name == 'espn3' or network_name == 'accextra':
            network_ids.append(network_name)
    return network_ids


def get_live_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_live_event_url() + '&channel=' + query_params


def get_upcoming_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_upcoming_event_url() + '&channel=' + query_params


def get_replay_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_replay_event_url() + '&channel=' + query_params


def get_live_events(network_names=None):
    if network_names is None:
        network_names = []
    et = util.get_url_as_xml_cache(player_config.get_live_event_url(), encoding='ISO-8859-1')
    return et.findall('.//event')


def get_events(url):
    et = util.get_url_as_xml_cache(url, encoding='ISO-8859-1')
    return et.findall('.//event')
