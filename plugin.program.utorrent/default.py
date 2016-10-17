import sys, os, re, time
import xbmcaddon, xbmcplugin, xbmcgui, xbmc
import simplejson

# Plugin constants
__addonname__ = "uTorrent"
__addonid__   = "plugin.program.utorrent"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__language__  = __addon__.getLocalizedString
__cwd__       = xbmc.translatePath( __addon__.getAddonInfo('path') )
__profile__   = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__icondir__   = os.path.join( __cwd__,'resources','icons' )

# Shared resources
BASE_RESOURCE_PATH = os.path.join( __cwd__, 'resources', 'lib' )
sys.path.append (BASE_RESOURCE_PATH)

UT_ADDRESS = __addon__.getSetting('ip')
UT_PORT = __addon__.getSetting('port')
UT_USER = __addon__.getSetting('usr')
UT_PASSWORD = __addon__.getSetting('pwd')
UT_TDIR = xbmc.translatePath( __addon__.getSetting('tdir') )
UT_HTTPS = __addon__.getSetting('use_https') == 'true'
UT_PATH = '/' + __addon__.getSetting('path').strip('/') + '/'
if UT_PATH != __addon__.getSetting('path'):
    __addon__.setSetting('path', UT_PATH)
UT_LABEL = __addon__.getSetting('use_label') == 'true'

from utilities import *

app = App()

params = {
    'address': UT_ADDRESS,
    'port': UT_PORT,
    'user': UT_USER,
    'password': UT_PASSWORD,
    'path': UT_PATH,
    'https': UT_HTTPS
}
baseurl = Url(**params)
myClient = Client(baseurl)

def getToken():
    try:
        data = myClient.CmdGetToken()
    except:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__addonname__ + ' ' + __language__(32100).encode('utf8'), __language__(32101).encode('utf8'), __language__(32102).encode('utf8'))
        if ret==True:
            __addon__.openSettings()
        sys.exit()

    match = re.compile("<div id='token' style='display:none;'>(.+?)</div>").findall(data)
    token = match[0]

    baseurl.token = token
    return token

torrentList = TorList()

def updateList():
    token = getToken()
    torrentList.empty()
    data = myClient.HttpCmd(baseurl.getBaseUrl(True) + '&list=1')
    data = unicode(data, 'utf-8', errors='ignore')
    json_response = simplejson.loads(data)
    for torrent in json_response['torrents']:
        torrentList.append(TorItem(torrent))

def listLabels():
    """
    List torrent labels
    """
    updateList()
    labels = torrentList.get_labels()
    for label in labels:
        thumb = os.path.join(__icondir__, 'label.png')

        label_text = label
        if not label:
            label_text = __language__(30009).encode('utf8')
        text = label_text + " [COLOR FFFF0000]" + str(labels[label]) + "[/COLOR]"

        u = urllib.urlencode({
            'mode': App.MODE_LIST,
            'label': label.encode('utf8'),
            'no_label': '1' if not label else ''
        })
        u = sys.argv[0] + '?' + u
        point = xbmcgui.ListItem(text, thumbnailImage=thumb)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=point, isFolder=True, totalItems=labels[label])
    xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)

def listTorrents():
    """
    List torrents, if label selected, then list torrents in label
    """
    updateList()

    selected_label = app.get_param('label')
    if selected_label:
        selected_label = selected_label.decode('utf8')
    if app.get_param('no_label'):
        selected_label = ''
    labels = torrentList.get_labels()

    # list labels if label not selected and we have labels (ome then one empty one)
    if UT_LABEL and selected_label == None and len(labels.keys()) > 1:
        listLabels()
        return

    # label does not exist or does not have any torrents anymore
    if UT_LABEL and selected_label and (selected_label not in labels.keys() or not labels[selected_label]):
        listLabels()
        return

    for tor in torrentList.items:
        if UT_LABEL and selected_label != None and selected_label != tor.label:
            continue
        addDir(tor, selected_label)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)

