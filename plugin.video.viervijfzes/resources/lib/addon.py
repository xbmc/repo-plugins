# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

from routing import Plugin

from resources.lib import kodilogging

try:  # Python 3
    from urllib.parse import unquote
except ImportError:  # Python 2
    from urllib import unquote

routing = Plugin()  # pylint: disable=invalid-name
_LOGGER = logging.getLogger(__name__)


@routing.route('/')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/channels')
def show_channels():
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channels()


@routing.route('/channels/<channel>')
def show_channel_menu(channel):
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_menu(channel)


@routing.route('/channels/<channel>/tvguide')
def show_channel_tvguide(channel):
    """ Shows the dates in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide().show_channel(channel)


@routing.route('/channels/<channel>/tvguide/<date>')
def show_channel_tvguide_detail(channel=None, date=None):
    """ Shows the programs of a specific date in the tv guide """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide().show_detail(channel, date)


@routing.route('/channels/<channel>/catalog')
def show_channel_catalog(channel):
    """ Show the catalog of a channel """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_catalog_channel(channel)


@routing.route('/catalog')
def show_catalog():
    """ Show the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_catalog()


@routing.route('/catalog/<program>')
def show_catalog_program(program):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program(program)


@routing.route('/catalog/<program>/clips')
def show_catalog_program_clips(program):
    """ Show the clips from a program """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program_clips(program)


@routing.route('/catalog/<program>/season/<season>')
def show_catalog_program_season(program, season):
    """ Show a season from a program """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program_season(program, season)


@routing.route('/category')
def show_categories():
    """ Show the catalog by category """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_categories()


@routing.route('/category/<category>')
def show_category(category):
    """ Show the catalog by category """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_category(category)


@routing.route('/recommendations')
def show_recommendations():
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations()


@routing.route('/recommendations/<category>')
def show_recommendations_category(category):
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations_category(category)


@routing.route('/mylist')
def show_mylist():
    """ Show my list """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_mylist()


@routing.route('/mylist/add/<uuid>')
def mylist_add(uuid):
    """ Add a program to My List """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_add(uuid)


@routing.route('/mylist/del/<uuid>')
def mylist_del(uuid):
    """ Remove a program from My List """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_del(uuid)


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search().show_search(query)


@routing.route('/play/live/<channel>')
def play_live(channel):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player().live(channel)


@routing.route('/play/epg/<channel>/<timestamp>')
def play_epg(channel, timestamp):
    """ Play the requested item """
    from resources.lib.modules.tvguide import TvGuide
    TvGuide().play_epg_datetime(channel, timestamp)


@routing.route('/play/catalog')
@routing.route('/play/catalog/<uuid>')
@routing.route('/play/catalog/<uuid>/<islongform>')
def play_catalog(uuid=None, islongform=False):
    """ Play the requested item """
    from ast import literal_eval
    from resources.lib.modules.player import Player
    # Convert string to bool using literal_eval
    Player().play(uuid, literal_eval(islongform))


@routing.route('/play/page/<page>')
def play_from_page(page):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player().play_from_page(unquote(page))


@routing.route('/iptv/channels')
def iptv_channels():
    """ Generate channel data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_channels()  # pylint: disable=too-many-function-args


@routing.route('/iptv/epg')
def iptv_epg():
    """ Generate EPG data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_epg()  # pylint: disable=too-many-function-args


def run(params):
    """ Run the routing plugin """
    kodilogging.config()
    routing.run(params)
