# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules import CHANNELS
from resources.lib.modules.menu import Menu
from resources.lib.vtmgo.vtmgo import VtmGo
from resources.lib.vtmgo.vtmgoauth import VtmGoAuth

_LOGGER = logging.getLogger(__name__)


class Channels:
    """ Menu code related to channels """

    def __init__(self):
        """ Initialise object """
        auth = VtmGoAuth(kodiutils.get_tokens_path())
        self._api = VtmGo(auth.get_tokens())

    def show_channels(self):
        """ Shows TV channels """
        # Fetch EPG from API
        channels = self._api.get_live_channels()

        listing = []
        for channel in channels:
            channel_data = CHANNELS.get(channel.key)

            fanart = channel.background
            title = channel.name
            if channel_data and channel_data.get('logo'):
                icon = '{path}/resources/logos/{logo}-white.png'.format(path=kodiutils.addon_path(), logo=channel_data.get('logo'))
            else:
                icon = channel.logo

            context_menu = [(
                kodiutils.localize(30052, channel=title),  # Watch live {channel}
                'PlayMedia(%s)' %
                kodiutils.url_for('play', category='channels', item=channel.channel_id),
            )]

            if channel_data and channel_data.get('epg'):
                context_menu.append((
                    kodiutils.localize(30053, channel=title),  # TV Guide for {channel}
                    'Container.Update(%s)' %
                    kodiutils.url_for('show_tvguide_channel', channel=channel_data.get('epg'))
                ))

            if channel.epg:
                label = title + '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(
                    title=channel.epg[0].title,
                    start=channel.epg[0].start.strftime('%H:%M'),
                    end=channel.epg[0].end.strftime('%H:%M'))
            else:
                label = title

            listing.append(kodiutils.TitleItem(
                title=label,
                path=kodiutils.url_for('show_channel_menu', channel=channel.key),
                art_dict=dict(
                    icon=icon,
                    thumb=icon,
                    fanart=fanart,
                ),
                info_dict=dict(
                    plot=Menu.format_plot(channel),
                    playcount=0,
                    mediatype='video',
                    studio=channel_data.get('studio_icon') if channel_data else None,
                ),
                stream_dict=dict(
                    codec='h264',
                    height=1080,
                    width=1920,
                ),
                context_menu=context_menu,
            ))

        kodiutils.show_listing(listing, 30007)

    def show_channel_menu(self, key):
        """ Shows a TV channel
        :type key: str
        """
        # Fetch EPG from API
        channel = self._api.get_live_channel(key)
        channel_data = CHANNELS.get(channel.key)

        fanart = channel.background
        title = channel.name
        if channel_data and channel_data.get('logo'):
            icon = '{path}/resources/logos/{logo}-white.png'.format(path=kodiutils.addon_path(), logo=channel_data.get('logo'))
        else:
            icon = channel.logo

        label = kodiutils.localize(30052, channel=title)  # Watch live {channel}
        if channel.epg:
            label = label + '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(
                title=channel.epg[0].title,
                start=channel.epg[0].start.strftime('%H:%M'),
                end=channel.epg[0].end.strftime('%H:%M'))

        # The .pvr suffix triggers some code paths in Kodi to mark this as a live channel
        listing = [kodiutils.TitleItem(
            title=label,
            path=kodiutils.url_for('play', category='channels', item=channel.channel_id) + '?.pvr',
            art_dict=dict(
                icon=icon,
                thumb=icon,
                fanart=fanart,
            ),
            info_dict=dict(
                plot=Menu.format_plot(channel),
                playcount=0,
                mediatype='video',
            ),
            stream_dict=dict(
                codec='h264',
                height=1080,
                width=1920,
            ),
            is_playable=True,
        )]

        if channel_data and channel_data.get('epg'):
            listing.append(
                kodiutils.TitleItem(
                    title=kodiutils.localize(30053, channel=title),  # TV Guide for {channel}
                    path=kodiutils.url_for('show_tvguide_channel', channel=channel_data.get('epg')),
                    art_dict=dict(
                        icon='DefaultAddonTvInfo.png',
                    ),
                    info_dict=dict(
                        plot=kodiutils.localize(30054, channel=title),  # Browse the TV Guide for {channel}
                    ),
                )
            )

        # Add YouTube channels
        if channel_data and kodiutils.get_cond_visibility('System.HasAddon(plugin.video.youtube)') != 0:
            for youtube in channel_data.get('youtube', []):
                listing.append(kodiutils.TitleItem(
                    title=kodiutils.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    path=youtube.get('path'),
                    info_dict=dict(
                        plot=kodiutils.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    )
                ))

        kodiutils.show_listing(listing, 30007, sort=['unsorted'])
