# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging
import routing

import kodilogging
from kodiutils import addon_fanart, addon_icon, get_search_string, has_addon, localize, ok_dialog, play, show_listing, TitleItem

from redbull import RedBullTV

kodilogging.config()
plugin = routing.Plugin()  # pylint: disable=invalid-name
redbull = RedBullTV()  # pylint: disable=invalid-name

_LOGGER = logging.getLogger('addon')
COLLECTION = 1
PRODUCT = 2


@plugin.route('/')
def index():
    """ Show the main menu """
    listing = [
        TitleItem(
            title=localize(30010),  # A-Z
            path=plugin.url_for(iptv_play),
            art_dict=dict(
                icon='DefaultMovieTitle.png',
                fanart=addon_fanart(),
                poster=addon_icon()
            ),
            info_dict=dict(
                plot=localize(30228),
            ),
            is_playable=True
        ),
        TitleItem(
            title=localize(30011),  # A-Z
            path=plugin.url_for(browse_product, 'discover'),
            art_dict=dict(
                icon='DefaultMovieTitle.png',
                fanart=addon_fanart(),
                poster=addon_icon()
            )
        ),
        TitleItem(
            title=localize(30012),  # A-Z
            path=plugin.url_for(browse_collection, 'playlists::d554f1ca-5a8a-4d5c-a562-419185d57979'),
            art_dict=dict(
                icon='DefaultMovieTitle.png',
                fanart=addon_fanart(),
                poster=addon_icon()
            )
        ),
        TitleItem(
            title=localize(30013),  # A-Z
            path=plugin.url_for(browse_product, 'events'),
            art_dict=dict(
                icon='DefaultMovieTitle.png',
                fanart=addon_fanart(),
                poster=addon_icon()
            )
        )
    ]

    if has_addon('plugin.video.youtube'):
        listing.append(TitleItem(
            title='YouTube',  # A-Z
            path='plugin://plugin.video.youtube/channel/UCblfuW_4rakIf2h6aqANefA/',
            art_dict=dict(
                icon='DefaultMovieTitle.png',
                fanart=addon_fanart(),
                poster=addon_icon()
            )
        ))

    listing.append(TitleItem(
        title=localize(30014),  # A-Z
        path=plugin.url_for(search),
        art_dict=dict(
            icon='DefaultMovieTitle.png',
            fanart=addon_fanart(),
            poster=addon_icon()
        )
    ))

    show_listing(listing, content='videos', sort=['unsorted'])


@plugin.route('/iptv/play')
def iptv_play():
    play_uid('linear-borb')


@plugin.route('/iptv/channels')
def iptv_channels():
    """ Generate channel data for the Kodi PVR integration """
    from iptvmanager import IPTVManager
    IPTVManager(int(plugin.args['port'][0])).send_channels()  # pylint: disable=too-many-function-args


@plugin.route('/iptv/epg')
def iptv_epg():
    """ Generate EPG data for the Kodi PVR integration """
    from iptvmanager import IPTVManager
    IPTVManager(int(plugin.args['port'][0])).send_epg()  # pylint: disable=too-many-function-args


@plugin.route('/play/<uid>')
def play_uid(uid):
    play(redbull.get_play_url(uid))


@plugin.route('/collection/<uid>')
def browse_collection(uid):
    build_menu(redbull.get_collection_url(uid))


@plugin.route('/product/<uid>')
def browse_product(uid):
    build_menu(redbull.get_product_url(uid))


@plugin.route('/notify/<msg>')
def notify(msg):
    ok_dialog(msg)


@plugin.route('/search')
def search():
    query = get_search_string()
    if query:
        build_menu(redbull.get_search_url(query))


def build_menu(items_url):
    from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
    setContent(plugin.handle, 'videos')
    list_items = []

    try:
        content = redbull.get_content(items_url)
    except IOError:
        ok_dialog(localize(30220), localize(30221))  # Error getting data from Redbull server
        return

    if content.get('links'):
        for link in content.get('links'):
            list_items.append(generate_list_item(link, PRODUCT))

    if content.get('collections'):
        collections = content.get('collections')
        if collections[0].get('collection_type') == 'top_results':  # Handle search results
            content['items'] = collections[0].get('items')
        else:
            for collection in collections:
                list_items.append(generate_list_item(collection, COLLECTION))

    if content.get('items'):
        for item in content.get('items'):
            list_items.append(generate_list_item(item, PRODUCT))

    if not list_items:
        ok_dialog(localize(30222), localize(30223))  # No results found
        return

    for list_item in list_items:
        addDirectoryItem(handle=plugin.handle, url=list_item.getPath(), listitem=list_item, isFolder=('/play/' not in list_item.getPath()))

    endOfDirectory(plugin.handle)


def generate_list_item(element, element_type):
    from xbmcgui import ListItem
    list_item = ListItem(element.get('label') or element.get('title'))
    info_labels = dict(title=element.get('title'))
    uid = element.get('id')
    resources = element.get('resources')

    if element.get('playable') or element.get('action') == 'play':
        list_item.setPath(plugin.url_for(play_uid, uid=uid))
        list_item.setProperty('IsPlayable', 'true')
        if element.get('duration'):
            info_labels['duration'] = element.get('duration') / 1000
    elif element.get('type') == 'video' and element.get('status').get('label') == 'Upcoming':
        info_labels['premiered'] = element.get('status').get('start_time')
        from time import timezone
        list_item.setPath('/notify/' + localize(30024), localize(30025), element.get('event_date') + ' (GMT+' + str(timezone / 3600 * -1))
    elif element_type == COLLECTION:
        list_item.setPath(plugin.url_for(browse_collection, uid=uid))
    elif element_type == PRODUCT:
        list_item.setPath(plugin.url_for(browse_product, uid=uid))

    info_labels['title'] = element.get('label') or element.get('title')
    info_labels['genre'] = element.get('subheading')
    info_labels['plot'] = element.get('long_description') if element.get('long_description') else element.get('short_description')

    if resources:
        list_item.setArt(dict(fanart=redbull.get_image_url(uid, resources, 'landscape')))
        list_item.setArt(dict(landscape=redbull.get_image_url(uid, resources, 'landscape')))
        list_item.setArt(dict(banner=redbull.get_image_url(uid, resources, 'banner')))
        list_item.setArt(dict(poster=redbull.get_image_url(uid, resources, 'poster')))
        list_item.setArt(dict(thumb=redbull.get_image_url(uid, resources, 'thumb')))

    if list_item.getArt('thumb') is None:
        list_item.setArt(dict(thumb=addon_icon()))

    list_item.setInfo(type='Video', infoLabels=info_labels)

    return list_item


def run(params):
    """ Run the routing plugin """
    plugin.run(params)
