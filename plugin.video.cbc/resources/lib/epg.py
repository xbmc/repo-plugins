"""Electronic program guide module."""
from datetime import datetime, timedelta
from concurrent import futures

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

from resources.lib.utils import log
from resources.lib.cbc import CBC
from resources.lib.livechannels import LiveChannels

# Y/M/D
GUIDE_URL_FMT = 'https://www.cbc.ca/programguide/daily/{}/cbc_television'
NEWSNET_URL_FMT = 'https://www.cbc.ca/programguide/daily/{}/cbc_news_network'


def get_iptv_epg():
    """Get the EPG Data."""
    live = LiveChannels()
    channels = live.get_live_channels()
    blocked = live.get_blocked_iptv_channels()
    unblocked = []
    for channel in channels:
        callsign = CBC.get_callsign(channel)
        if callsign not in blocked:
            unblocked.append(channel)
    channel_map = map_channel_ids(unblocked)
    epg_data = {}

    future_to_callsign = {}
    log('Starting EPG update')
    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        for callsign, guide_id in channel_map.items():

            # determine if we're dealing with news network
            newsnetwork = callsign == 'NN'

            # add empty array of programs
            epg_data[callsign] = []

            # submit three concurrent requests for a days guide data
            for day_offset in [0, 1, 2]:
                dttm = datetime.now() + timedelta(days=day_offset)
                future = executor.submit(get_channel_data, dttm, guide_id, newsnetwork)
                future_to_callsign[future] = callsign

        for future in futures.as_completed(future_to_callsign):
            callsign = future_to_callsign[future]
            epg_data[callsign].extend(future.result())
    log('EPG update complete.')
    return epg_data


def map_channel_ids(unblocked):
    """Map channel IDs to guide names."""
    data = call_guide_url(datetime.now())
    soup = BeautifulSoup(data, features="html.parser")
    select = soup.find('select', id="selectlocation-tv")
    options = select.find_all('option')
    channel_map = {'NN': None}
    for option in options:
        title = option.get_text()
        value = option['value']
        for channel in unblocked:
            if unidecode(channel['title']).lower() == unidecode(title).lower():
                channel_map[CBC.get_callsign(channel)] = value
    return channel_map


def call_guide_url(dttm, location=None, newsnetwork=False):
    """Call the guide URL and return the response body."""
    date_str = dttm.strftime('%Y/%m/%d')
    url = (NEWSNET_URL_FMT if newsnetwork else GUIDE_URL_FMT).format(date_str)
    cookies = {}
    if location is not None:
        cookies['pgTvLocation'] = location
    resp = requests.get(url, cookies=cookies)
    if resp.status_code != 200:
        log('{} returns status of {}'.format(url, resp.status_code), True)
        return None
    return resp.content


def get_channel_data(dttm, channel, newsnetwork=False):
    """Get channel program data for a specified date."""
    epg_data = []
    data = call_guide_url(dttm, channel, newsnetwork)
    soup = BeautifulSoup(data, features="html.parser")

    select = soup.find('table', id="sched-table").find('tbody')
    progs = select.find_all('tr')
    for prog in progs:
        prog_js = {}
        tds = prog.find_all('td')
        for cell in tds:
            cell_class = cell['class'][0]
            if cell_class == 'time':
                prog_js['stop'] = datetime.utcfromtimestamp(int(cell['data-end-time-epoch'])/1000).isoformat()
                prog_js['start'] = datetime.utcfromtimestamp(int(cell['data-start-time-epoch'])/1000).isoformat()

            if cell_class == 'program':
                prog_js['title'] = cell.find('a').get_text()
                prog_js['description'] = cell.find('dd').get_text()

        # skip the header row
        if len(prog_js.items()) == 0:
            log('Invalid CBC program data for "{}"'.format(channel), True)
        else:
            epg_data.append(prog_js)

    return epg_data
