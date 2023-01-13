# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

import routing

from resources.lib import kodilogging, kodiutils
from resources.lib.streamz.auth import Auth

routing = routing.Plugin()  # pylint: disable=invalid-name

_LOGGER = logging.getLogger(__name__)


@routing.route('/')
def index():
    """ Show the profile selection, or go to the main menu. """
    auth = Auth(kodiutils.get_tokens_path())
    tokens = auth.get_tokens()

    if tokens:
        select_profile()
    else:
        show_login_menu()


@routing.route('/menu')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/select-profile')
@routing.route('/select-profile/<key>')
def select_profile(key=None):
    """ Select your profile """
    from resources.lib.modules.authentication import Authentication
    Authentication().select_profile(key)


@routing.route('/auth/login')
def show_login_menu():
    """ Show the login menu """
    from resources.lib.modules.authentication import Authentication
    Authentication().login()


@routing.route('/auth/clear-tokens')
def auth_clear_tokens():
    """ Clear the authentication tokens """
    from resources.lib.modules.authentication import Authentication
    Authentication().clear_tokens()


@routing.route('/auth/clear-cache')
def auth_clear_cache():
    """ Clear the cache """
    from resources.lib.modules.authentication import Authentication
    Authentication().clear_cache()


@routing.route('/catalog/program/<program>')
def show_catalog_program(program):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program(program)


@routing.route('/program/program/<program>/<season>')
def show_catalog_program_season(program, season):
    """ Show a program from the catalog """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_program_season(program, int(season))


@routing.route('/catalog/recommendations/<storefront>')
def show_recommendations(storefront):
    """ Shows the recommendations of a storefront """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations(storefront)


@routing.route('/catalog/recommendations/<storefront>/<category>')
def show_recommendations_category(storefront, category):
    """ Show the items in a recommendations category """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_recommendations_category(storefront, category)


@routing.route('/catalog/mylist')
def show_mylist():
    """ Show the items in "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_mylist()


@routing.route('/catalog/mylist/add/<content_id>')
def mylist_add(content_id):
    """ Add an item to "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_add(content_id)


@routing.route('/catalog/mylist/del/<content_id>')
def mylist_del(content_id):
    """ Remove an item from "My List" """
    from resources.lib.modules.catalog import Catalog
    Catalog().mylist_del(content_id)


@routing.route('/catalog/continuewatching')
def show_continuewatching():
    """ Show the items in "Continue Watching" """
    from resources.lib.modules.catalog import Catalog
    Catalog().show_continuewatching()


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search().show_search(query)


@routing.route('/play/catalog/<category>/<item>')
def play(category, item):
    """ Play the requested item """
    from resources.lib.modules.player import Player
    Player().play(category, item)


def run(params):
    """ Run the routing plugin """
    kodilogging.config()
    routing.run(params)
