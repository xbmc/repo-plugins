# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT NU video plugin entry point '''

from __future__ import absolute_import, division, unicode_literals
import sys
import routing
from resources.lib import kodiwrapper
from resources.lib.statichelper import to_unicode

try:  # Python 3
    from urllib.parse import unquote_plus
except ImportError:  # Python 2
    from urllib import unquote_plus

plugin = routing.Plugin()
kodi = kodiwrapper.KodiWrapper(globals())


@plugin.route('/')
def main_menu():
    ''' The VRT NU plugin main menu '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_main_menu_items()


@plugin.route('/cache/delete')
@plugin.route('/cache/delete/<cache_file>')
def delete_cache(cache_file=None):
    ''' The API interface to delete caches '''
    kodi.refresh_caches(cache_file=cache_file)


@plugin.route('/tokens/delete')
def delete_tokens():
    ''' The API interface to delete all VRT tokens '''
    from resources.lib import tokenresolver
    tokenresolver.TokenResolver(kodi).delete_tokens()


@plugin.route('/tokens/check-credentials')
def check_credentials():
    ''' Check if the credentials are correct '''
    from resources.lib import tokenresolver
    tokenresolver.TokenResolver(kodi).check_credentials()


@plugin.route('/widevine/install')
def install_widevine():
    ''' The API interface to install Widevine '''
    kodi.install_widevine()


@plugin.route('/follow/<program>/<title>')
def follow(program, title):
    ''' The API interface to follow a program used by the context menu '''
    from resources.lib import favorites
    favorites.Favorites(kodi).follow(program=program, title=to_unicode(unquote_plus(title)))


@plugin.route('/unfollow/<program>/<title>')
def unfollow(program, title):
    ''' The API interface to unfollow a program used by the context menu '''
    from resources.lib import favorites
    favorites.Favorites(kodi).unfollow(program=program, title=to_unicode(unquote_plus(title)))


@plugin.route('/favorites')
def favorites_menu():
    ''' The favorites My program menu '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_favorites_menu_items()


@plugin.route('/favorites/programs')
def favorites_programs():
    ''' The favorites A-Z listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_tvshow_menu_items(use_favorites=True)


@plugin.route('/favorites/docu')
def favorites_docu():
    ''' The favorites docu listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_favorites_docu_menu_items()


@plugin.route('/favorites/recent')
@plugin.route('/favorites/recent/<page>')
def favorites_recent(page=1):
    ''' The favorites recent listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_recent(page=page, use_favorites=True)


@plugin.route('/favorites/offline')
@plugin.route('/favorites/offline/<page>')
def favorites_offline(page=1):
    ''' The favorites offline listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_offline(page=page, use_favorites=True)


@plugin.route('/favorites/refresh')
def favorites_refresh():
    ''' The API interface to refresh the favorites cache '''
    from resources.lib import favorites
    favorites.Favorites(kodi).refresh_favorites()


@plugin.route('/programs')
@plugin.route('/programs/<program>')
@plugin.route('/programs/<program>/<season>')
def programs(program=None, season=None):
    ''' The programs A-Z / seasons / episode listing '''
    from resources.lib import vrtplayer
    if program:
        vrtplayer.VRTPlayer(kodi).show_episodes(program=program, season=season)
    else:
        vrtplayer.VRTPlayer(kodi).show_tvshow_menu_items()


@plugin.route('/categories')
@plugin.route('/categories/<category>')
def categories(category=None):
    ''' The categories menu and listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_category_menu_items(category=category)


@plugin.route('/channels')
@plugin.route('/channels/<channel>')
def channels(channel=None):
    ''' The channels menu and listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_channels_menu_items(channel=channel)


@plugin.route('/livetv')
def livetv():
    ''' The livetv menu '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_livestream_items()


@plugin.route('/recent')
@plugin.route('/recent/<page>')
def recent(page=1):
    ''' The most recent items listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_recent(page=page)


@plugin.route('/offline')
@plugin.route('/offline/<page>')
def offline(page=1):
    ''' The soon offline listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_offline(page=page)


@plugin.route('/featured')
@plugin.route('/featured/<feature>')
def featured(feature=None):
    ''' The featured menu and listing '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).show_featured_menu_items(feature=feature)


@plugin.route('/tvguide')
@plugin.route('/tvguide/<date>')
@plugin.route('/tvguide/<date>/<channel>')
def tvguide(date=None, channel=None):
    ''' The TV guide menu and listings '''
    from resources.lib import tvguide as tvguide_module
    tvguide_module.TVGuide(kodi).show_tvguide(date=date, channel=channel)


@plugin.route('/search')
def search():
    ''' The Search menu and history '''
    from resources.lib import search as search_module
    search_module.Search(kodi).search_menu()


@plugin.route('/search/clear')
def clear_search():
    ''' Clear the search history '''
    from resources.lib import search as search_module
    search_module.Search(kodi).clear()


@plugin.route('/search/query')
@plugin.route('/search/query/<keywords>')
@plugin.route('/search/query/<keywords>/<page>')
def search_query(keywords=None, page=1):
    ''' The Search interface and query listing '''
    from resources.lib import search as search_module
    search_module.Search(kodi).search(keywords=keywords, page=page)


@plugin.route('/play/id/<video_id>')
@plugin.route('/play/id/<video_id>/<publication_id>')
def play_id(video_id, publication_id=None):
    ''' The API interface to play a video by video_id and/or publication_id '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).play(dict(video_id=video_id, publication_id=publication_id))


@plugin.route('/play/url/<path:video_url>')
def play_url(video_url):
    ''' The API interface to play a video by using a URL '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).play(dict(video_url=video_url))


@plugin.route('/play/latest/<program>')
def play_latest(program):
    ''' The API interface to play the latest episode of a program '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).play_latest_episode(program=program)


@plugin.route('/play/airdate/<channel>/<start_date>')
@plugin.route('/play/airdate/<channel>/<start_date>/<end_date>')
def play_by_air_date(channel, start_date, end_date=None):
    ''' The API interface to play an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00) '''
    from resources.lib import vrtplayer
    vrtplayer.VRTPlayer(kodi).play_episode_by_air_date(channel, start_date, end_date)


if __name__ == '__main__':
    kodi.log_access(to_unicode(sys.argv[0]))
    plugin.run(sys.argv)
