# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import imp
import YDStreamUtils
import YDStreamExtractor
from resources.lib import skeleton
from resources.lib import common

YDStreamExtractor.disableDASHVideo(True)

# Useful path
LIB_PATH = common.sp.xbmc.translatePath(
    common.sp.os.path.join(
        common.ADDON.path,
        "resources",
        "lib"))

MEDIA_PATH = (
    common.sp.xbmc.translatePath(
        common.sp.os.path.join(
            common.ADDON.path,
            "resources",
            "media"
        )))

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()


@common.PLUGIN.action()
def root(params):
    """
    Build the addon main menu
    with all not hidden categories
    """
    listing = []
    last_category_id = ''
    for category_id, string_id in skeleton.CATEGORIES.iteritems():
        if common.PLUGIN.get_setting(category_id):
            last_category_id = category_id
            last_window_title = _(string_id)
            context_menu = []
            hide = (
                _('Hide'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='hide',
                    item_id=category_id) + ')'
            )
            media_category_path = common.sp.xbmc.translatePath(
                common.sp.os.path.join(
                    MEDIA_PATH,
                    'categories',
                    category_id[-2:]
                )
            )

            icon = media_category_path + '.png'
            fanart = media_category_path + '_fanart.png'

            context_menu.append(hide)
            listing.append({
                'icon': icon,
                'fanart': fanart,
                'label': _(string_id),
                'url': common.PLUGIN.get_url(
                    action='list_channels',
                    category_id=category_id,
                    window_title=_(string_id)
                ),
                'context_menu': context_menu
            })

    # If only one category is present, directly open this category
    if len(listing) == 1:
        params['category_id'] = last_category_id
        params['window_title'] = last_window_title
        return list_channels(params)

    return common.PLUGIN.create_listing(
        listing,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL)
    )


@common.PLUGIN.action()
def list_channels(params):
    """
    Build the channels list
    of the desired category
    """

    # First, we sort channels by order
    channels_dict = skeleton.CHANNELS[params.category_id]
    channels = []
    for channel_id, title in channels_dict.iteritems():
        # If channel isn't disable
        if common.PLUGIN.get_setting(channel_id):
            channel_order = common.PLUGIN.get_setting(channel_id + '.order')
            channel = (channel_order, channel_id, title)
            channels.append(channel)

    channels = sorted(channels, key=lambda x: x[0])

    # Secondly, we build channels list in Kodi
    listing = []
    for index, (order, channel_id, title) in enumerate(channels):
        # channel_id = channels.fr.6play.w9
        [
            channel_type,  # channels
            channel_category,  # fr
            channel_file,  # 6play
            channel_name  # w9
        ] = channel_id.split('.')

        # channel_module = channels.fr.6play
        channel_module = '.'.join((
            channel_type,
            channel_category,
            channel_file))

        media_channel_path = common.sp.xbmc.translatePath(
            common.sp.os.path.join(
                MEDIA_PATH,
                channel_type,
                channel_category,
                channel_name
            ))

        # Build context menu (Move up, move down, ...)
        context_menu = []

        item_down = (
            _('Move down'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='move',
                direction='down',
                channel_id_order=channel_id + '.order',
                displayed_channels=channels) + ')'
        )
        item_up = (
            _('Move up'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='move',
                direction='up',
                channel_id_order=channel_id + '.order',
                displayed_channels=channels) + ')'
        )

        if index == 0:
            context_menu.append(item_down)
        elif index == len(channels) - 1:
            context_menu.append(item_up)
        else:
            context_menu.append(item_up)
            context_menu.append(item_down)

        hide = (
            _('Hide'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='hide',
                item_id=channel_id) + ')'
        )
        context_menu.append(hide)

        icon = media_channel_path + '.png'
        fanart = media_channel_path + '_fanart.png'

        listing.append({
            'icon': icon,
            'fanart': fanart,
            'label': title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='root',
                channel_name=channel_name,
                channel_module=channel_module,
                channel_id=channel_id,
                channel_category=channel_category,
                window_title=title
            ),
            'context_menu': context_menu
        })

    return common.PLUGIN.create_listing(
        listing,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,)
    )


