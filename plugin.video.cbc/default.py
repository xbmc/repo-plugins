from resources.lib.utils import log, getAuthorizationFile
from resources.lib.livechannels import *
from resources.lib.liveprograms import *
from resources.lib.shows import *
from resources.lib.cbc import *
from urllib.parse import urlencode
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib.parse
import inputstreamhelper

getString = xbmcaddon.Addon().getLocalizedString

LIVE_CHANNELS = getString(30004)
LIVE_PROGRAMS = getString(30005)
SHOWS = getString(30006)

# handle logout before using argv[1] as the addon handle
if sys.argv[1] == 'logout':
    log('Logging out... {}'.format(sys.argv[1]), True)
    os.remove(getAuthorizationFile())
    sys.exit(0)

addon_handle = int(sys.argv[1])

def authorize():
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
    item = xbmcgui.ListItem(labels['title'], path=url)
    item.setArt({ 'thumb': image, 'poster': image })
    item.setInfo(type="Video", infoLabels=labels)
    helper = inputstreamhelper.Helper('hls')
    if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
        item.setProperty('inputstreamaddon','inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    xbmcplugin.setResolvedUrl(addon_handle, True, item)

def playSmil(smil, labels, image):
    cbc = CBC()
    url = cbc.parseSmil(smil)
    return play(labels, image, url)


def playShow(values):
    smil = values['smil'][0]
    image = values['image'][0]
    labels = values['labels'][0]
    labels = urllib.parse.parse_qs(labels)
    for key in list(labels.keys()):
        labels[key] = labels[key][0]
    shows = Shows()
    try:
        res = shows.getStream(smil)
    except CBCAuthError as e:
        log('(playShows) auth failed. retrying', True)
        if not authorize():
            log('(playShows) auth retry failed', True)
            return
        log('(playShows) auth retry successful', True)
        try:
            res = shows.getStream(smil)
        except CBCAuthError as e:
            if e.payment:
                log('(playShows) getStream failed because login required', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30011))
            else:
                log('(playShows) getStream failed despite successful auth retry', True)
                xbmcgui.Dialog().ok(getString(30010), getString(30012))
            return

    return play(labels, image, res['url'])


def liveProgramsMenu():
    xbmcplugin.setContent(addon_handle, 'videos')
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
        item.setArt({ 'thumb': image, 'poster': image })
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        values = {
            'smil': prog['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(addon_handle, url, item,False)

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(addon_handle)


def liveChannelsMenu():
    xbmcplugin.setContent(addon_handle, 'videos')
    chans = LiveChannels()
    chan_list = chans.getLiveChannels()
    cbc = CBC()
    for channel in chan_list:
        labels = cbc.getLabels(channel)
        image = cbc.getImage(channel)
        item = xbmcgui.ListItem(labels['title'])
        item.setArt({ 'thumb': image, 'poster': image })
        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true')
        values = {
            'smil': channel['content'][0]['url'],
            'labels': urlencode(labels),
            'image': image
        }
        url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(addon_handle, url, item, False)

    xbmcplugin.endOfDirectory(addon_handle)


def showsMenu(values):
    cbc = CBC()
    shows = Shows()
    if 'smil' in values:
        url = values['smil'][0]
    else:
        # if there is no smil link this is the main menu of all shows, so it
        # only has show titles (eg: not season or episode titles). In this
        # situation, it is appropriate to sort by title and ignore 'The ...'
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
        url = None

    prog = xbmcgui.DialogProgress()
    prog.create(getString(30003))
    try:
        show_list = shows.getShows(url, progress_callback = prog.update)
    except CBCAuthError as e:
        log('(showsMenu) auth failed. retrying', True)
        if not authorize():
            log('(showsMenu) auth retry failed', True)
            return
        log('(showsMenu) auth retry successful', True)
        try:
            show_list = shows.getShows(url, progress_callback = prog.update)
        except CBCAuthError as e:
            log('(showsMenu) getShows failed despite successful auth retry', True)
            return

    # if the first episode is video, assume all are video
    isVideo = True if 'video' in show_list[0] else False
    xbmcplugin.setContent(addon_handle, 'episodes' if isVideo else 'tvshows')

    prog.close()
    for show in show_list:
        if show['url'] == None:
            continue
        isVideo = show['video'] if 'video' in show else False
        labels = cbc.getLabels(show)
        image = show['image'] if 'image' in show else None
        item = xbmcgui.ListItem(labels['title'])


        item.setInfo(type="Video", infoLabels=labels)
        item.setProperty('IsPlayable', 'true' if isVideo else 'false')
        if 'duration' in show:
            item.addStreamInfo('video', {'duration':show['duration']})
        item.setArt({ 'thumb': image, 'poster': image })
        values = {
            'smil': show['url'],
            'video': show['video'] if isVideo else None,
            'image': image
        }

        if not values['video']:
            values['menu'] = SHOWS
        else:
            values['labels'] = urlencode(labels)

        plugin_url = sys.argv[0] + "?" + urlencode(values)
        xbmcplugin.addDirectoryItem(addon_handle, plugin_url, item, not isVideo)

    xbmcplugin.endOfDirectory(addon_handle)


def mainMenu():

    xbmcplugin.setContent(addon_handle, 'videos')
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
        authorize()

    mainMenu()
else:
    values = urllib.parse.parse_qs(sys.argv[2][1:])
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
        labels = dict(urllib.parse.parse_qsl(values['labels'][0]))
        image = values['image'][0]
        playSmil(smil, labels, image)
