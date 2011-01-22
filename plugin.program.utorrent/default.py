import urllib, sys, os, re, time
import xbmcaddon, xbmcplugin, xbmcgui, xbmc

# uTorrent Plugin v1.0.4

# Plugin constants 
__addonname__ = "uTorrent"
__addonid__ = "plugin.program.utorrent"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__language__ = __addon__.getLocalizedString
__cwd__ = __addon__.getAddonInfo('path')
__icondir__ = xbmc.translatePath(os.path.join(__cwd__,'resources','icons'))

# Shared resources 
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
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
    data = data.split('\n')
    torrentList = []
    for line in data:
        if '\"rssfeeds\"' in line:
            xbmc.log( "%s::updateList - %s" % ( __addonname__, 'break with \"rssfeeds\"' ), xbmc.LOGDEBUG )
            break
        if len(line) > 80:
            tor = re.findall('\"[^\"]*\"|[0-9\-]+', line)
            xbmc.log( "%s::updateList - %d: %s" % ( __addonname__, len(torrentList), str(tor) ), xbmc.LOGDEBUG )
            hashnum = tor[0][1:-1]
            status = tor[1]
            torname = tor[2]
            complete = tor[4]
            complete = int(complete)
            complete = complete / 10.0
            size = int(tor[3]) / (1024*1024)
            if (size >= 1024.00):
                size_str = str(round(size / 1024.00,2)) +"Gb"
            else:
                size_str = str(size) + "Mb"
            up_rate = round(float(tor[8]) / (1024),2)
            down_rate = round(float(tor[9]) / (1024),2)
            remain = int(tor[10]) / 60
            if (remain >=60):
                remain_str = str(remain//60) + __language__(30006).encode('utf8') + str(remain%60) + __language__(30007).encode('utf8')
            elif(remain == -1):
                remain_str = __language__(30008).encode('utf8')
            else:
                remain_str = str(remain) + __language__(30007).encode('utf8')
            tup = (hashnum, status, torname, complete, size_str, up_rate, down_rate,remain_str)
            torrentList.append(tup)
    return torrentList

def listTorrents():
    tupList = updateList()
    mode = 1
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str in tupList:
        if int(bw) in (169,232,233):
            thumb = os.path.join(__icondir__,'pause.png')
        elif int(bw) in (130,137,200,201):
            thumb = os.path.join(__icondir__,'play.png')
        elif int(bw) in (128,136):
            thumb = os.path.join(__icondir__,'stop.png')
        elif int(bw) == 200:
            thumb = os.path.join(__icondir__,'queued.png')
        else:
            thumb = os.path.join(__icondir__,'unknown.png')
        url = baseurl
        addDir(name+" "+__language__(30001).encode('utf8')+str(complete)+"% "+__language__(30002).encode('utf8')+size_str+" "+__language__(30003).encode('utf8')+ str(down_rate)+"Kb/s "+__language__(30004).encode('utf8')+str(up_rate)+"Kb/s "+__language__(30005).encode('utf8')+remain_str,url,mode,thumb,hashnum)
        mode = mode + 1
    xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=False)

def performAction(selection):
    dialog = xbmcgui.Dialog()
    sel = dialog.select(__language__(32001),[__language__(32002),__language__(32003),__language__(32004),__language__(32005),__language__(32006),__language__(32007),__language__(32008)])
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
    xbmc.executebuiltin('Container.Refresh')

def pauseAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str in tupList:
        token = getToken()
        url = baseurl + token + '&action=pause&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def resumeAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str in tupList:
        token = getToken()
        url = baseurl + token + '&action=unpause&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def stopAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str in tupList:
        token = getToken()
        url = baseurl + token + '&action=stop&hash='+hashnum
        myClient.HttpCmd(url)
    time.sleep(1)
    xbmc.executebuiltin('Container.Refresh')

def startAll():
    tupList = updateList()
    for hashnum, bw, name, complete,size_str, up_rate, down_rate,remain_str in tupList:
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

def addDir(name,url,mode,iconimage,hashNum):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&hashNum="+str(hashNum)
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
    performAction(hashNum)

