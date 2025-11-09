"""Default plugin module."""
import os
import json
from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from xbmcvfs import translatePath
import inputstreamhelper
import routing

from resources.lib.cbc import CBC
from resources.lib.utils import log, getAuthorizationFile, get_cookie_file, get_iptv_channels_file
from resources.lib.livechannels import LiveChannels
from resources.lib.gemv2 import GemV2
from resources.lib.iptvmanager import IPTVManager

getString = xbmcaddon.Addon().getLocalizedString
LIVE_CHANNELS = getString(30004)
SEARCH = getString(30026)


plugin = routing.Plugin()


def authorize():
    """Authorize the client."""
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30001))
    cbc = CBC()

    username = xbmcaddon.Addon().getSetting("username")
    if len(username) == 0:
        username = None

    password = xbmcaddon.Addon().getSetting("password")
    if len(password) == 0:
        password = None
        username = None

    if not cbc.azure_authorize(username, password, prog.update):
        log('(authorize) unable to authorize', True)
        prog.close()
        xbmcgui.Dialog().ok(getString(30002), getString(30002))
        return False

    prog.close()
    return True


def play(labels, image, data):
    """Play the stream using the configured player."""
    if not 'url' in data:
        xbmcgui.Dialog().ok(getString(30010), getString(30011))
        return

    (lic, tok) = GemV2.get_stream_drm(data)
    is_helper = None
    mime = None
    drm = None
    if data['type'] == 'hls':
        is_helper = inputstreamhelper.Helper('hls')
    elif data['type'] == 'dash':
        drm = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper('mpd', drm=drm)
        mime = 'application/dash+xml'

    if is_helper is None:
        xbmcgui.Dialog().ok(getString(30027), getString(30027))
        return
    
    if is_helper.check_inputstream():
        url = data['url']
        play_item = xbmcgui.ListItem(path=url)
        play_item.setInfo(type="Video", infoLabels=labels)
        if mime:
            play_item.setMimeType(mime)
            play_item.setContentLookup(False)

        if int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0]) >= 19:
            play_item.setProperty('inputstream', is_helper.inputstream_addon)
        else:
            play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

        if drm:
            play_item.setProperty('inputstream.adaptive.license_type', drm)
            license_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
                'Content-Type': 'application/octet-stream',
                'Origin': 'https://gem.cbc.ca',
                'x-dt-auth-token': tok, # string containing "Bearer eyJ...."
            }
            license_config = [ lic, urlencode(license_headers), 'R{SSM}', 'R']
            license_key = '|'.join(license_config)
            play_item.setProperty('inputstream.adaptive.license_key', license_key)
        xbmcplugin.setResolvedUrl(plugin.handle, True, play_item)
    
def add_items(handle, items):
    for item in items:
        list_item = xbmcgui.ListItem(item['title'])
        list_item.setInfo(type="Video", infoLabels=CBC.get_labels(item))
        image = item['image']['url'].replace('(Size)', '224')
        list_item.setArt({'thumb': image, 'poster': image})
        item_type = item['type']
        is_folder = True
        if item_type.lower() == 'show' or item_type.lower() == 'media':
            p = GemV2.normalized_format_path(item)
            url = plugin.url_for(layout_menu, p)
        else:
            log(f'Unable to handle shelf item type "{item_type}".', True)
            url = None
        xbmcplugin.addDirectoryItem(handle, url, list_item, is_folder)


@plugin.route('/logout')
def logout():
    """Remove authorization stuff."""
    log('Logging out...', True)
    os.remove(getAuthorizationFile())
    os.remove(get_cookie_file())


@plugin.route('/iptv/channels')
def iptv_channels():
    """Send a list of IPTV channels."""
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_channels()


@plugin.route('/iptv/epg')
def iptv_epg():
    """Get EPG information for IPTV manager."""
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_epg()


@plugin.route('/iptv/addall')
def live_channels_add_all():
    """Add all channels back to the PVR listing."""
    os.remove(get_iptv_channels_file())


