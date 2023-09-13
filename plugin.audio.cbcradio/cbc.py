import os
import sys
import time
import urllib.parse as urlparse
from datetime import datetime
import xbmcgui
import xbmcplugin
import xbmc
import now_playing

xbmc.log(level=xbmc.LOGDEBUG, msg=str(sys.argv))

def set_file_constant(file):
    file_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(file_path, "resources", file)


MONITOR = xbmc.Monitor()
BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
FANART = set_file_constant("fanart.jpg")
ICON = set_file_constant("icon.png")
PLAYER = xbmc.Player()

xbmcplugin.setPluginFanart(ADDON_HANDLE, FANART)
xbmcplugin.setContent(ADDON_HANDLE, "audio")

def build_url(query):
    return BASE_URL + "?" + urlparse.urlencode(query)


def list_stations():
    stations = now_playing.get_station_names()
    for station in stations:
        url = build_url({"mode": "folder", "foldername": station})
        li = xbmcgui.ListItem(station)
        li.setArt({"icon": ICON, "fanart": FANART})
        xbmcplugin.addDirectoryItem(
            handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True
        )
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def list_streams(stn):
    station = now_playing.get_stations()[stn]
    for stream in station.streams:
        station_and_title = f"{station.name} - {stream.title}"
        url = build_url(
            {
                "mode": "stream",
                "url": stream.url,
                "title": station_and_title,
                "key": station.key,
                "location": stream.location
            }
        )
        li = xbmcgui.ListItem(station_and_title)
        li.setProperty("IsPlayable", "true")
        li.setArt({"icon": ICON, "fanart": FANART})
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def create_play_item(track):
    info_labels = {
        'album': track.album,
        'artist': track.artist,
        'title': track.title
        }
    play_item = xbmcgui.ListItem()
    xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: play_item.setInfo('music', {info_labels})")
    play_item.setInfo('music', info_labels)
    return play_item


def set_program_art(program):
    try:
        play_item = PLAYER.getPlayingItem()
    except RuntimeError:
        xbmc.log(level=xbmc.LOGDEBUG, msg="RuntimeError: Could not get PlayingItem.")
        return
    if program is not None:
        try:
            play_item.setArt({'fanart': program.artwork_url})
            xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: Set 'fanart': {program.artwork_url}")
        except Exception:
            xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: Could not fetch fanart: {program.artwork_url} Using default.")
            play_item.setArt({'fanart': FANART})
    else:
        play_item.setArt({'fanart': FANART})
        xbmc.log(level=xbmc.LOGDEBUG, msg=f"plugin.audio.cbcradio: Set 'fanart': FANART")
    PLAYER.updateInfoTag(play_item)


def news_break():
    xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: News break.")
    play_item = PLAYER.getPlayingItem()
    play_item.setArt({'fanart': FANART})
    xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: Set 'fanart': FANART")
    tag = play_item.getMusicInfoTag()
    tag.setAlbum(None)
    tag.setArtist(None)
    tag.setTitle("CBC News")
    tag.setComment(None)
    PLAYER.updateInfoTag(play_item)


def calc_minutes():
    time_now = datetime.now().strftime("%M")
    mins = int(time_now)
    return mins


def chill(length):
    MONITOR.waitForAbort(length)
    if MONITOR.abortRequested():
        # had an issue with the fanart sticking around
        # may have been a problem with another addon
        # this might not strictly be necessary
        set_program_art(None)
        PLAYER.stop()


def initialize(key, location, url):
    program_schedule = now_playing.get_program_schedule(key, location)
    program = now_playing.get_current_program(program_schedule)
    playlog = now_playing.get_playlog(program, location)
    last_track = now_playing.get_current_track(playlog)
    play_item = create_play_item(last_track)
    play_item.setPath(url)
    play_item.setProperty('IsPlayable', 'true')
    play_item.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
    if PLAYER.isPlaying():
        PLAYER.stop()
        chill(1)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)
    while not PLAYER.isPlaying():
        chill(1)
    while xbmc.getCondVisibility('Window.IsActive(BusyDialog)'):
        chill(1)
        xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: sleep for fullscreen")
    set_program_art(program)
    xbmc.executebuiltin('Action(FullScreen)')
    xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: fullscreen")
    return program_schedule, program, playlog, last_track, play_item


def play_stream(key, location, url):
    program_schedule, program, playlog, last_track, play_item = initialize(key, location, url)
    c = -1
    while not MONITOR.abortRequested():
        now = time.time() * 1000
        if calc_minutes() in [00, 1, 2, 3, 4, 5] and key == 2:
        # cbc music has 5 min news breaks at the top of the hour
            news_break()
            while calc_minutes() in [00, 1, 2, 3, 4, 5]:
                chill(1)
            now = time.time() * 1000
            program.time_end = now - 10000  # make sure program gets changed after news
            c = -1  # make sure program gets updated if no playlog
        if program.time_end < now:
            try:
                program = now_playing.get_current_program(program_schedule)
                playlog = now_playing.get_playlog(program, location)
                set_program_art(program)
            except Exception:
                pass
        if c == 12 and not playlog:  # if there's no playlog, check every min
            try:
                playlog = now_playing.get_playlog(program, location)
            except Exception:
                pass
            finally:
                c = 0
        if playlog:  # if there is a playlog, get which track should be playing
            track = now_playing.get_current_track(playlog)
            if track != last_track:  # if it's a new track, update 'now playing'
                last_track = track
                play_item = PLAYER.getPlayingItem()
                tag = play_item.getMusicInfoTag()
                tag.setAlbum(track.album)
                tag.setArtist(track.artist)
                tag.setTitle(track.title)
                tag.setComment(f"{program.title} with {program.host}")
                PLAYER.updateInfoTag(play_item)
                # could not get this to work for v19
                # if someone knows how to update currently playing
                # this could be added to the matrix repo as well
                '''play_item = xbmcgui.ListItem()
                play_item.setPath(PLAYER.getPlayingFile())
                play_item.setInfo('music', {'album': track.album, 'artist': track.artist, 'title': track.title})
                PLAYER.updateInfoTag(play_item)'''
                xbmc.log(level=xbmc.LOGDEBUG, msg="plugin.audio.cbcradio: track updated")
        elif program.time_end < now or c == -1:  # if program over or plugin just started
            play_item = PLAYER.getPlayingItem()
            tag = play_item.getMusicInfoTag()
            title = tag.getTitle()
            # if there is no playlog, we're going to set the info displayed to
            # the program name and host. this is mainly for CBC One as most of
            # the shows do not have playlogs. CBC Music, usually does, but
            # they can take awhile to be posted. this will display the show/host
            # until the playlog is available.
            if title == program.title:
                pass
            else:
                tag.setAlbum(None)
                tag.setArtist(program.host)
                tag.setTitle(program.title)
                tag.setComment(None)
                PLAYER.updateInfoTag(play_item)
        chill(5)
        c += 1
        if not PLAYER.isPlaying():
            sys.exit(0)


def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get("mode", None)

    if mode is None:
        list_stations()

    elif mode[0] == "folder":
        station = args["foldername"][0]
        list_streams(station)

    elif mode[0] == "stream":
        url = args["url"][0]
        key = int(args["key"][0])
        location = args["location"][0]
        play_stream(key, location, url)
        sys.exit(0)
