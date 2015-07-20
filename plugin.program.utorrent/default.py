import urllib, sys, os, re, time
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
baseurl = 'http://'+UT_ADDRESS+':'+UT_PORT+'/gui/?token='

from utilities import *

params = {
    'address': UT_ADDRESS,
    'port': UT_PORT,
    'user': UT_USER,
    'password': UT_PASSWORD
}
myClient = Client(**params)

def getToken():
    tokenUrl = 'http://'+UT_ADDRESS+':'+UT_PORT+'/gui/token.html'

    try:
        data = myClient.HttpCmd(tokenUrl)
    except:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__addonname__ + ' ' + __language__(32100).encode('utf8'), __language__(32101).encode('utf8'), __language__(32102).encode('utf8'))
        if ret==True:
            __addon__.openSettings()
        sys.exit()

    match = re.compile("<div id='token' style='display:none;'>(.+?)</div>").findall(data)
    token = match[0]

    return token

def updateList():
    token = getToken()
    url = baseurl + token + '&list=1'
    data = myClient.HttpCmd(url)
    torrentList = []
    data = unicode(data, 'utf-8', errors='ignore')
    json_response = simplejson.loads(data)
    for torrent in json_response['torrents']:
        xbmc.log( "%s::updateList - %d: %s" % ( __addonname__, len(torrentList), str(torrent) ), xbmc.LOGDEBUG )
        hashnum = torrent[0].encode('utf-8')
        status = torrent[1]
        torname = torrent[2].encode('utf-8')
        complete = torrent[4] / 10.0
        size = torrent[3] / (1024*1024)
        if (size >= 1024.00):
            size_str = str(round(size / 1024.00,2)) + "Gb"
        else:
            size_str = str(size) + "Mb"
        up_rate = round(torrent[8] / 1024, 2)
        down_rate = round(torrent[9] / 1024, 2)
        remain = torrent[10] / 60
        if (remain >=60):
            remain_str = str(remain//60) + __language__(30006).encode('utf8') + str(remain%60) + __language__(30007).encode('utf8')
        elif(remain == -1):
            remain_str = __language__(30008).encode('utf8')
        else:
            remain_str = str(remain) + __language__(30007).encode('utf8')
        try:
            sid = torrent[22]
        except:
            # old utorrent version, don't support stream
            sid = -1
        tup = (hashnum, status, torname, complete, size_str, up_rate, down_rate, remain_str, sid)
        torrentList.append(tup)
    torrentList.sort(key=lambda tor : tor[2])  # sort by torrent name
    return torrentList

def listTorrents():
    tupList = updateList()
    mode = 1
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str,sid in tupList:
        if bw in (169,232,233):
            thumb = os.path.join(__icondir__,'pause.png')
        elif bw in (130,137,200,201):
            thumb = os.path.join(__icondir__,'play.png')
        elif bw in (128,136):
            thumb = os.path.join(__icondir__,'stop.png')
        elif bw == 200:
            thumb = os.path.join(__icondir__,'queued.png')
        else:
            thumb = os.path.join(__icondir__,'unknown.png')
        url = baseurl
        addDir(name+" [COLOR FFFF0000]"
                +__language__(30001).encode('utf8')+"[/COLOR]"+str(complete)+"% [COLOR FF00FF00]"
                +__language__(30002).encode('utf8')+"[/COLOR]"+size_str+" [COLOR FFFFFF00]"
                +__language__(30003).encode('utf8')+"[/COLOR]"+str(down_rate)+"Kb/s [COLOR FF00FFFF]"
                +__language__(30004).encode('utf8')+"[/COLOR]"+str(up_rate)+"Kb/s [COLOR FFFF00FF]"
                +__language__(30005).encode('utf8')+"[/COLOR]"+remain_str,url,mode,thumb,hashnum,sid)
        mode = mode + 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)


def getFiles(hash):
    token = getToken()
    url = baseurl + token + '&action=getfiles&hash='+hash
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
        myClient.HttpCmd(baseurl+token+'&action=pause&hash='+selection)
    if sel == 1:
        myClient.HttpCmd(baseurl+token+'&action=unpause&hash='+selection)
    if sel == 2:
        myClient.HttpCmd(baseurl+token+'&action=start&hash='+selection)
    if sel == 3:
        myClient.HttpCmd(baseurl+token+'&action=stop&hash='+selection)
    if sel == 4:
        myClient.HttpCmd(baseurl+token+'&action=forcestart&hash='+selection)
    if sel == 5:
        myClient.HttpCmd(baseurl+token+'&action=remove&hash='+selection)
    if sel == 6:
        myClient.HttpCmd(baseurl+token+'&action=removedata&hash='+selection)
    if sel == 7:
        files = getFiles(selection)
        if len(files) > 1: 
             xbmc.Player().play('http://'+UT_USER+':'+UT_PASSWORD+'@'+UT_ADDRESS+':'+UT_PORT+'/proxy?sid='+sid+'&file='+str(dialog.select(__language__(32202),files)))
        else:
             xbmc.Player().play('http://'+UT_USER+':'+UT_PASSWORD+'@'+UT_ADDRESS+':'+UT_PORT+'/proxy?sid='+sid+'&file=0')
    xbmc.executebuiltin('Container.Refresh')

def pauseAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str,sid in tupList:
        token = getToken()
        url = baseurl + token + '&action=pause&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def resumeAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str,sid in tupList:
        token = getToken()
        url = baseurl + token + '&action=unpause&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def stopAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str,sid in tupList:
        token = getToken()
        url = baseurl + token + '&action=stop&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def startAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str,sid in tupList:
        token = getToken()
        url = baseurl + token + '&action=start&hash='+hashnum
        myClient.HttpCmd(url)
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
        url = baseurl + token + '&action=setsetting' + opt
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
            url = baseurl + token + '&action=add-file'
            Response = myClient.HttpCmd(url, postdta=Postx, content=Contentx)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param

def addDir(name,url,mode,iconimage,hashNum,sid):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&hashNum="+str(hashNum)+"&sid="+str(sid)
    ok = True
    point = xbmcgui.ListItem(name,thumbnailImage=iconimage)
    rp = "XBMC.RunPlugin(%s?mode=%s)"
    point.addContextMenuItems([(__language__(32011), rp % (sys.argv[0], 1000)),(__language__(32012), rp % (sys.argv[0], 1001)),(__language__(32013), rp % (sys.argv[0], 1002)),(__language__(32014), rp % (sys.argv[0], 1003)),(__language__(32015), rp % (sys.argv[0], 1004)),(__language__(32016), rp % (sys.argv[0], 1005))],replaceItems=True)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=point,isFolder=False)

params = get_params()
url = None
name = None
mode = 0
hashNum = None
sid = None

try:
    url = urllib.unquote_plus(params['url'])
except:
    pass
try:
    name = urllib.unquote_plus(params['name'])
except:
    pass
try:
    mode = int(params['mode'])
except:
    pass
try:
    hashNum = urllib.unquote_plus(params['hashNum'])
except:
    pass
try:
    sid = urllib.unquote_plus(params['sid'])
except:
    pass

if mode == 0:
    listTorrents()

elif mode == 1000:
    pauseAll()

elif mode == 1001:
    resumeAll()

elif mode == 1002:
    stopAll()

elif mode == 1003:
    startAll()

elif mode == 1004:
    limitSpeeds()

elif mode == 1005:
    addFiles()

elif 0 < mode < 1000:
    xbmc.log( "%s::main - hashNum: %s" % ( __addonname__, hashNum ), xbmc.LOGDEBUG )
    performAction(hashNum,sid)
