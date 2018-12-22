# -*- coding: utf-8 -*-
"""A Kodi plugin for watching NPO uitzending gemist."""
import datetime
import os
import sys
import time
import collections

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import resources.lib.dateconversions as dateconversions
from resources.lib.directory import Directory
import resources.lib.pypo as pypo
from resources.lib.npo_start import NPO
from resources.lib.errors import NPOContentError
from resources.lib.router import Router
from resources.lib.settings import Settings
from resources.lib.profile import Profile

# constants
# sort orders
DATE_DURATION_TITLE = (xbmcplugin.SORT_METHOD_DATEADDED,
                       xbmcplugin.SORT_METHOD_DURATION,
                       xbmcplugin.SORT_METHOD_VIDEO_TITLE)
# duration up to
DURATION_CATEGORIES = (5, 10, 30, 60)
# Maximum number of recent programs to remember. Just make it bounded.
MAX_NUM_RECENTS = 25
# Maximum number of searchterms to remember. Just make it bounded.
MAX_NUM_SEARCHES = 25

# globals
url = sys.argv[0]
handle = int(sys.argv[1])
parameters = sys.argv[2]

# Objects
addon = xbmcaddon.Addon()
router = Router(handle, url, xbmc)
lang = pypo.Po(addon, xbmc)
s = lang.get_string
npo = NPO()
settings = Settings(handle, xbmc, xbmcplugin)
profile = Profile(addon, xbmc)
directory = Directory(handle, xbmc, xbmcplugin)

# some useful paths
ADDON_PATH = xbmc.translatePath(addon.getAddonInfo("path")).decode("utf-8")
DEFAULT_IMAGE = os.path.join(ADDON_PATH, "resources/icon.png")
DEFAULT_FANART = os.path.join(ADDON_PATH, "resources/fanart.jpg")

# plugin settings
setting_subtitles = settings.get_boolean("subtitles")

# plugin stored data
# deques are recreated every time to make sure the max size can be changed.
data = profile.get_data("recent_programs")
if data is None:
    data = []
profile_recent_programs = collections.deque(data, MAX_NUM_RECENTS)
data = profile.get_data("recent_searches")
if data is None:
    data = []
profile_recent_searches = collections.deque(data, MAX_NUM_SEARCHES)

# plugin content, will tell the view to offer more view types
xbmcplugin.setContent(handle, "tvshows")


@router.route('/')
def index():
    """The main menu."""
    menu_items = [
        {"url": router.make_url(recent),
         "list_item": make_list_item({"label": s(pypo.strings.new),
                                      "plot": s(pypo.strings.new_broadcasts_from_the_last_few_days)})},
        {"url": router.make_url(guides),
         "list_item": make_list_item({"label": s(pypo.strings.guide),
                                      "plot": s(pypo.strings.the_television_guide_for_the_last_week_)})},
        {"url": router.make_url(viewed),
         "list_item": make_list_item({"label": s(pypo.strings.recently_viewed),
                                      "plot": s(pypo.strings.programs_you_have_recently_viewed_check_here_)})},
        {"url": router.make_url(alpha),
         "list_item": make_list_item({"label": s(pypo.strings.programs),
                                      "plot": s(pypo.strings.programs_by_alphabet)})},
        {"url": router.make_url(genres),
         "list_item": make_list_item({"label": s(pypo.strings.genres),
                                      "plot": s(pypo.strings.programs_by_genre)})},
        {"url": router.make_url(durations),
         "list_item": make_list_item({"label": s(pypo.strings.duration),
                                      "plot": s(pypo.strings.broadcasts_of_a_certain_duration_check_here_)})},
        {"url": router.make_url(searches),
         "list_item": make_list_item({"label": s(pypo.strings.search),
                                      "plot": s(pypo.strings.search_for_broadcasts_by_name_or_description)})},
    ]
    for menu_item in menu_items:
        directory.add(**menu_item)
    directory.display()


@router.route("/searches")
def searches():
    """The Search menu."""
    desc = s(pypo.strings.new_search)
    directory.add(router.make_url(search), make_list_item({"label": desc, "plot": desc}))
    for old_search_term in reversed(profile_recent_searches):
        desc = s(pypo.strings.earlier_search_I0I).format(old_search_term)
        directory.add(router.make_url(search, search_term=old_search_term),
                      make_list_item({"label": desc,
                                      "plot": desc}))
    directory.display()


