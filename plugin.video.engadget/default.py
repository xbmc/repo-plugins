import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.engadget')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
showicon = xbmc.translatePath( os.path.join( home, 'resources/show.png' ) )
nexticon = xbmc.translatePath( os.path.join( home, 'resources/next.png' ) )
videoq = __settings__.getSetting('video_quality')


def Categories():
        addDir(__language__(30000),'http://www.engadget.com/engadgetshow.xml',1,showicon)
        addDir(__language__(30001),'http://api.viddler.com/api/v2/viddler.videos.getByUser.xml?key=tg50w8nr11q8176liowh&user=engadget',2,icon)


def getEngadgetVideos(url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        videos = soup('video_list')[0]('video')
        page = int(soup('list_result')[0]('page')[0].string)+1
        for video in videos:
                name = video('title')[0].string
                link = video('html5_video_source')[0].string
                thumb = video('thumbnail_url')[0].string
                length = video('length')[0].string
                addLink(name,link,length,thumb)
        addDir(__language__(30006),'http://api.viddler.com/api/v2/viddler.videos.getByUser.xml?key=tg50w8nr11q8176liowh&user=engadget&page='+str(page),2,nexticon)


def getEngadgetShow(url):
        url = 'http://www.engadget.com/engadgetshow.xml'
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        episodes = soup('item')
        for episode in episodes:
                url = episode('enclosure')[0]['url']
                title = episode('enclosure')[0]('itunes:subtitle')[0].string
                duration = episode('enclosure')[0]('itunes:duration')[0].string
                thumbnail = 'http://www.blogcdn.com/www.engadget.com/media/2009/09/show_front_sm.jpg'
                if videoq == '0':
                        url=url.replace('900.mp4','500.mp4')
                elif videoq == '2':
                        url=url.replace('900.mp4','2500.mp4')
                else:
                        url=url
                addLink(title,url,duration,thumbnail,True)


class DownloadFiles:
        def __init__(self):
                url = sys.argv[2]
                filename = sys.argv[3]
                def download(url, dest):
                        dialog = xbmcgui.DialogProgress()
                        dialog.create(__language__(30015),__language__(30016), filename)
                        urllib.urlretrieve(url, dest, lambda nb, bs, fs, url = url: _pbhook(nb, bs, fs, url, dialog))
                def _pbhook(numblocks, blocksize, filesize, url = None,dialog = None):
                        try:
                                percent = min((numblocks * blocksize * 100) / filesize, 100)
                                dialog.update(percent)
                        except:
                                percent = 100
                                dialog.update(percent)
                        if dialog.iscanceled():
                                dialog.close()
                # check for a download location, if not open settings
                if (__settings__.getSetting('save_path') == ''):
                        __settings__.openSettings('save_path')
                # lets the user rename the file
                keyboard = xbmc.Keyboard(filename,__language__(30011))
                keyboard.doModal()
                if (keyboard.isConfirmed() == False):
                        return
                filename = keyboard.getText()
                if len(filename) == 0:
                        return
                filepath = xbmc.translatePath(os.path.join(__settings__.getSetting('save_path'),filename))
                download(url, filepath)
                if __settings__.getSetting('play') == "true":
                    play=xbmc.Player().play( xbmc.translatePath( os.path.join( __settings__.getSetting('save_path'), filename ) ))
                
                
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


def addLink(name,url,duration,iconimage,showcontext=True):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration":duration } )
        if showcontext:
                try:
                        filename = name.replace(':','-')+'.mp4'
                except:
                        pass
                contextMenu = [(__language__(30004),'XBMC.RunScript('+xbmc.translatePath( os.path.join( home, 'default.py' ) )+',download,'+url+','+filename+')')]
                liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def startPlugin():			
    params=get_params()
    url=None
    name=None
    mode=None

    try:
            url=urllib.unquote_plus(params["url"])
    except:
            pass
    try:
            name=urllib.unquote_plus(params["name"])
    except:
            pass
    try:
            mode=int(params["mode"])
    except:
            pass

    print "Mode: "+str(mode)
    print "URL: "+str(url)
    print "Name: "+str(name)

    if mode==None:
            print ""
            Categories()
            
    if mode==1:
            print""
            getEngadgetShow(url)
            
    if mode==2:
            print""
            getEngadgetVideos(url)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
if sys.argv[1] == 'download':
        DownloadFiles()
        
else:
        startPlugin()