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

# This is a combination of actual callsigns (NN for newsnet) and guid values
# for over-the-top-only services. No doubt, someone will come back here some
# day and have questions. When this was written, channels in LIST_URL (from
# livechannels.py) had callsigns, guids or both (and maybe neither). Where
# we don't have a callsign, get_callsign (from cbc.py) uses a guid instead.
# Also important is that there needs to be symmetry between get_iptv_epg and
# get_iptv_channels (from livechannels.py) because of how iptvmanager works.
SPECIAL_GUIDES = {
    'NN': 'https://www.cbc.ca/programguide/daily/{}/cbc_news_network',
    '2265331267748': 'https://www.cbc.ca/programguide/daily/{}/cbc_comedy_fast',
    '2076284995790': 'https://www.cbc.ca/programguide/daily/{}/cbc_news_explore',
}

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
            # add empty array of programs
            epg_data[callsign] = []

            # submit three concurrent requests for a days guide data
            for day_offset in [0, 1, 2]:
                dttm = datetime.now() + timedelta(days=day_offset)
                future = executor.submit(get_channel_data, dttm, guide_id, callsign)
                future_to_callsign[future] = callsign

        for future in futures.as_completed(future_to_callsign):
            callsign = future_to_callsign[future]
            epg_data[callsign].extend(future.result())
    log('EPG update complete.')
    return epg_data


def map_channel_ids(unblocked):
    """Map channel IDs to guide names."""
    url = get_guide_url(datetime.now())
    data = call_guide_url(url)
    soup = BeautifulSoup(data, features="html.parser")
    select = soup.find('select', id="selectlocation-tv")
    options = select.find_all('option')
    channel_map = { sign: None for sign in SPECIAL_GUIDES.keys()}
    for option in options:
        title = option.get_text()
        value = option['value']
        for channel in unblocked:
            if unidecode(channel['title']).lower() == unidecode(title).lower():
                channel_map[CBC.get_callsign(channel)] = value
    return channel_map


def get_guide_url(dttm, callsign=None):
    """Get the guide data URL location."""
    date_str = dttm.strftime('%Y/%m/%d')
    url_fmt = SPECIAL_GUIDES[callsign] if callsign in SPECIAL_GUIDES else GUIDE_URL_FMT
    url = url_fmt.format(date_str)
    return url


def call_guide_url(url, location=None):
    """Call the guide URL and return the response body."""
    cookies = {}
    if location is not None:
        cookies['pgTvLocation'] = location
    resp = requests.get(url, cookies=cookies)
    if resp.status_code != 200:
        log('{} returns status of {}'.format(url, resp.status_code), True)
        return None
    return resp.content


def get_channel_data(dttm, channel, callsign):
    """Get channel program data for a specified date."""
    epg_data = []
    url = get_guide_url(dttm, callsign)
    data = call_guide_url(url, channel)
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
                # in situations where we have no title the data is 'to be determined' so just skip it
                # and hopefully at a future date it gets meaningful information
                title_cell = cell.find('a')
                if not title_cell:
                    prog_js = {}
                    break
                prog_js['title'] = title_cell.get_text()
                prog_js['description'] = cell.find('dd').get_text()

        # skip the header row
        if len(prog_js.items()) == 0:
            log('Invalid CBC program data at "{}"'.format(url), True)
        else:
            epg_data.append(prog_js)

    return epg_data
