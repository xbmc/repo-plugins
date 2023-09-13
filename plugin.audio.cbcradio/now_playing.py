import urllib.request
import json
import time
from datetime import datetime
from dataclasses import dataclass
import xbmc


API_URL = 'https://www.cbc.ca/listen/api/v1'
LIVE_STATIONS = "/live-radio/getLiveRadioStations"

@dataclass
class Station:
    name: str
    key: int
    streams: list


@dataclass
class Program:
    title: str
    slug_title: str
    host: str
    time_start: int
    time_end: int
    artwork_url: str
    id: int
    network_id: int


@dataclass
class Stream:
    title: str
    location: str
    network: str
    url: str
    station_key: int
    id: int


@dataclass
class Track:
    title: str
    artist: int
    album: str


def get_json_api(url):
    response = urllib.request.urlopen(url)
    return json.loads(response.read().decode('UTF-8'))


def get_station_names():
    names = []
    j = get_json_api(API_URL + LIVE_STATIONS)
    stations = j['data']
    for station in stations:
        names.append(station['liveTitle'])
    return names


def get_stations():
    formatted = {}
    j = get_json_api(API_URL + LIVE_STATIONS)
    stations = j['data']
    for station in stations:
        name = station['liveTitle']
        key = int(station['key'])
        streams = get_streams(station)
        station = Station(name, key, streams)
        formatted[name] = station
    return formatted


def get_streams(station):
    streams = []
    strms = station['streams']
    for s in strms:
        streams.append(
            Stream(
                s['title'],
                s['programGuideLocationKey'],
                s['programGuideNetworkKey'],
                s['streamURL'],
                station['networkID'],
                s['id']
            )
        )
    return streams


def get_program_schedule(key, location):
    url = API_URL + "/program-queue/" + str(key) + "/" + location
    program_schedule = []
    data = get_json_api(url)['data']
    for program in data:
        new_image = program['programImage'].replace("${width}", "2160").replace("${ratio}", "16x9")
        program['programImage'] = new_image
        program_schedule.append(program)
    return program_schedule


def get_current_program(program_schedule):
    now = time.time() * 1000
    for program in program_schedule:
        time_start = program['epochStart']
        time_end = program['epochEnd']
        xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: title: {program['showTitle']}")
        xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: time_start: {time_start}")
        xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: time_end: {time_end}")
        if time_start < now:
            xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: program started")
            started = True
        else:
            started = False
        if time_end > now:
            ended = False
        else:
            xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: program ended")
            ended = True
        if started and not ended:
            show = Program(
                program['showTitle'],
                program['showSlugTitle'],
                program['hostName'],
                program['epochStart'],
                program['epochEnd'],
                program['programImage'],
                program['showID'],
                program['networkID']
            )
            return show


def get_playlog(program, location):
    now = datetime.now()
    playlog = []
    playlog_url = f"https://www.cbc.ca/listen/api/v1/shows/{program.network_id}/{program.id}/playlogs/day/{now.strftime('%Y%m%d')}?withWebURL=true&locationKey={location}&xcountry=INT"
    playlog = get_json_api(playlog_url)['data']['tracks']
    if not playlog:
        xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: No playlog received from CBC.")
    return playlog


def get_current_track(playlog):
    now = time.time() * 1000
    now_playing = None
    if playlog == []:
        xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: Empty playlog.")
        return Track(None, None, None)
    for item in playlog:
        time_started = item['broadcastedTime']
        if now > time_started:
            now_playing = item
    try:
        return Track(now_playing['title'], now_playing['artists'], now_playing['album'])
    except TypeError:
        return Track(None, None, None)


# this is for debugging via cli
'''
def run(key, location):
    program_schedule = get_program_schedule(key, location)
    program = get_current_program(program_schedule)
    playlog = get_playlog(program, location)
    track = get_current_track(playlog)
    old_track = None
    while 1:
        now = time.time() * 1000
        if program.time_end < now:
            time.sleep(15)
            program = get_current_program(program_schedule)
            track = get_current_track(playlog)
        if track != old_track:
            old_track = track
            print(f"""
Show: {program.title}
Host: {program.host}
Song: {track.title}
Artist: {track.artist}
Album: {track.album}
==========================
            """)
    time.sleep(5)
'''