def getFiles(hash):
    token = getToken()
    url = baseurl.getActionUrl('getfiles', hash)
    data = myClient.HttpCmd(url)
    fileList = []
    data = unicode(data, 'utf-8', errors='ignore')
    json_response = simplejson.loads(data)
    for file in json_response['files'][1]:
        xbmc.log( "%s::getFiles - %d: %s" % ( __addonname__, len(fileList), str(file) ), xbmc.LOGDEBUG )
        fileList.append(file[0].encode('utf-8'))
    return fileList

def performAction(selection,sid):
    dialog = xbmcgui.Dialog()
    if sid == '-1':
        # don't support stream
        sel = dialog.select(__language__(32001),[__language__(32002),__language__(32003),__language__(32004),__language__(32005),__language__(32006),__language__(32007),__language__(32008)])
    else:
        sel = dialog.select(__language__(32001),[__language__(32002),__language__(32003),__language__(32004),__language__(32005),__language__(32006),__language__(32007),__language__(32008),__language__(32201)])
    token = getToken()
    if sel == 0:
        myClient.HttpCmd(baseurl.getActionUrl('pause', selection))
    if sel == 1:
        myClient.HttpCmd(baseurl.getActionUrl('unpause', selection))
    if sel == 2:
        myClient.HttpCmd(baseurl.getActionUrl('start', selection))
    if sel == 3:
        myClient.HttpCmd(baseurl.getActionUrl('stop', selection))
    if sel == 4:
        myClient.HttpCmd(baseurl.getActionUrl('forcestart', selection))
    if sel == 5:
        myClient.HttpCmd(baseurl.getActionUrl('remove', selection))
    if sel == 6:
        myClient.HttpCmd(baseurl.getActionUrl('removedata', selection))
    if sel == 7:
        files = getFiles(selection)
        if len(files) > 1: 
             xbmc.Player().play(baseurl.getProxyUrl(sid, str(dialog.select(__language__(32202), files))) + '|auth=any')
        else:
             xbmc.Player().play(baseurl.getProxyUrl(sid, '0') + '|auth=any')
    xbmc.executebuiltin('Container.Refresh')

def pauseAll():
    updateList()
    token = getToken()
    selected_label = app.get_param('label')
    if selected_label:
        selected_label = selected_label.decode('utf8')
    if app.get_param('no_label'):
        selected_label = ''
    for tor in torrentList.items:
        if UT_LABEL and selected_label != tor.label:
            continue
        myClient.HttpCmd(baseurl.getActionUrl('pause', tor.hashnum))
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def resumeAll():
    updateList()
    token = getToken()
    selected_label = app.get_param('label')
    if selected_label:
        selected_label = selected_label.decode('utf8')
    if app.get_param('no_label'):
        selected_label = ''
    for tor in torrentList.items:
        if UT_LABEL and selected_label != tor.label:
            continue
        myClient.HttpCmd(baseurl.getActionUrl('unpause', tor.hashnum))
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def stopAll():
    updateList()
    token = getToken()
    selected_label = app.get_param('label')
    if selected_label:
        selected_label = selected_label.decode('utf8')
    if app.get_param('no_label'):
        selected_label = ''
    for tor in torrentList.items:
        if UT_LABEL and selected_label != tor.label:
            continue
        myClient.HttpCmd(baseurl.getActionUrl('stop', tor.hashnum))
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def startAll():
    updateList()
    token = getToken()
    selected_label = app.get_param('label')
    if selected_label:
        selected_label = selected_label.decode('utf8')
    if app.get_param('no_label'):
        selected_label = ''
    for tor in torrentList.items:
        if UT_LABEL and selected_label != tor.label:
            continue
        myClient.HttpCmd(baseurl.getActionUrl('start', tor.hashnum))
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def limitSpeeds():
    dialog = xbmcgui.Dialog()
    upLimit = dialog.numeric(0, __language__(32009))
    downLimit = dialog.numeric(0, __language__(32010))
    opt = ''
    if upLimit != None:
        opt = '&s=max_ul_rate&v='+upLimit
    if downLimit != None:
        opt = opt + '&s=max_dl_rate&v='+downLimit
    if opt != '':
        token = getToken()
        #url = baseurl + token + '&action=setsetting&s=max_ul_rate&v='+upLimit+'&s=max_dl_rate&v='+downLimit
        url = baseurl.getActionUrl('setsetting') + opt
        myClient.HttpCmd(url)

