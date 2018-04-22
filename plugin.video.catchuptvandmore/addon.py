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

from resources.lib import skeleton
from resources.lib import common
from resources.lib import utils
from resources.lib.root.channels.fr import live_tv_fr


@common.PLUGIN.action()
def root(params):
    # Download xmltv_fr.xml file in background
    live_tv_fr.download_xmltv_in_background()
    return generic_menu(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
@common.PLUGIN.action()
def generic_menu(params):
    """
    Build a generic addon menu
    with all not hidden items
    """
    current_skeleton = skeleton.SKELETON[('root', 'generic_menu')]
    current_path = ['root']

    if 'item_skeleton' in params:
        current_skeleton = eval(params.item_skeleton)
        current_path = eval(params.item_path)

    # First we sort the current menu
    menu = []
    for value in current_skeleton:
        item_id = value[0]
        item_next = value[1]
        # If menu item isn't disable
        if common.PLUGIN.get_setting(item_id):
            # Get order value in settings file
            item_order = common.PLUGIN.get_setting(item_id + '.order')

            # Get english item title in LABELS dict in skeleton file
            # and check if this title has any translated version in strings.po
            item_title = ''
            try:
                item_title = common.GETTEXT(skeleton.LABELS[item_id])
            except Exception:
                item_title = skeleton.LABELS[item_id]

            # Build step by step the module pathfile
            item_path = list(current_path)
            if item_id in skeleton.FOLDERS:
                item_path.append(skeleton.FOLDERS[item_id])
            else:
                item_path.append(item_id)

            item_skeleton = {}
            try:
                item_skeleton = current_skeleton[value]
            except TypeError:
                item_skeleton = {}

            item = (item_order, item_id, item_title, item_path, item_next,
                    item_skeleton)
            menu.append(item)

    menu = sorted(menu, key=lambda x: x[0])

    # If only one item is present, directly open this item
    only_one_item = False
    if len(menu) == 1:
        only_one_item = True
        item = menu[0]
        item_id = item[1]
        item_title = item[2]
        item_path = item[3]
        item_next = item[4]
        item_skeleton = item[5]

        params['item_id'] = item_id
        params['item_path'] = str(item_path)
        params['item_skeleton'] = str(item_skeleton)
        params['window_title'] = item_title

        if item_next == 'root':
            return root(params)
        elif item_next == 'replay_entry':
            return replay_entry(params)
        elif item_next == 'build_live_tv_menu':
            return build_live_tv_menu(params)
        else:
            only_one_item = False

    if not only_one_item:
        listing = []
        for index, (item_order, item_id, item_title, item_path, item_next,
                    item_skeleton) in enumerate(menu):

            # Build context menu (Move up, move down, ...)
            context_menu = []

            item_down = (
                common.GETTEXT('Move down'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='move',
                    direction='down',
                    item_id_order=item_id + '.order',
                    displayed_items=menu) + ')'
            )
            item_up = (
                common.GETTEXT('Move up'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='move',
                    direction='up',
                    item_id_order=item_id + '.order',
                    displayed_items=menu) + ')'
            )

            if index == 0:
                context_menu.append(item_down)
            elif index == len(menu) - 1:
                context_menu.append(item_up)
            else:
                context_menu.append(item_up)
                context_menu.append(item_down)

            hide = (
                common.GETTEXT('Hide'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='hide',
                    item_id=item_id) + ')'
            )
            context_menu.append(hide)

            item_path_media = list(current_path)
            item_path_media.append(item_id)
            media_item_path = common.sp.xbmc.translatePath(
                common.sp.os.path.join(
                    common.MEDIA_PATH,
                    *(item_path_media)
                )
            )

            media_item_path = media_item_path.decode(
                "utf-8").encode(common.FILESYSTEM_CODING)

            icon = media_item_path + '.png'
            fanart = media_item_path + '_fanart.jpg'

            listing.append({
                'icon': icon,
                'fanart': fanart,
                'label': item_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action=item_next,
                    item_id=item_id,
                    item_path=str(item_path),
                    item_skeleton=str(item_skeleton),
                    window_title=item_title
                ),
                'context_menu': context_menu
            })

        return common.PLUGIN.create_listing(
            listing,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,),
            category=common.get_window_title()
        )


@common.PLUGIN.action()
def replay_entry(params):
    """
    replay_entry is the bridge between the
    simpleplegin behavior and each channel files
    """
    if 'item_id' in params:
        params['module_name'] = params.item_id  # w9
        module_path = eval(params.item_path)
        module_path.pop()
        module_path.append(skeleton.CHANNELS[params.module_name])

        # ['root', 'channels', 'fr', '6play']
        params['module_path'] = str(module_path)
        params['next'] = 'replay_entry'

    channel = utils.get_module(params)

    # Legacy fix (il faudrait remplacer channel_name par
    # module_name dans tous les .py des chaines)
    params['channel_name'] = params.module_name

    # Let's go to the channel python file ...
    return channel.channel_entry(params)