@router.route("/search")
def search(search_term=None):
    """New search dialog."""
    if search_term is None:
        keyboard_dialog = xbmc.Keyboard("", s(pypo.strings.search), False)
        keyboard_dialog.doModal()
        if keyboard_dialog.isConfirmed():
            text = keyboard_dialog.getText()
            if len(text) > 0:
                search_term = text
    if search_term is not None:
        if search_term in profile_recent_searches:
            profile_recent_searches.remove(search_term)
        profile_recent_searches.append(search_term)
        # and store
        profile.set_data("recent_searches", profile_recent_searches)
        # now search
        display_mixed(npo.get_search(search_term))


@router.route("/viewed")
def viewed():
    """Recently viewed programs menu."""
    display_programs(npo.get_series_by_ids(reversed(profile_recent_programs)), sortable=False)


@router.route("/durations")
def durations():
    """Duration categories menu."""
    fr = 0
    for to in DURATION_CATEGORIES:
        desc = s(pypo.strings.I0II1I_minutes).format(fr, to)
        item = {"label": desc, "plot": desc}
        directory.add(router.make_url(duration, fr=fr, to=to), make_list_item(item))
        fr = to
    desc = s(pypo.strings.I0I_minutes_or_more).format(fr)
    item = {"label": desc, "plot": desc}
    directory.add(router.make_url(duration, fr=fr), make_list_item(item))
    directory.display()


@router.route("/duration")
def duration(fr, to=None):
    """Menu of all programs with a duration between fr and to."""
    fr = int(fr) * 60
    if to is not None:
        to = int(to) * 60
    display_broadcasts(npo.get_duration(fr, to), add_time=True)


@router.route("/recent")
def recent():
    """Menu of broadcasts from the last 24 hrs."""
    display_broadcasts(npo.get_recents(), add_time=True)


@router.route("/guides")
def guides():
    """Menu of days in the last week, for the television guides."""
    for days_ago in range(0, 7):
        date = datetime.datetime.today() - datetime.timedelta(days=days_ago)
        desc = s(dateconversions.relative_day_resid(days_ago, date))
        item = {
            "label": desc,
            "plot": desc,
            "info": {
                "date": dateconversions.date2kodi_date(date),
            },
        }
        directory.add(router.make_url(guide, datestamp=time.mktime(date.timetuple())), make_list_item(item))
    directory.display()


@router.route("/guide/channels")
def guide(datestamp):
    """Menu of the channels for a certain date."""
    date = datetime.datetime.fromtimestamp(float(datestamp))
    item = {"label": s(pypo.strings.all), "plot": s(pypo.strings.broadcasts_from_all_channels)}
    directory.add(router.make_url(channelguide, channel="all", datestamp=datestamp), make_list_item(item))

    for guide_item in npo.get_guide_channels(date):
        # Do not support unknown stations
        item = {
            "label": guide_item["label"],
            "plot": guide_item["label"],
            "thumb": guide_item["thumb"],
        }
        directory.add(router.make_url(channelguide, channel=guide_item["channel"], datestamp=datestamp),
                      make_list_item(item))
    directory.display()


@router.route("/guide/channel")
def channelguide(channel, datestamp):
    """Menu of broadcasts on a certain channel for a certain date."""
    display_broadcasts(npo.get_channel_guide(channel, datestamp), add_time=True)


@router.route("/programs/alpha")
def alpha():
    """Menu of letters programs begin with."""
    for letter, value in npo.get_letters():
        if letter == "#":
            item = {"label": letter, "plot": s(pypo.strings.programs_not_starting_with_a_letter).format(letter)}
        else:
            item = {"label": letter, "plot": s(pypo.strings.programs_starting_with_the_letter_I0I).format(letter)}
        directory.add(router.make_url(programs_by_letter, letter=value), make_list_item(item))
    directory.display((xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE,))


@router.route("/programs/alpha/letter")
def programs_by_letter(letter):
    """Menu of all programs starting with letter"""
    display_programs(npo.get_series(letter))


@router.route("/program")
def program(mid):
    """Menu of all broadcasts of a certain program."""
    try:
        display_broadcasts(npo.get_episodes(mid))
    except NPOContentError:
        xbmcgui.Dialog().notification(s(pypo.strings.npo_gemist),
                                      s(pypo.strings.this_program_is_not_available), xbmcgui.NOTIFICATION_ERROR)


