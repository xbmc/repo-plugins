# http://docs.python-requests.org/en/latest/
import requests

BASQUE_ONLINE_RADIOS_URL = 'https://raw.githubusercontent.com/aldatsa/plugin.audio.euskarazko-irratiak/master/streams/streams.json'

def get_streams():
    """
    Get the list of audio/streams.

    :param url: str
    :return: list
    """

    data = requests.get(BASQUE_ONLINE_RADIOS_URL)
    return data.json().get('streams')
