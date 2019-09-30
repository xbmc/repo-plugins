# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' This is the actual VRT NU video plugin entry point '''

from __future__ import absolute_import, division, unicode_literals
from routing import Plugin

try:  # Python 3
    from urllib.parse import unquote_plus
except ImportError:  # Python 2
    from urllib import unquote_plus

from kodiwrapper import KodiWrapper
from statichelper import from_unicode, to_unicode

# pylint: disable=invalid-name
plugin = Plugin()
kodi = KodiWrapper(globals())


@plugin.route('/')
def main_menu():
    ''' The VRT NU plugin main menu '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_main_menu()


@plugin.route('/cache/delete')
@plugin.route('/cache/delete/<cache_file>')
def delete_cache(cache_file=None):
    ''' The API interface to delete caches '''
    kodi.refresh_caches(cache_file=cache_file)


@plugin.route('/tokens/delete')
def delete_tokens():
    ''' The API interface to delete all VRT tokens '''
    from tokenresolver import TokenResolver
    TokenResolver(kodi).delete_tokens()


@plugin.route('/follow/<program>/<title>')
def follow(program, title):
    ''' The API interface to follow a program used by the context menu '''
    from favorites import Favorites
    Favorites(kodi).follow(program=program, title=to_unicode(unquote_plus(from_unicode(title))))


@plugin.route('/unfollow/<program>/<title>')
def unfollow(program, title):
    ''' The API interface to unfollow a program used by the context menu '''
    move_down = bool(plugin.args.get('move_down'))
    from favorites import Favorites
    Favorites(kodi).unfollow(program=program, title=to_unicode(unquote_plus(from_unicode(title))), move_down=move_down)


@plugin.route('/favorites')
def favorites_menu():
    ''' The My favorites menu '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_favorites_menu()


@plugin.route('/favorites/programs')
def favorites_programs():
    ''' The favorites A-Z listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_tvshow_menu(use_favorites=True)


@plugin.route('/favorites/docu')
def favorites_docu():
    ''' The favorites docu listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_favorites_docu_menu()


@plugin.route('/favorites/recent')
@plugin.route('/favorites/recent/<page>')
def favorites_recent(page=1):
    ''' The favorites recent listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_recent_menu(page=page, use_favorites=True)


@plugin.route('/favorites/offline')
@plugin.route('/favorites/offline/<page>')
def favorites_offline(page=1):
    ''' The favorites offline listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_offline_menu(page=page, use_favorites=True)


@plugin.route('/favorites/refresh')
def favorites_refresh():
    ''' The API interface to refresh the favorites cache '''
    from favorites import Favorites
    Favorites(kodi).refresh_favorites()


@plugin.route('/favorites/manage')
def favorites_manage():
    ''' The API interface to manage your favorites '''
    from favorites import Favorites
    Favorites(kodi).manage_favorites()


@plugin.route('/programs')
@plugin.route('/programs/<program>')
@plugin.route('/programs/<program>/<season>')
def programs(program=None, season=None):
    ''' The programs A-Z / seasons / episode listing '''
    from vrtplayer import VRTPlayer
    if program:
        VRTPlayer(kodi).show_episodes_menu(program=program, season=season)
    else:
        VRTPlayer(kodi).show_tvshow_menu()


@plugin.route('/categories')
@plugin.route('/categories/<category>')
def categories(category=None):
    ''' The categories menu and listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_category_menu(category=category)


@plugin.route('/channels')
@plugin.route('/channels/<channel>')
def channels(channel=None):
    ''' The channels menu and listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_channels_menu(channel=channel)


@plugin.route('/livetv')
def livetv():
    ''' The livetv menu '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_livetv_menu()


@plugin.route('/recent')
@plugin.route('/recent/<page>')
def recent(page=1):
    ''' The most recent items listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_recent_menu(page=page)


@plugin.route('/offline')
@plugin.route('/offline/<page>')
def offline(page=1):
    ''' The soon offline listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_offline_menu(page=page)


@plugin.route('/featured')
@plugin.route('/featured/<feature>')
def featured(feature=None):
    ''' The featured menu and listing '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).show_featured_menu(feature=feature)


@plugin.route('/tvguide')
@plugin.route('/tvguide/date')
@plugin.route('/tvguide/date/<date>')
@plugin.route('/tvguide/date/<date>/<channel>')
def tvguide(date=None, channel=None):
    ''' The TV guide menu and listings by date '''
    from tvguide import TVGuide
    TVGuide(kodi).show_tvguide(date=date, channel=channel)


@plugin.route('/tvguide/channel')
@plugin.route('/tvguide/channel/<channel>')
@plugin.route('/tvguide/channel/<channel>/<date>')
def tvguide_channel(channel=None, date=None):
    ''' The TV guide menu and listings by channel '''
    from tvguide import TVGuide
    TVGuide(kodi).show_tvguide(channel=channel, date=date)


@plugin.route('/search')
def search():
    ''' The Search menu and history '''
    from search import Search
    Search(kodi).search_menu()


@plugin.route('/search/clear')
def clear_search():
    ''' Clear the search history '''
    from search import Search
    Search(kodi).clear()


@plugin.route('/search/add/<keywords>')
def add_search(keywords):
    ''' Add to search history '''
    from search import Search
    Search(kodi).add(keywords)


@plugin.route('/search/remove/<keywords>')
def remove_search(keywords):
    ''' Remove from search history '''
    from search import Search
    Search(kodi).remove(keywords)


@plugin.route('/search/query')
@plugin.route('/search/query/<keywords>')
@plugin.route('/search/query/<keywords>/<page>')
def search_query(keywords=None, page=1):
    ''' The Search interface and query listing '''
    from search import Search
    Search(kodi).search(keywords=keywords, page=page)


@plugin.route('/play/id/<video_id>')
@plugin.route('/play/id/<video_id>/<publication_id>')
def play_id(video_id, publication_id=None):
    ''' The API interface to play a video by video_id and/or publication_id '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).play(dict(video_id=video_id, publication_id=publication_id))


@plugin.route('/play/url/<path:video_url>')
def play_url(video_url):
    ''' The API interface to play a video by using a URL '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).play(dict(video_url=video_url))


@plugin.route('/play/latest/<program>')
def play_latest(program):
    ''' The API interface to play the latest episode of a program '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).play_latest_episode(program=program)


@plugin.route('/play/airdate/<channel>/<start_date>')
@plugin.route('/play/airdate/<channel>/<start_date>/<end_date>')
def play_by_air_date(channel, start_date, end_date=None):
    ''' The API interface to play an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00) '''
    from vrtplayer import VRTPlayer
    VRTPlayer(kodi).play_episode_by_air_date(channel, start_date, end_date)


def run(argv):
    ''' Addon entry point from wrapper '''
    kodi.log_access(argv[0])
    plugin.run(argv)