@router.route("/programs/genres")
def genres():
    """Menu of all genres of programs."""
    for genre in npo.get_genres():
        item = {"label": genre, "plot": genre}
        directory.add(router.make_url(programs_by_genre, genre=genre), make_list_item(item))
    directory.display((xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE,))


@router.route("/programs/genre")
def programs_by_genre(genre):
    """Menu of all programs with a certain genre."""
    display_programs(npo.get_series_by_genre(genre))


def make_list_item(item, add_time=False):
    """Make an xbmc list item. Add a timestamp in front if add_time is True."""
    if add_time:
        label = u"[{0}] ".format(dateconversions.time2kodi_time(item["aired"]))
    else:
        label = ""
    sorttitle = item["label"]
    if item.get("rerun", False):
        sorttitle += " (" + s(pypo.strings.rerun) + ")"
    label += sorttitle
    if item.get("future", False):
        label = u"[I]{0}[/I]".format(label)

    list_item = xbmcgui.ListItem(label=label)

    art = {
        "thumb": item.get("thumb", DEFAULT_IMAGE),
        "icon": item.get("thumb", DEFAULT_IMAGE),
        "fanart": item.get("fanart", DEFAULT_FANART)
    }
    list_item.setArt(art)

    info = {
        "title": label,
        "sorttitle": sorttitle,
        "plot": item.get("plot", ""),
        "genre": item.get("genre", ""),
        "tagline": item.get("tagline", "")
    }
    if "aired" in item:
        info["dateadded"] = dateconversions.time2kodi_datetime(item["aired"])
    list_item.setInfo("video", info)

    if "duration" in item:
        stream = {"duration": item["duration"]}
        list_item.addStreamInfo("video", stream)

    if item.get("is_video", False):
        list_item.setProperty("IsPlayable", "true")
    return list_item


def display_broadcasts(broadcasts, add_time=False):
    """Display a list of broadcasts."""
    for broadcast in broadcasts:
        directory.add(router.make_url(play, mid=broadcast["mid"]), make_list_item(broadcast, add_time=add_time),
                      is_folder=False)
    directory.display(DATE_DURATION_TITLE)


def display_programs(programs, sortable=True):
    """Display a list of programs."""
    for program_item in programs:
        directory.add(router.make_url(program, mid=program_item["mid"]), make_list_item(program_item))
    sort_methods = []
    if sortable:
        sort_methods.append(xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    directory.display(sort_methods)


def display_mixed(items):
    """Display a list of episodes and programs, mixed."""
    for item in items:
        if item.get("is_video", False):
            directory.add(router.make_url(play, mid=item["mid"]), make_list_item(item),
                          is_folder=False)
        else:
            directory.add(router.make_url(program, mid=item["mid"]), make_list_item(item))
    sort_methods = DATE_DURATION_TITLE
    directory.display(sort_methods)


@router.route("/play")
def play(mid):
    """Play a video with id mid."""
    # store recent
    # TODO If we don't have a serie, we want to store the episode, but we need to adapt recents for that.
    # For now, skip if no series.
    try:
        serie_id = npo.get_serie_id_by_episode(mid)
    except NPOContentError:
        serie_id = None
    if serie_id is not None:
        if serie_id in profile_recent_programs:
            profile_recent_programs.remove(serie_id)
        profile_recent_programs.append(serie_id)
        # store
        profile.set_data("recent_programs", profile_recent_programs)
    # now play
    try:
        play_item = xbmcgui.ListItem(path=(npo.get_play_url(mid)))
        # Add subtitles
        subs_url = npo.get_subtitles_url(mid)
        play_item.setSubtitles([subs_url])
        xbmcplugin.setResolvedUrl(handle, True, listitem=play_item)
        # Wait for the player to play
        player = playing_player()
        # Enable/disable the subtitles
        player.showSubtitles(setting_subtitles)
    except NPOContentError:
        xbmcgui.Dialog().notification(s(pypo.strings.npo_gemist),
                                      s(pypo.strings.this_program_is_not_available), xbmcgui.NOTIFICATION_ERROR)


def playing_player():
    """Get the currently playing player, to add subtitles."""
    player = xbmc.Player()
    passed = 0
    while not player.isPlaying():
        time.sleep(0.1)
        passed += 0.1
        if passed >= 10:
            raise Exception("No video playing. Aborted after 10 seconds.")
    return player


if __name__ == "__main__":
    # Call the router function and pass the plugin call parameters to it.
    router.dispatch(url, parameters)
