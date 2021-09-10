"""Default plugin module."""
import os
from urllib.parse import urlencode, parse_qs, parse_qsl

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import inputstreamhelper
import routing

from resources.lib.cbc import CBC
from resources.lib.utils import log, getAuthorizationFile, get_cookie_file, get_iptv_channels_file
from resources.lib.livechannels import LiveChannels
from resources.lib.liveprograms import LivePrograms
from resources.lib.shows import Shows, CBCAuthError
from resources.lib.iptvmanager import IPTVManager

getString = xbmcaddon.Addon().getLocalizedString
LIVE_CHANNELS = getString(30004)
LIVE_PROGRAMS = getString(30005)
SHOWS = getString(30006)

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

    if not cbc.authorize(username, password, prog.update):
        log('(authorize) unable to authorize', True)
        prog.close()
        xbmcgui.Dialog().ok(getString(30002), getString(30002))
        return False

    prog.close()
    return True


def play(labels, image, url):
    """Play the stream using the configured player."""
    item = xbmcgui.ListItem(labels['title'], path=url)
    item.setArt({'thumb': image, 'poster': image})
    item.setInfo(type="Video", infoLabels=labels)
    helper = inputstreamhelper.Helper('hls')
    if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
        item.setProperty('inputstream', 'inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(plugin.handle, True, item)


@plugin.route('/logout')
def logout():
    """Remove authorization stuff."""
    log('Logging out...', True)
    os.remove(getAuthorizationFile())
    os.remove(get_cookie_file())


@plugin.route('/smil')
def play_smil():
    """Play an SMIL file."""
    cbc = CBC()
    url = cbc.parseSmil(plugin.args['url'][0])
    labels = dict(parse_qsl(plugin.args['labels'][0])) if 'labels' in plugin.args else None
    return play(labels, plugin.args['image'][0], url)


@plugin.route('/show')
def play_show():
    """Play a show."""
    smil = plugin.args['smil'][0]
    image = plugin.args['image'][0]
    labels = plugin.args['labels'][0]
    labels = parse_qs(labels)
    for key in list(labels.keys()):
        labels[key] = labels[key][0]
    shows = Shows()
    try:
        res = shows.getStream(smil)
    except CBCAuthError as ex:
        log('(play_show) auth failed. retrying...', True)
        if not authorize():
            log('(play_show) auth retry failed: {}'.format(ex), True)
            return
        log('(play_show) auth retry successful', True)
        try:
            res = shows.getStream(smil)
        except CBCAuthError as ex:
            if ex.payment:
                log('(play_show) getStream failed because login required', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30011))
            else:
                log('(play_show) getStream failed despite successful auth retry', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30012))
            return

    play(labels, image, res['url'])


@plugin.route('/programs')
def live_programs_menu():
    """Populate the menu with live programs."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    progs = LivePrograms()
    prog_list = progs.getLivePrograms()
    cbc = CBC()
    for prog in prog_list:
        # skip unavailable streams
        if not prog['availabilityState'] == 'available':
            continue

        if prog['availableDate'] == 0:
            continue

        labels = cbc.get_labels(prog)
        image = cbc.getImage(prog)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({'thumb': image, 'poster': image})
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        values = {
            'smil': prog['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(plugin.handle, url, item, False)

    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(plugin.handle)


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

@plugin.route('/channels')
def live_channels_menu():
    """Populate the menu with live channels."""
    xbmcplugin.setContent(plugin.handle, 'videos')
    chans = LiveChannels()
    chan_list = chans.get_live_channels()
    cbc = CBC()
    for channel in chan_list:
        labels = cbc.get_labels(channel)
        callsign = cbc.get_callsign(channel)
        image = cbc.getImage(channel)
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
                                    plugin.url_for(play_smil, url=channel['content'][0]['url'],
                                                   labels=urlencode(labels), image=image), item, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/shows')
def play_menu():
    """Populate the menu with shows."""
    cbc = CBC()
    shows = Shows()
    if 'smil' in plugin.args:
        url = plugin.args['smil'][0]
    else:
        # if there is no smil link this is the main menu of all shows, so it
        # only has show titles (eg: not season or episode titles). In this
        # situation, it is appropriate to sort by title and ignore 'The ...'
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        url = None

    prog = xbmcgui.DialogProgress()
    prog.create(getString(30003))
    try:
        show_list = shows.getShows(url, progress_callback=prog.update)
    except CBCAuthError:
        log('(play_menu) auth failed. retrying', True)
        if not authorize():
            log('(play_menu) auth retry failed', True)
            return
        log('(play_menu) auth retry successful', True)
        try:
            show_list = shows.getShows(url, progress_callback=prog.update)
        except CBCAuthError:
            log('(play_menu) getShows failed despite successful auth retry', True)
            return

    xbmcplugin.setContent(plugin.handle, 'episodes' if 'video' in show_list[0] else 'tvshows')

    prog.close()
    for show in show_list:
        if show['url'] is None:
            continue
        is_video = show['video'] if 'video' in show else False
        labels = cbc.get_labels(show)
        image = show['image'] if 'image' in show else None
        item = xbmcgui.ListItem(labels['title'])

        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true' if is_video else 'false')
        if 'duration' in show:
            item.addStreamInfo('video', {'duration': show['duration']})
        item.setArt({'thumb': image, 'poster': image})

        plugin_url = plugin.url_for(play_menu, smil=show['url'])
        if is_video:
            plugin_url = plugin.url_for(play_show, smil=show['url'], labels=urlencode(labels), image=image)
        xbmcplugin.addDirectoryItem(plugin.handle, plugin_url, item, not is_video)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/')
def main_menu():
    """Populate the menu with the main menu items."""
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        authorize()

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(live_channels_menu),
                                xbmcgui.ListItem(LIVE_CHANNELS), True)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(live_programs_menu),
                                xbmcgui.ListItem(LIVE_PROGRAMS), True)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(play_menu),
                                xbmcgui.ListItem(SHOWS), True)
    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin.run()
