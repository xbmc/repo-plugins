# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

from resources.lib.kodiwrapper import TitleItem
from resources.lib.modules import CHANNELS
from resources.lib.modules.menu import Menu
from resources.lib.vtmgo.vtmgo import VtmGo


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
        product = self._vtm_go.get_product()
        kids = (product == 'VTM_GO_KIDS')

        # Fetch EPG from API
        channel_infos = self._vtm_go.get_live_channels()

        listing = []
        for i, key in enumerate(CHANNELS):  # pylint: disable=unused-variable
            channel = CHANNELS[key]

            if kids and channel.get('kids') is False:
                continue

            # Find this channel in the list
            channel_info = next((c for c in channel_infos if c.key == key), None)

            if channel_info:
                # Lookup the high resolution logo based on the channel name
                icon = '{path}/resources/logos/{logo}-white.png'.format(path=self._kodi.get_addon_path(), logo=channel.get('logo'))
                fanart = '{path}/resources/logos/{logo}.png'.format(path=self._kodi.get_addon_path(), logo=channel.get('logo'))

                context_menu = [(
                    self._kodi.localize(30052, channel=channel.get('label')),  # Watch live {channel}
                    'PlayMedia(%s)' %
                    self._kodi.url_for('play', category='channels', item=channel_info.channel_id)
                ), (
                    self._kodi.localize(30053, channel=channel.get('label')),  # TV Guide for {channel}
                    'Container.Update(%s)' %
                    self._kodi.url_for('show_tvguide_channel', channel=channel.get('epg'))
                )]
                if self._kodi.get_setting_as_bool('metadata_update'):
                    context_menu.append(
                        (
                            self._kodi.localize(30055, channel=channel.get('label')),  # Catalog for {channel}
                            'Container.Update(%s)' %
                            self._kodi.url_for('show_catalog_channel', channel=key)
                        )
                    )

                title = channel.get('label')
                if channel_info.epg:
                    title += '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(title=channel_info.epg[0].title,
                                                                                       start=channel_info.epg[0].start.strftime('%H:%M'),
                                                                                       end=channel_info.epg[0].end.strftime('%H:%M'))

                listing.append(TitleItem(
                    title=title,
                    path=self._kodi.url_for('show_channel_menu', channel=key),
                    art_dict=dict(
                        icon=icon,
                        thumb=icon,
                        fanart=fanart,
                    ),
                    info_dict=dict(
                        plot=self._menu.format_plot(channel),
                        playcount=0,
                        mediatype='video',
                        studio=channel.get('studio_icon'),
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
        channel = CHANNELS[key]

        # Fetch EPG from API
        channel_info = self._vtm_go.get_live_channel(key)

        title = self._kodi.localize(30052, channel=channel.get('label'))  # Watch live {channel}
        if channel_info.epg:
            title += '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(title=channel_info.epg[0].title,
                                                                               start=channel_info.epg[0].start.strftime('%H:%M'),
                                                                               end=channel_info.epg[0].end.strftime('%H:%M'))

        # Lookup the high resolution logo based on the channel name
        icon = '{path}/resources/logos/{logo}-white.png'.format(path=self._kodi.get_addon_path(), logo=channel.get('logo'))
        fanart = '{path}/resources/logos/{logo}.png'.format(path=self._kodi.get_addon_path(), logo=channel.get('logo'))

        listing = [
            TitleItem(
                title=title,
                path=self._kodi.url_for('play', category='channels', item=channel_info.channel_id) + '?.pvr',
                art_dict=dict(
                    icon=icon,
                    thumb=icon,
                    fanart=fanart,
                ),
                info_dict=dict(
                    plot=self._menu.format_plot(channel_info),
                    playcount=0,
                    mediatype='video',
                ),
                stream_dict=dict(
                    codec='h264',
                    height=1080,
                    width=1920,
                ),
                is_playable=True,
            ),
            TitleItem(
                title=self._kodi.localize(30053, channel=channel.get('label')),  # TV Guide for {channel}
                path=self._kodi.url_for('show_tvguide_channel', channel=channel.get('epg')),
                art_dict=dict(
                    icon='DefaultAddonTvInfo.png',
                ),
                info_dict=dict(
                    plot=self._kodi.localize(30054, channel=channel.get('label')),  # Browse the TV Guide for {channel}
                ),
            ),
        ]

        if self._kodi.get_setting_as_bool('metadata_update'):
            listing.append(TitleItem(
                title=self._kodi.localize(30055, channel=channel.get('label')),  # Catalog for {channel}
                path=self._kodi.url_for('show_catalog_channel', channel=key),
                art_dict=dict(
                    icon='DefaultMovieTitle.png'
                ),
                info_dict=dict(
                    plot=self._kodi.localize(30056, channel=channel.get('label')),
                ),
            ))

        # Add YouTube channels
        if self._kodi.get_cond_visibility('System.HasAddon(plugin.video.youtube)') != 0:
            for youtube in channel.get('youtube', []):
                listing.append(TitleItem(
                    title=self._kodi.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    path=youtube.get('path'),
                    info_dict=dict(
                        plot=self._kodi.localize(30206, label=youtube.get('label')),  # Watch {label} on YouTube
                    )
                ))

        self._kodi.show_listing(listing, 30007, sort=['unsorted'])
