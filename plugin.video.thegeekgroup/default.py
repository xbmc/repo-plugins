import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, os
from time import strftime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import StorageServer
from datetime import datetime
try:
    import json
except:
    import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.video.thegeekgroup')
__language__ = __settings__.getLocalizedString

def make_request(url):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://thegeekgroup.org'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log( 'We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: ', e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)

def get_jtv():
        soup = BeautifulSoup(make_request('http://usher.justin.tv/find/thegeekgroup.xml?type=live'))
        token = ' jtv='+soup.token.string.replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        rtmp = soup.connect.string+'/'+soup.play.string
        Pageurl = ' Pageurl=http://www.justin.tv/thegeekgroup'
        swf = ' swfUrl=http://www.justin.tv/widgets/live_embed_player.swf?channel=thegeekgroup live=true'
        url = rtmp+token+swf+Pageurl
        return url

def CATEGORIES():
    # List all the shows.
    shows = {}

    # TGG live stream
    addLink(
        name = __language__(30000),
        url = get_jtv(),
        date = '',
        iconimage = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'tgg.png'),
        info = {
            'title': __language__(30000),
            'plot': __language__(30200),
            'genre': 'Science & Technology',
            'count': 1
        }
    )

# Info takes Plot, date, size
def addLink(name, url, date, iconimage, info):
        ok=True
        liz=xbmcgui.ListItem(name, date, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="video", infoLabels=info )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

CATEGORIES()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