@common.PLUGIN.action()
def build_live_tv_menu(params):
    """
    build_live_tv_menu asks each channel for current live TV
    information and display the concatenation of this to Kodi
    """
    folder_path = eval(params.item_path)

    country = folder_path[-1]
    if country == "fr":
        return live_tv_fr.build_live_tv_menu(params)

    else:

        # First we sort channels
        menu = []
        for channel in eval(params.item_skeleton):
            channel_name = channel[0]
            # If channel isn't disable
            if common.PLUGIN.get_setting(channel_name):
                # Get order value in settings file
                channel_order = common.PLUGIN.get_setting(
                    channel_name + '.order')
                channel_path = list(folder_path)
                channel_path.append(skeleton.CHANNELS[channel_name])

                item = (channel_order, channel_name, channel_path)
                menu.append(item)

        menu = sorted(menu, key=lambda x: x[0])

        listing = []
        for index, (channel_order, channel_name, channel_path) in \
                enumerate(menu):
            params['module_path'] = str(channel_path)
            params['module_name'] = channel_name
            params['channel_label'] = skeleton.LABELS[channel_name]

            channel = utils.get_module(params)

            # Legacy fix (il faudrait remplacer channel_name par
            # module_name dans tous les .py des chaines)
            params['channel_name'] = params.module_name

            item = {}
            # Build context menu (Move up, move down, ...)
            context_menu = []

            item_down = (
                common.GETTEXT('Move down'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='move',
                    direction='down',
                    item_id_order=channel_name + '.order',
                    displayed_items=menu) + ')'
            )
            item_up = (
                common.GETTEXT('Move up'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='move',
                    direction='up',
                    item_id_order=channel_name + '.order',
                    displayed_items=menu) + ')'
            )

            if index == 0:
                context_menu.append(item_down)
            elif index == len(menu) - 1:
                context_menu.append(item_up)
            else:
                context_menu.append(item_up)
                context_menu.append(item_down)

            hide = (
                common.GETTEXT('Hide'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='hide',
                    item_id=channel_name) + ')'
            )
            context_menu.append(hide)

            try:
                item = channel.get_live_item(params)
                if item is not None:
                    if type(item) is dict:
                        item['context_menu'] = context_menu
                        listing.append(item)
                    elif type(item) is list:
                        for subitem in item:
                            subitem['context_menu'] = context_menu
                            listing.append(subitem)
            except Exception:
                title = params['channel_label'] + ' broken'
                utils.send_notification(
                    '', title=title, time=2000)

        return common.PLUGIN.create_listing(
            listing,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            ),
            category=common.get_window_title()
        )


@common.PLUGIN.action()
def start_live_tv_stream(params):
    """
    Once the user chooses a Live TV channel
    start_live_tv_stream does the bridge in the channel file
    to load the streaming media
    """

    # Legacy fix (il faudrait remplacer channel_name par
    # module_name dans tous les .py des chaines)
    params['channel_name'] = params.module_name

    channel = utils.get_module(params)

    # Fix tempo pour le XMLTV de France
    if "'fr'," in params.module_path:
        return channel.start_live_tv_stream(params)
    else:
        return channel.get_video_url(params)


@common.PLUGIN.action()
def website_entry(params):
    """
    website_entry is the bridge between the
    simpleplegin behavior and each webiste files
    """
    if 'item_id' in params:
        params['module_name'] = params.item_id
        params['module_path'] = params.item_path
        params['next'] = 'root'

    website = utils.get_module(params)

    # Let's go to the website python file ...
    return website.website_entry(params)


@common.PLUGIN.action()
def move(params):
    if params.direction == 'down':
        offset = + 1
    elif params.direction == 'up':
        offset = - 1

    for k in range(0, len(params.displayed_items)):
        item = eval(params.displayed_items[k])
        item_order = item[0]
        item_id = item[1]
        if item_id + '.order' == params.item_id_order:
            item_swaped = eval(params.displayed_items[k + offset])
            item_swaped_order = item_swaped[0]
            item_swaped_id = item_swaped[1]
            common.PLUGIN.set_setting(
                params.item_id_order,
                item_swaped_order)
            common.PLUGIN.set_setting(
                item_swaped_id + '.order',
                item_order)
            common.sp.xbmc.executebuiltin('XBMC.Container.Refresh()')
            return None


@common.PLUGIN.action()
def hide(params):
    if common.PLUGIN.get_setting('show_hidden_items_information'):
        common.sp.xbmcgui.Dialog().ok(
            common.GETTEXT('Information'),
            common.GETTEXT(
                'To re-enable hidden items go to the plugin settings'))
        common.PLUGIN.set_setting('show_hidden_items_information', False)

    common.PLUGIN.set_setting(params.item_id, False)
    common.sp.xbmc.executebuiltin('XBMC.Container.Refresh()')
    return None


@common.PLUGIN.action()
def download_video(params):
    # Here we only have the webpage link of the video
    # We have to call get_video_url function from the module
    # to get the final video URL
    params['next'] = 'replay_entry'

    # Legacy fix (il faudrait remplacer channel_name par
    # module_name dans tous les .py des chaines)
    params['channel_name'] = params.module_name

    channel = utils.get_module(params)

    params['next'] = 'download_video'
    url_video = channel.get_video_url(params)

    #  Now that we have video URL we can try to download this one
    YDStreamUtils = __import__('YDStreamUtils')
    YDStreamExtractor = __import__('YDStreamExtractor')

    quality_string = {
        'SD': 0,
        '720p': 1,
        '1080p': 2,
        'Highest available': 3
    }

    vid = YDStreamExtractor.getVideoInfo(
        url_video,
        quality=quality_string[common.PLUGIN.get_setting('dl_quality')],
        resolve_redirects=True
    )

    path = common.PLUGIN.get_setting('dl_folder')
    path = path.decode(
        "utf-8").encode(common.FILESYSTEM_CODING)

    with YDStreamUtils.DownloadProgress() as prog:
        try:
            YDStreamExtractor.setOutputCallback(prog)
            YDStreamExtractor.handleDownload(
                vid,
                bg=common.PLUGIN.get_setting('dl_background'),
                path=path
            )
        finally:
            YDStreamExtractor.setOutputCallback(None)
    return None



@common.PLUGIN.action()
def clear_cache():
    utils.clear_cache()
    return None


if __name__ == '__main__':
    common.PLUGIN.run()
