#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Builders for Kodi ListItem menus.

The functions construct (url, ListItem, isFolder) tuples from API data and
addon state passed in as arguments, which makes menu output testable without
instantiating DrDkTvAddon.
"""
from typing import Any, Optional

import xbmcgui

from resources.lib.kodiutils import bool_setting, log, resources_path, tr

# (label, area, image) for the simple area selector
AREA_ITEMS = [
    ('DR TV', 'drtv', 'button-drtv.png'),
    ('Minisjang', 'minisjang', 'button-minisjang.png'),
    ('Ramasjang', 'ramasjang', 'button-ramasjang.png'),
    ('Ultra', 'ultra', 'button-ultra.png'),
    ('Gensyn', 'gensyn', 'gensyn.png'),
]


def area_selector_items(plugin_url: str, menu_items: list[tuple[str, str]]) -> list[tuple[str, xbmcgui.ListItem, bool]]:
    """(url, ListItem, isFolder) tuples for the simple area selector."""
    items = []
    for label, area, image in AREA_ITEMS:
        item = xbmcgui.ListItem(label, offscreen=True)
        png = str(resources_path() / 'media' / image)
        item.setArt({'fanart': png, 'icon': png})
        item.addContextMenuItems(menu_items, False)
        items.append((plugin_url + f'?area={area}', item, True))
    return items


def main_menu_items(plugin_url: str, api: Any, menu_items: list[tuple[str, str]], fanart_image: str, area: str) -> list[tuple[str, xbmcgui.ListItem, bool]]:
    """(url, ListItem, isFolder) tuples for an area's main menu."""
    items = []

    # Live TV
    item = xbmcgui.ListItem(tr(30001), offscreen=True)
    item.setArt({'fanart': fanart_image, 'icon': str(resources_path() / 'icons/livetv.png')})
    item.addContextMenuItems(menu_items, False)
    items.append((plugin_url + '?show=liveTV', item, True))

    if api.user_name != 'anonymous' and area == 'drtv':
        # Mylist and continue watching
        for string_id, param in [(30004, 'mylist'), (30003, 'continue')]:
            item = xbmcgui.ListItem(f'{tr(string_id)} ({api.user_name})', offscreen=True)
            item.setArt({'fanart': fanart_image, 'icon': str(resources_path() / 'icons/drtv.png')})
            item.addContextMenuItems(menu_items, False)
            items.append((plugin_url + f'?show={param}', item, True))

    for hitem in api.get_home(area=area):
        if hitem['path']:
            item = xbmcgui.ListItem(hitem['title'], offscreen=True)
            png = hitem.get('icon', 'star.png')
            if area in ['drtv', 'minisjang', 'ramasjang', 'ultra']:
                png = hitem.get('icon', f'{area}.png')
            item.setArt({'fanart': fanart_image, 'icon': str(resources_path() / f'icons/{png}')})
            item_params = '?listVideos=' + hitem['path']
            runScript = f"RunAddon(plugin.video.drnu,{item_params}&nocache=1)"
            item.addContextMenuItems(menu_items + [(tr(30217), runScript)], False)
            items.append((plugin_url + item_params, item, True))

    # Search videos
    item = xbmcgui.ListItem(tr(30002), offscreen=True)
    item.setArt({'fanart': fanart_image, 'icon': str(resources_path() / 'icons/search.png')})
    item.addContextMenuItems(menu_items, False)
    items.append((plugin_url + '?show=search', item, True))

    if bool_setting('enable.areaitem'):
        item = xbmcgui.ListItem(tr(30101), offscreen=True)
        item.setArt({'fanart': fanart_image, 'icon': str(resources_path() / 'icons/all.png')})
        items.append((plugin_url + '?show=areaselector', item, True))

    return items


def kodi_item(plugin_url: str, api: Any, menu_items: list[tuple[str, str]], fanart_image: str, item: dict, is_season: bool = False) -> Optional[tuple[str, xbmcgui.ListItem, bool]]:
    """Build the (url, ListItem, isFolder) tuple for an API item, or None."""
    menuItems = list(menu_items)
    isFolder = item['type'] not in ['program', 'episode', 'movie']
    if item.get('path', '').startswith('/kanal/') and item['type'] == 'link':
        isFolder = False
    if item['type'] in ['ImageEntry', 'TextEntry'] or item['title'] == '':
        return None
    if 'kodi_seasons' in item:
        is_season = item['kodi_seasons']

    title = api.get_title(item)
    listItem = xbmcgui.ListItem(title, offscreen=True)
    videoInfoTag = listItem.getVideoInfoTag()
    api.set_info(item, videoInfoTag, title)
    if 'images' in item:
        img = {}
        for label in ['tile', 'poster', 'square']:
            if label in item['images']:
                img['thumb'] = item['images'][label]
                img['icon'] = item['images'][label]
                break
        # fanart is the 16:9 background. DR's 'wallpaper' and 'tile' are
        # 1920x1080, while 'poster' is 1440x2160 (2:3 portrait), so poster is
        # only a last resort. Stop at the first match: without a break a later
        # label overwrites an earlier one, which is how poster ended up as the
        # background.
        for label in ['wallpaper', 'tile', 'square', 'poster']:
            if label in item['images']:
                img['fanart'] = item['images'][label]
                break
        listItem.setArt(img)
    else:
        area = api.item_area(item)
        icon_file = str(resources_path() / f'icons/{area}.png')
        listItem.setArt({'fanart': fanart_image, 'icon': icon_file})

    log(f'{title} -- {item["id"]} | {item["type"]} | {item.get("path")}', level=1)
    if item.get('in_mylist', False):
        runScript = f"RunPlugin(plugin://plugin.video.drnu/?delfavorite={item['id']})"
        menuItems.append((tr(30010), runScript))
    elif item.get('ResumeTime', False):
        runScript = f"RunPlugin(plugin://plugin.video.drnu/?delwatched={item['id']})"
        menuItems.append((tr(30008), runScript))
    else:
        if item['type'] not in ['ListEntry', 'RecommendationEntry']:
            runScript = f"RunPlugin(plugin://plugin.video.drnu/?addfavorite={item['id']})"
            menuItems.append((tr(30009), runScript))

    if isFolder:
        if item.get('path', False):
            url = plugin_url + f"?listVideos={item['path']}&seasons={is_season}"
        elif 'list' in item:
            param = item['list'].get('parameter', 'NoParam')
            url = plugin_url + f"?listVideos=ID_{item['list']['id']}&list_param={param}&seasons={is_season}"
        else:
            return None
        runScript = f"RunAddon(plugin.video.drnu,?{url.split('?')[1]}&nocache=1)"
        menuItems.append((tr(30217), runScript))
        listItem.setIsFolder(True)
    else:
        listItem.setIsFolder(False)
        kids = api.kids_item(item)
        url = plugin_url + f"?playVideo={item['id']}&kids={str(kids)}&idpath={item['path']}"
        listItem.setProperty('IsPlayable', 'true')

    listItem.addContextMenuItems(menuItems, False)
    return (url, listItem, isFolder,)