def get_channel_module(params):
    if 'channel_name' in params and \
            'channel_module' in params and \
            'channel_id' in params and \
            'channel_category' in params:
        channel_name = params.channel_name
        channel_module = params.channel_module
        channel_id = params.channel_id
        channel_category = params.channel_category
        with common.PLUGIN.get_storage() as storage:
            storage['last_channel_name'] = channel_name
            storage['last_channel_module'] = channel_module
            storage['last_channel_id'] = channel_id
            storage['last_channel_category'] = channel_category
    else:
        with common.PLUGIN.get_storage() as storage:
            channel_name = storage['last_channel_name']
            channel_module = storage['last_channel_module']
            channel_id = storage['last_channel_id']
            channel_category = storage['last_channel_category']

    params['channel_name'] = channel_name
    params['channel_id'] = channel_id
    params['channel_category'] = channel_category

    channel_path = common.sp.xbmc.translatePath(
        common.sp.os.path.join(
            LIB_PATH,
            channel_module.replace('.', '/') + '.py'))

    return imp.load_source(
        channel_name,
        channel_path)


@common.PLUGIN.action()
def channel_entry(params):
    """
    Last plugin action function in addon.py.
    Now we are going into the channel python file.
    The channel file can return folder or not item ; playable or not item
    """
    channel = get_channel_module(params)

    # Let's go to the channel file ...
    return channel.channel_entry(params)


@common.PLUGIN.action()
def move(params):
    if params.direction == 'down':
        offset = + 1
    elif params.direction == 'up':
        offset = - 1

    for k in range(0, len(params.displayed_channels)):
        channel = eval(params.displayed_channels[k])
        channel_order = channel[0]
        channel_id = channel[1]
        if channel_id + '.order' == params.channel_id_order:
            channel_swaped = eval(params.displayed_channels[k + offset])
            channel_swaped_order = channel_swaped[0]
            channel_swaped_id = channel_swaped[1]
            common.PLUGIN.set_setting(
                params.channel_id_order,
                channel_swaped_order)
            common.PLUGIN.set_setting(
                channel_swaped_id + '.order',
                channel_order)
            common.sp.xbmc.executebuiltin('XBMC.Container.Refresh()')
            return None


@common.PLUGIN.action()
def hide(params):
    if common.PLUGIN.get_setting('show_hidden_items_information'):
        common.sp.xbmcgui.Dialog().ok(
            _('Information'),
            _('To re-enable hidden items go to the plugin settings'))
        common.PLUGIN.set_setting('show_hidden_items_information', False)

    common.PLUGIN.set_setting(params.item_id, False)
    common.sp.xbmc.executebuiltin('XBMC.Container.Refresh()')
    return None


@common.PLUGIN.action()
def download_video(params):
    #  Ici on a seulement le lien de la page web où se trouve la video
    #  Il faut appeller la fonction get_video_url de la chaine concernée pour avoir l'URL finale de la vidéo
    channel = get_channel_module(params)
    params.next = 'download_video'
    url_video = channel.get_video_url(params)

    #  Maintenant on peut télécharger la vidéo

    print 'URL_VIDEO to download ' + url_video

    vid = YDStreamExtractor.getVideoInfo(url_video, quality=3)
    path = common.PLUGIN.get_setting('dlFolder')

    with YDStreamUtils.DownloadProgress() as prog:  # This gives a progress dialog interface ready to use
        try:
            YDStreamExtractor.setOutputCallback(prog)
            result = YDStreamExtractor.downloadVideo(vid, path)
            if result:
                # success
                full_path_to_file = result.filepath
            elif result.status != 'canceled':
                # download failed
                error_message = result.message
        finally:
            YDStreamExtractor.setOutputCallback(None)

    return None


if __name__ == '__main__':
    window_title = common.get_window_title()
    common.PLUGIN.run(window_title)
