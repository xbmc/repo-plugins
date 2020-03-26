# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import routing

from resources.lib.kodiwrapper import KodiWrapper

routing = routing.Plugin()  # pylint: disable=invalid-name
kodi = KodiWrapper(globals())  # pylint: disable=invalid-name


@routing.route('/')
def index():
    """ Show the profile selection, or go to the main menu. """
    if not kodi.has_credentials() or (kodi.get_setting_as_bool('auto_login') and bool(kodi.get_setting('profile'))):
        # If we have no credentials (browse only mode) or we have autologin and a profile, go directly to the main menu
        show_main_menu()

    else:
        # Ask the user for the profile to use
        select_profile()


@routing.route('/menu')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu(kodi).show_mainmenu()


@routing.route('/select-profile')
@routing.route('/select-profile/<key>')
def select_profile(key=None):
    """ Select your profile """
    from resources.lib.modules.authentication import Authentication
    Authentication(kodi).select_profile(key)


@routing.route('/channels')
def show_channels():
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels(kodi).show_channels()


@routing.route('/channels/<channel>')
def show_channel_menu(channel):
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels(kodi).show_channel_menu(channel)


@routing.route('/tvguide/channel/<channel>')
def show_tvguide_channel(channel):
    """ Shows the dates in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide(kodi).show_tvguide_channel(channel)


@routing.route('/tvguide/channel/<channel>/<date>')
def show_tvguide_detail(channel=None, date=None):
    """ Shows the programs of a specific date in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide(kodi).show_tvguide_detail(channel, date)


@routing.route('/catalog')
def show_catalog():
    """ Show the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_catalog()


@routing.route('/catalog/all')
def show_catalog_all():
    """ Show a category in the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_catalog_category()


@routing.route('/catalog/by-category/<category>')
def show_catalog_category(category):
    """ Show a category in the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_catalog_category(category)


@routing.route('/catalog/by-channel/<channel>')
def show_catalog_channel(channel):
    """ Show a category in the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_catalog_channel(channel)


@routing.route('/catalog/program/<program>')
def show_catalog_program(program):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_program(program)


@routing.route('/program/program/<program>/<season>')
def show_catalog_program_season(program, season):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_program_season(program, int(season))


@routing.route('/catalog/recommendations')
def show_recommendations():
    """ Shows the programs of a specific date in the tv guide """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_recommendations()


@routing.route('/catalog/recommendations/<category>')
def show_recommendations_category(category):
    """ Show the items in a recommendations category """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_recommendations_category(category)


@routing.route('/catalog/mylist')
def show_mylist():
    """ Show the items in "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_mylist()


@routing.route('/catalog/mylist/add/<video_type>/<content_id>')
def mylist_add(video_type, content_id):
    """ Add an item to "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).mylist_add(video_type, content_id)


@routing.route('/catalog/mylist/del/<video_type>/<content_id>')
def mylist_del(video_type, content_id):
    """ Remove an item from "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).mylist_del(video_type, content_id)


@routing.route('/catalog/continuewatching')
def show_continuewatching():
    """ Show the items in "Continue Watching" """
    from resources.lib.modules.catalog import Catalog
    Catalog(kodi).show_continuewatching()


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search(kodi).show_search(query)


@routing.route('/metadata/update')
def metadata_update():
    """ Update the metadata for the listings (called from settings) """
    from resources.lib.modules.metadata import Metadata
    Metadata(kodi).update()


@routing.route('/metadata/clean')
def metadata_clean():
    """ Clear metadata (called from settings) """
    from resources.lib.modules.metadata import Metadata
    Metadata(kodi).clean()


@routing.route('/play/epg/<channel>/<timestamp>')
def play_epg_datetime(channel, timestamp):
    """ Play a program based on the channel and the timestamp when it was aired """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide(kodi).play_epg_datetime(channel, timestamp)


@routing.route('/play/catalog/<category>/<item>/<channel>')
def play_or_live(category, item, channel):
    """ Ask to play the requested item or switch to the live channel """
    from resources.lib.modules.player import Player
    Player(kodi).play_or_live(category, item, channel)


@routing.route('/play/catalog/<category>/<item>')
def play(category, item):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player(kodi).play(category, item)


def run(params):
    """ Run the routing plugin """
    routing.run(params)