@plugin.route('/iptv/add/<station>')
def live_channels_add(station):
    """Add a single station."""
    LiveChannels.add_iptv_channel(station)


@plugin.route('/iptv/remove/<station>')
def live_channels_remove(station):
    """Remove a station."""
    LiveChannels.remove_iptv_channel(station)


@plugin.route('/iptv/addonly/<station>')
def live_channels_add_only(station):
    """Remove all but the specified station from the IPTV station list."""
    LiveChannels.add_only_iptv_channel(station)


@plugin.route('/channels/play')
def play_live_channel():
    labels = dict(parse_qsl(plugin.args['labels'][0])) if 'labels' in plugin.args else None
    data = GemV2.get_stream(plugin.args['id'][0], plugin.args['app_code'][0])
    if not 'url' in data:
        log('Failed to get stream URL, attempting to authorize.')
        if authorize():
            data = GemV2.get_stream(plugin.args['id'][0], plugin.args['app_code'][0])
    return play(labels, plugin.args['image'][0] if 'image' in plugin.args else None, data)

@plugin.route('/channels')
def live_channels_menu():
    """Populate the menu with live channels."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    chans = LiveChannels()
    chan_list = chans.get_live_channels()
    cbc = CBC()
    for channel in chan_list:
        labels = CBC.get_labels(channel)
        callsign = cbc.get_callsign(channel)
        image = cbc.get_image(channel)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({'thumb': image, 'poster': image})
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        item.addContextMenuItems([
            (getString(30014), 'RunPlugin({})'.format(plugin.url_for(live_channels_add_all))),
            (getString(30015), 'RunPlugin({})'.format(plugin.url_for(live_channels_add, callsign))),
            (getString(30016), 'RunPlugin({})'.format(plugin.url_for(live_channels_remove, callsign))),
            (getString(30017), 'RunPlugin({})'.format(plugin.url_for(live_channels_add_only, callsign))),
        ])
        xbmcplugin.addDirectoryItem(plugin.handle,
                                    plugin.url_for(play_live_channel, id=channel['idMedia'], app_code='medianetlive',
                                                   labels=urlencode(labels), image=image), item, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/gem/search')
def search():
    handle = plugin.handle
    term = xbmcgui.Dialog().input(SEARCH, type=xbmcgui.INPUT_ALPHANUM)
    results = GemV2.search_by_term(term)
    add_items(handle, results)
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/gem/layout/<path:layout>')
def layout_menu(layout):
    """Populate the menu with featured items."""
    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    for f in GemV2.get_format(layout):
        n = GemV2.normalized_format_item(f)
        p = GemV2.normalized_format_path(f)
        item = xbmcgui.ListItem(n['label'])
        if 'art' in n:
            item.setArt(n['art'])
        item.setInfo(type="Video", infoLabels=n['info_labels'])
        if n['playable']:
            item.setProperty('IsPlayable', 'true')
            url = plugin.url_for(play_live_channel, id=p, app_code=n['app_code'])
        else:
            url = plugin.url_for(layout_menu, p)
        xbmcplugin.addDirectoryItem(handle, url, item, not n['playable'])
    xbmcplugin.endOfDirectory(handle)


@plugin.route('/')
def main_menu():
    """Populate the menu with the main menu items."""
    data_path = translatePath('special://userdata/addon_data/plugin.video.cbc')
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        authorize()

    handle = plugin.handle
    xbmcplugin.setContent(handle, 'videos')
    for c in GemV2.get_browse():
        xbmcplugin.addDirectoryItem(handle, plugin.url_for(layout_menu, c['url']), xbmcgui.ListItem(c['title']), True)
    xbmcplugin.addDirectoryItem(handle, plugin.url_for(live_channels_menu), xbmcgui.ListItem(LIVE_CHANNELS), True)
    xbmcplugin.addDirectoryItem(handle, plugin.url_for(search), xbmcgui.ListItem(SEARCH), True)
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    plugin.run()
