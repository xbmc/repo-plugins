# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

from routing import Plugin

from resources.lib import kodilogging

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


@routing.route('/channels/<uuid>')
def show_channel_menu(uuid):
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_menu(uuid)


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


@routing.route('/catalog/<uuid>')
def show_catalog_program(uuid):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program(uuid)


@routing.route('/catalog/season/<uuid>')
def show_catalog_program_season(uuid):
    """ Show a season from a program """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_season(uuid)


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


@routing.route('/continue')
def continue_watching():
    """ Show continue watching list """
    from resources.lib.modules.catalog import Catalog
    Catalog().continue_watching()


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


@routing.route('/play/catalog')
@routing.route('/play/catalog/<uuid>/<content_type>')
def play_catalog(uuid=None, content_type=None):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player().play(uuid, content_type)


def run(params):
    """ Run the routing plugin """
    kodilogging.config()
    routing.run(params)
