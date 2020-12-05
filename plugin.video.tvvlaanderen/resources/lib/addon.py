# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

from requests import HTTPError
from routing import Plugin

from resources.lib import kodilogging, kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.exceptions import InvalidLoginException

kodilogging.config()
routing = Plugin()  # pylint: disable=invalid-name
_LOGGER = logging.getLogger(__name__)


@routing.route('/')
def index():
    """ Ask to login, or go to the main menu. """
    if not kodiutils.has_credentials():
        if not kodiutils.yesno_dialog(message=kodiutils.localize(30701)):  # You need to configure your credentials...
            # We have no credentials, return to the Home Menu
            kodiutils.end_of_directory()
            kodiutils.execute_builtin('ActivateWindow(Home)')
            return

        kodiutils.open_settings()

    try:
        # Try authentication
        AuthApi(username=kodiutils.get_setting('username'),
                password=kodiutils.get_setting('password'),
                tenant=kodiutils.get_setting('tenant'),
                token_path=kodiutils.get_tokens_path())
    except InvalidLoginException:
        kodiutils.ok_dialog(message=kodiutils.localize(30203))  # Your credentials are not valid!
        kodiutils.open_settings()
        kodiutils.execute_builtin('ActivateWindow(Home)')
        kodiutils.end_of_directory()
        return

    except HTTPError as exc:
        kodiutils.ok_dialog(message=kodiutils.localize(30702, code='HTTP %d' % exc.response.status_code))  # Unknown error while logging in: {code}
        kodiutils.end_of_directory()
        return

    show_main_menu()


@routing.route('/menu')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/channels')
def show_channels():
    """ Shows TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channels()


@routing.route('/channel/<channel_id>')
def show_channel(channel_id):
    """ Shows TV channel details """
    from resources.lib.modules.channels import Channels
    Channels().show_channel(channel_id)


@routing.route('/channel/<channel_id>/guide')
def show_channel_guide(channel_id):
    """ Shows TV channel guide """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_guide(channel_id)


@routing.route('/channel/<channel_id>/guide/<date>')
def show_channel_guide_detail(channel_id, date):
    """ Shows TV channel guide details """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_guide_detail(channel_id, date)


@routing.route('/channel/<channel_id>/replay')
def show_channel_replay(channel_id):
    """ Shows TV channel replay overview """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_replay(channel_id)


@routing.route('/series/<series_id>')
def show_channel_replay_series(series_id):
    """ Shows TV channel replay series details """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_replay_series(series_id)


@routing.route('/play/asset/<asset_id>')
def play_asset(asset_id):
    """ PLay a Program """
    from resources.lib.modules.player import Player
    Player().play_asset(asset_id)


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search().show_search(query)


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
    routing.run(params)
