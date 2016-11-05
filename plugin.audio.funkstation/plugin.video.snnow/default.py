import snnow
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse

__settings__ = xbmcaddon.Addon(id='plugin.video.snnow')
__language__ = __settings__.getLocalizedString


def getAuthCredentials():
    username = __settings__.getSetting("username")
    if len(username) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    # get the password
    password = __settings__.getSetting("password")
    if len(password) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    mso = __settings__.getSetting("mso")

    return { 'u' : username, 'p' : password, 'm' : mso }


def createMainMenu():
    """
    Create the main menu
    """

    sn = snnow.SportsnetNow()
    creds = getAuthCredentials()
    if creds == None:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    sn.checkMSOs()
    if not sn.authorize(creds['u'], creds['p'], creds['m']):
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30004))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)

    channels = sn.getChannels()
    guide = sn.getGuideData()
    
    for channel in channels:
        chanId = str(channel['id'])
        values = { 'menu' : 'channel', 'name' : channel['name'],
                   'id' : channel['id'], 'abbr' : channel['abbr'] }

        title = values['name']
        showTitle = channel['name']

        if chanId in guide.keys():
            prog = guide[chanId]
            for key in prog.keys():
                values[key] = prog[key].encode('utf-8')
        
            if prog['tvshowtitle']:
                title += ' ([B]' + prog['tvshowtitle'] + '[/B]'
                if prog['title']:
                    title += ' - [I]' + prog['title'] + '[/I]'
                title += ')'

            showTitle = prog['tvshowtitle']

        live = xbmcgui.ListItem(title)
        
        labels = {"TVShowTitle" : showTitle,
                  "Studio" : channel['name']}
        if 'title' in values:
            labels['Title'] = prog['title']
        if 'plot' in values:
            labels["Plot"] = prog['plot']
        live.setInfo(type="Video", infoLabels=labels)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=live,
                                    isFolder=True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def createLiveMenu(values):
    pid = values['provider'][0]
    pf = providerfactory.ProviderFactory()
    provider = pf.getProviders()[pid]


    channels = provider.getChannels()
    for channel in channels:
        values = { 'menu' : 'channel', 'provider' : pid,
                   'name' : channel['name'], 'id' : channel['id'],
                   'abbr' : channel['abbr'] }
        live = xbmcgui.ListItem(values['name'])
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=live,
                                    isFolder=False)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playChannel(values):
    mso = __settings__.getSetting("mso")
    stream = getChannelStream(values['id'][0], values['abbr'][0], mso)

    if not stream:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30005))
    else:
        name = values['name'][0]
        li = xbmcgui.ListItem(name)

        labels = {"TVShowTitle" : values['tvshowtitle'][0],
                  "Studio" : values['name'][0]}
        if 'title' in values:
            labels['Title'] = values['title'][0]
        if 'plotoutline' in values:
            labels["Plot"] = values['plot'][0]
        li.setInfo(type="Video", infoLabels=labels)
        p = xbmc.Player()
        p.play(stream, li)


def getChannelStream(channelId, channelName, msoName):
    sn = snnow.SportsnetNow()
    stream = sn.getChannel(channelId, channelName, msoName)
    if not stream:
        # auth token may have expired - attempt re-auth first
        print('Auth token may have expired. Attempting re-auth.')
        creds = getAuthCredentials()
        if sn.authorize(creds['u'], creds['p'], creds['m']):
            return sn.getChannel(channelId, channelName, msoName)
    return stream


if len(sys.argv[2]) == 0:

    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    # show the main menu
    createMainMenu()
else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if values['menu'][0] == 'live':
        createLiveMenu(values)
    elif values['menu'][0] == 'channel':
        playChannel(values)

