# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib.kodiwrapper import TitleItem
from resources.lib.modules import CHANNELS
from resources.lib.modules.menu import Menu
from resources.lib.vtmgo.vtmgo import VtmGo

_LOGGER = logging.getLogger('channels')


class Channels:
    """ Menu code related to channels """

    def __init__(self, kodi):
        """ Initialise object
        :type kodi: resources.lib.kodiwrapper.KodiWrapper
        """
        self._kodi = kodi
        self._vtm_go = VtmGo(self._kodi)
        self._menu = Menu(self._kodi)

    def show_channels(self):
        """ Shows TV channels """
        # Fetch EPG from API
        channels = self._vtm_go.get_live_channels()

        listing = []
        for channel in channels:
            channel_data = CHANNELS.get(channel.key)

            icon = channel.logo
            fanart = channel.background
            title = channel.name
            if channel_data:
                icon = '{path}/resources/logos/{logo}-white.png'.format(path=self._kodi.get_addon_path(), logo=channel.key)
                title = channel_data.get('label')

            context_menu = [(
                self._kodi.localize(30052, channel=title),  # Watch live {channel}
                'PlayMedia(%s)' %
                self._kodi.url_for('play', category='channels', item=channel.channel_id),
            )]

            if channel_data and channel_data.get('epg'):
                context_menu.append((
                    self._kodi.localize(30053, channel=title),  # TV Guide for {channel}
                    'Container.Update(%s)' %
                    self._kodi.url_for('show_tvguide_channel', channel=channel_data.get('epg'))
                ))

            context_menu.append((
                self._kodi.localize(30055, channel=title),  # Catalog for {channel}
                'Container.Update(%s)' %
                self._kodi.url_for('show_catalog_channel', channel=channel.key)
            ))

            if channel.epg:
                label = title + '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(
                    title=channel.epg[0].title,
                    start=channel.epg[0].start.strftime('%H:%M'),
                    end=channel.epg[0].end.strftime('%H:%M'))
            else:
                label = title

            listing.append(TitleItem(
                title=label,
                path=self._kodi.url_for('show_channel_menu', channel=channel.key),
                art_dict=dict(
                    icon=icon,
                    thumb=icon,
                    fanart=fanart,
                ),
                info_dict=dict(
                    plot=self._menu.format_plot(channel),
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

        self._kodi.show_listing(listing, 30007)

    def show_channel_menu(self, key):
        """ Shows a TV channel
        :type key: str
        """
        # Fetch EPG from API
        channel = self._vtm_go.get_live_channel(key)
        channel_data = CHANNELS.get(channel.key)

        icon = channel.logo
        fanart = channel.background
        title = channel.name
        if channel_data:
            icon = '{path}/resources/logos/{logo}-white.png'.format(path=self._kodi.get_addon_path(), logo=channel.key)
            title = channel_data.get('label')

        title = self._kodi.localize(30052, channel=title)  # Watch live {channel}
        if channel.epg:
            label = title + '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(
                title=channel.epg[0].title,
                start=channel.epg[0].start.strftime('%H:%M'),
                end=channel.epg[0].end.strftime('%H:%M'))
        else:
            label = title

        # The .pvr suffix triggers some code paths in Kodi to mark this as a live channel
        listing = [TitleItem(
            title=label,
            path=self._kodi.url_for('play', category='channels', item=channel.channel_id) + '?.pvr',
            art_dict=dict(
                icon=icon,
                thumb=icon,
                fanart=fanart,
            ),
            info_dict=dict(
                plot=self._menu.format_plot(channel),
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
                TitleItem(
                    title=self._kodi.localize(30053, channel=channel.name),  # TV Guide for {channel}
                    path=self._kodi.url_for('show_tvguide_channel', channel=channel_data.get('epg')),
                    art_dict=dict(
                        icon='DefaultAddonTvInfo.png',
                    ),
                    info_dict=dict(
                        plot=self._kodi.localize(30054, channel=channel.name),  # Browse the TV Guide for {channel}
                    ),
                )
            )

        listing.append(TitleItem(
            title=self._kodi.localize(30055, channel=channel.name),  # Catalog for {channel}
            path=self._kodi.url_for('show_catalog_channel', channel=key),
            art_dict=dict(
                icon='DefaultMovieTitle.png'
            ),
            info_dict=dict(
                plot=self._kodi.localize(30056, channel=channel.name),
            ),
        ))

        # Add YouTube channels
        if channel_data and self._kodi.get_cond_visibility('System.HasAddon(plugin.video.youtube)') != 0:
            for youtube in channel_data.get('youtube', []):
                listing.append(TitleItem(
                    title=self._kodi.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    path=youtube.get('path'),
                    info_dict=dict(
                        plot=self._kodi.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    )
                ))

        self._kodi.show_listing(listing, 30007, sort=['unsorted'])
