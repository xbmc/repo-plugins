# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime, timedelta

import dateutil.tz

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.modules import SETTINGS_ADULT_HIDE, SETTINGS_ADULT_ALLOW
from resources.lib.modules.menu import Menu
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi
from resources.lib.solocoo.epg import EpgApi

_LOGGER = logging.getLogger(__name__)


class Channels:
    """ Menu code related to channels. """

    def __init__(self):
        """ Initialise object. """
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant=kodiutils.get_setting('tenant'),
                       token_path=kodiutils.get_tokens_path())
        self._entitlements = auth.list_entitlements()
        self._channel_api = ChannelApi(auth)
        self._epg_api = EpgApi(auth)

    def show_channels(self):
        """ Shows TV channels. """
        channels = self._channel_api.get_channels(filter_pin=kodiutils.get_setting_int('interface_adult') == SETTINGS_ADULT_HIDE)

        # Load EPG details for the next 6 hours
        date_now = datetime.now(dateutil.tz.UTC)
        date_from = date_now.replace(minute=0, second=0, microsecond=0)
        date_to = (date_from + timedelta(hours=6))
        epg = self._epg_api.get_guide([channel.uid for channel in channels], date_from, date_to)
        for channel in channels:
            shows = [show for show in epg.get(channel.uid, {}) if show.end > date_now]
            try:
                channel.epg_now = shows[0]
            except (IndexError, KeyError):
                pass
            try:
                channel.epg_next = shows[1]
            except (IndexError, KeyError):
                pass

        listing = []
        for item in channels:
            title_item = Menu.generate_titleitem_channel(item)
            title_item.path = kodiutils.url_for('show_channel', channel_id=item.get_combi_id())
            title_item.is_playable = False
            listing.append(title_item)

        kodiutils.show_listing(listing, 30007)

    def show_channel(self, channel_id):
        """ Shows TV channel details.

        :param str channel_id:          The channel we want to display.
        """
        channel = self._channel_api.get_asset(channel_id.split(':')[0])

        # Verify PIN
        if channel.pin and kodiutils.get_setting_int('interface_adult') != SETTINGS_ADULT_ALLOW:
            pin = kodiutils.get_numeric_input(kodiutils.localize(30204))  # Enter PIN
            if not pin:
                # Cancelled
                kodiutils.end_of_directory()
                return

            if not self._channel_api.verify_pin(pin):
                kodiutils.ok_dialog(message=kodiutils.localize(30205))  # The PIN you have entered is invalid!
                kodiutils.end_of_directory()
                return

        listing = []

        # Play live
        live_titleitem = Menu.generate_titleitem_channel(channel)
        live_titleitem.info_dict['title'] = kodiutils.localize(30051, channel=channel.title)  # Watch live [B]{channel}[/B]
        listing.append(live_titleitem)

        # Restart currently airing program
        if channel.epg_now and channel.epg_now.restart:
            restart_titleitem = Menu.generate_titleitem_program(channel.epg_now)
            restart_titleitem.info_dict['title'] = kodiutils.localize(30052, program=channel.epg_now.title)  # Restart [B]{program}[/B]
            restart_titleitem.art_dict['thumb'] = 'DefaultInProgressShows.png'
            listing.append(restart_titleitem)

        # TV Guide
        listing.append(
            TitleItem(
                title=kodiutils.localize(30053, channel=channel.title),  # TV Guide for {channel}
                path=kodiutils.url_for('show_channel_guide', channel_id=channel_id),
                art_dict=dict(
                    icon='DefaultAddonTvInfo.png',
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30054, channel=channel.title),  # Browse the TV Guide for {channel}
                ),
            )
        )

        if channel.replay:
            listing.append(
                TitleItem(
                    title=kodiutils.localize(30055, channel=channel.title),  # Catalog for {channel}
                    path=kodiutils.url_for('show_channel_replay', channel_id=channel_id),
                    art_dict=dict(
                        icon='DefaultMovieTitle.png',
                    ),
                    info_dict=dict(
                        plot=kodiutils.localize(30056, channel=channel.title),  # Browse the Catalog for {channel}
                    ),
                )
            )

        kodiutils.show_listing(listing, 30007)

    def show_channel_guide(self, channel_id):
        """ Shows the dates in the tv guide.

        :param str channel_id:          The channel for which we want to show an EPG.
        """
        listing = []
        for day in self._get_dates('%A %d %B %Y'):
            if day.get('highlight'):
                title = '[B]{title}[/B]'.format(title=day.get('title'))
            else:
                title = day.get('title')

            listing.append(TitleItem(
                title=title,
                path=kodiutils.url_for('show_channel_guide_detail', channel_id=channel_id, date=day.get('key')),
                art_dict=dict(
                    icon='DefaultYear.png',
                    thumb='DefaultYear.png',
                ),
                info_dict=dict(
                    plot=None,
                    date=day.get('date'),
                ),
            ))

        kodiutils.show_listing(listing, 30013, content='files')

    def show_channel_guide_detail(self, channel_id, date):
        """ Shows the dates in the tv guide.

        :param str channel_id:          The channel for which we want to show an EPG.
        :param str date:                The date to show.
        """
        # Lookup with CAPI
        lookup_id = channel_id.split(':')[1]
        programs = self._epg_api.get_guide_with_capi([lookup_id], date)

        # Lookup with TV API
        # lookup_id = channel_id.split(':')[0]
        # programs = self._epg_api.get_guide([lookup_id], date)

        listing = [Menu.generate_titleitem_program(item, timeline=True) for item in programs.get(lookup_id)]

        kodiutils.show_listing(listing, 30013, content='files')

    def show_channel_replay(self, channel_id):
        """ Shows the replay programs of the specified channel.

        :param str channel_id:          The channel for which we want to show the replay programs.
        """
        programs = self._channel_api.get_replay(channel_id.split(':')[0])

        listing = []
        for item in programs:
            # Hide these items
            if item.title == EpgApi.EPG_NO_BROADCAST:
                continue

            if item.series_id:
                listing.append(Menu.generate_titleitem_series(item))
            else:
                listing.append(Menu.generate_titleitem_program(item))

        kodiutils.show_listing(listing, 30013, content='tvshows', sort=['label'])

    def show_channel_replay_series(self, series_id):
        """ Shows the related programs of the specified channel.

        :param str series_id:           The series we want to show.
        """

        programs = self._channel_api.get_series(series_id)

        listing = [Menu.generate_titleitem_program(item) for item in programs]

        kodiutils.show_listing(listing, 30013, content='episodes')

    @staticmethod
    def _get_dates(date_format):
        """ Return a dict of dates.

        :param str date_format:         The date format to use for the labels.

        :rtype: list[dict]
        """
        dates = []
        today = datetime.today()

        # The API provides content for 8 days in the past and 0 days in the future
        for i in range(0, -8, -1):
            day = today + timedelta(days=i)

            if i == -1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30301), day.strftime(date_format)),  # Yesterday
                    'key': 'yesterday',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            elif i == 0:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30302), day.strftime(date_format)),  # Today
                    'key': 'today',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': True,
                })
            elif i == 1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30303), day.strftime(date_format)),  # Tomorrow
                    'key': 'tomorrow',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            else:
                dates.append({
                    'title': day.strftime(date_format),
                    'key': day.strftime('%Y-%m-%d'),
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })

        return dates
