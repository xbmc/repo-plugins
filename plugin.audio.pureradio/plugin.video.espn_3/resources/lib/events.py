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
    soup = util.get_url_as_xml_soup_cache(player_config.get_live_event_url())
    return soup.findall('.//event')


def get_events(url):
    soup = util.get_url_as_xml_soup_cache(url)
    return soup.findall('.//event')
