from resources.lib.utils import log, getAuthorizationFile
from resources.lib.livechannels import *
from resources.lib.liveprograms import *
from resources.lib.shows import *
from resources.lib.cbc import *
from urllib import urlencode
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urlparse

getString = xbmcaddon.Addon().getLocalizedString

LIVE_CHANNELS = getString(30004)
LIVE_PROGRAMS = getString(30005)
SHOWS = getString(30006)

addon_handle = int(sys.argv[1])

def playSmil(smil, labels, image):
    cbc = CBC()
    url = cbc.parseSmil(smil)
    item = xbmcgui.ListItem(labels['title'])
    item.setIconImage(image)
    item.setInfo(type="Video", infoLabels=labels)
    p = xbmc.Player()
    p.play(url, item)


def playShow(values):
    smil = values['smil'][0]
    image = values['image'][0]
    labels = values['labels'][0]
    labels = urlparse.parse_qs(labels)
    for key in labels.keys():
        labels[key] = labels[key][0]
    shows = Shows()
    res = shows.getStream(smil)
    item = xbmcgui.ListItem(labels['title'])

    item.setInfo(type="Video", infoLabels=labels)
    item.setIconImage(image)
    p = xbmc.Player()
    p.play(res['url'], item)


def liveProgramsMenu():
    progs = LivePrograms()
    prog_list = progs.getLivePrograms()
    cbc = CBC()
    for prog in prog_list:
        # skip unavailable streams
        if not prog['availabilityState'] == 'available':
            continue
        elif prog['availableDate'] == 0:
            continue

        labels = cbc.getLabels(prog)
        image = cbc.getImage(prog)
        item = xbmcgui.ListItem(labels['title'])
        item.setIconImage(image)
        item.setInfo(type="Video", infoLabels=labels)
        values = {
            'smil': prog['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=sys.argv[0] + "?" + urlencode(values),
                                    listitem=item,
                                    isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def liveChannelsMenu():
    chans = LiveChannels()
    chan_list = chans.getLiveChannels()
    cbc = CBC()
    for channel in chan_list:
        labels = cbc.getLabels(channel)
        image = cbc.getImage(channel)
        item = xbmcgui.ListItem(labels['title'])
        item.setIconImage(image)
        item.setInfo(type="Video", infoLabels=labels)
        values = {
            'smil': channel['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=sys.argv[0] + "?" + urlencode(values),
                                    listitem=item,
                                    isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)


def showsMenu(values):
    #result = shows.getShows(None if len(args) == 0 else args[0])
    cbc = CBC()
    shows = Shows()
    if 'smil' in values:
        url = values['smil'][0]
    else:
        url = None
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30003))
    show_list = shows.getShows(url, progress_callback = prog.update)
    prog.close()
    for show in show_list:
        labels = cbc.getLabels(show)
        image = show['image'] if 'image' in show else None
        item = xbmcgui.ListItem(labels['title'])
        item.setIconImage(image)
        item.setInfo(type="Video", infoLabels=labels)
        values = {
            'smil': show['url'],
            'video': show['video'] if 'video' in show else None,
            'image': image
        }

        if not values['video']:
            values['menu'] = SHOWS
        else:
            values['labels'] = urlencode(labels)

        plugin_url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=plugin_url,
                                    listitem=item,
                                    isFolder = True)

    xbmcplugin.endOfDirectory(addon_handle)


def mainMenu():

    for menu_item in [LIVE_CHANNELS, LIVE_PROGRAMS, SHOWS]:
        labels = { 'title': menu_item }
        item = xbmcgui.ListItem(menu_item)
        item.setInfo(type="Video", infoLabels=labels)
        values = { 'menu': menu_item }
        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    url=sys.argv[0] + "?" + urlencode(values),
                                    listitem=item,
                                    isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


if len(sys.argv[2]) == 0:
    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    if not os.path.exists(getAuthorizationFile()):
        prog = xbmcgui.DialogProgress()
        prog.create(getString(30001))
        cbc = CBC()
        prog.update(33)
        reg_url = cbc.getRegistrationURL()
        prog.update(66)
        if not cbc.registerDevice(reg_url):
            # display error window
            log('Error: unable to authorize', True)
            prog.close()
            xbmcgui.Dialog().ok(getString(30002), getString(30002))
        prog.update(100)
        prog.close()

    mainMenu()
else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if 'video' in values and values['video'][0] == 'True':
        playShow(values)
    elif 'menu' in values:
        menu = values['menu'][0]
        if menu == LIVE_CHANNELS:
            liveChannelsMenu()
        elif menu == LIVE_PROGRAMS:
            liveProgramsMenu()
        elif menu == SHOWS:
            showsMenu(values)
    elif 'smil' in values:
        smil = values['smil'][0]
        labels = dict(urlparse.parse_qsl(values['labels'][0]))
        image = values['image'][0]
        playSmil(smil, labels, image)