def addFiles():
    MyTorrents = UT_TDIR
    if not os.path.exists(MyTorrents):
        return
    tlist = os.listdir(MyTorrents)
    for TorrentFile in tlist:
        if '.torrent' in TorrentFile:
            ## Read file data..
            realfile = os.path.join(MyTorrents, TorrentFile)
            xbmc.log( "%s::addFiles - %s" % ( __addonname__, realfile ), xbmc.LOGDEBUG )
            f = open(realfile, 'rb')
            fdata = f.read()
            f.close()
            ## Create post data..
            Contentx,Postx = MultiPart([],[['torrent_file',TorrentFile,fdata]],'torrent')
            if Contentx == None and Postx == None   :   raise Exception

            ## Now Action the command..?action=add-file
            token = getToken()
            Response = myClient.HttpCmd(baseurl.getActionUrl('add-file'), postdta=Postx, content=Contentx)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')


def getThumbByStatus(status):
    thumb = os.path.join(__icondir__, 'unknown.png')
    if status in (169, 232, 233):
        thumb = os.path.join(__icondir__, 'pause.png')
    elif status in (130, 137, 200, 201):
        thumb = os.path.join(__icondir__, 'play.png')
    elif status in (128, 136):
        thumb = os.path.join(__icondir__, 'stop.png')
    elif status == 200:
        thumb = os.path.join(__icondir__, 'queued.png')
    return thumb


def addDir(tor, selected_label):
    if selected_label:
        selected_label = selected_label.encode('utf8')
    thumb = getThumbByStatus(tor.status)

    label = tor.name+" [COLOR FFFF0000]" \
         + __language__(30001).encode('utf8')+"[/COLOR]"+str(tor.complete)+"% [COLOR FF00FF00]" \
         + __language__(30002).encode('utf8')+"[/COLOR]"+tor.size_str+" [COLOR FFFFFF00]" \
         + __language__(30003).encode('utf8')+"[/COLOR]"+str(tor.down_rate)+"Kb/s [COLOR FF00FFFF]" \
         + __language__(30004).encode('utf8')+"[/COLOR]"+str(tor.up_rate)+"Kb/s [COLOR FFFF00FF]" \
         + __language__(30005).encode('utf8')+"[/COLOR]"+tor.remain_str

    u = urllib.urlencode({
        'mode': App.MODE_ACTION_MENU,
        'name': tor.name,
        'hashNum': tor.hashnum,
        'sid': tor.stream_id
    })
    u = sys.argv[0] + '?' + u
    point = xbmcgui.ListItem(label,thumbnailImage=thumb)

    def action(mode):
        return "XBMC.RunPlugin(" + sys.argv[0] + "?" + urllib.urlencode({
            'mode': mode,
            'label': selected_label,
            'no_label': '1' if not selected_label else ''
        }) + ")"

    point.addContextMenuItems([
        (__language__(32011), action(App.MODE_PAUSE_ALL)),
        (__language__(32012), action(App.MODE_RESUME_ALL)),
        (__language__(32013), action(App.MODE_STOP_ALL)),
        (__language__(32014), action(App.MODE_START)),
        (__language__(32015), action(App.MODE_LIMIT_SPEED)),
        (__language__(32016), action(App.MODE_ADD_FILES))
    ], replaceItems=True)
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=point, isFolder=False)

url = app.get_param('url')
name = app.get_param('name')
mode = app.get_mode()

if mode == App.MODE_LIST:
    listTorrents()
elif mode == App.MODE_PAUSE_ALL:
    pauseAll()
elif mode == App.MODE_RESUME_ALL:
    resumeAll()
elif mode == App.MODE_STOP_ALL:
    stopAll()
elif mode == App.MODE_START:
    startAll()
elif mode == App.MODE_LIMIT_SPEED:
    limitSpeeds()
elif mode == App.MODE_ADD_FILES:
    addFiles()
elif mode == App.MODE_ACTION_MENU:
    hashNum = app.get_param('hashNum')
    sid = app.get_param('sid')
    performAction(hashNum,sid)
else:
    listTorrents()
