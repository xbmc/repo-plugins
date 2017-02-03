import urllib
import urllib2
import xbmcvfs
import os,xbmc,xbmcaddon,xbmcgui,re,xbmcplugin,sys
import json
import datetime
addon = xbmcaddon.Addon('plugin.video.SimpleKore')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
cacheDir = os.path.join(profile, 'cachedir')
headers=dict({'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:32.0) Gecko/20100101 Firefox/32.0'})

if not cacheDir.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')) and not os.path.isdir(cacheDir):
    os.mkdir(cacheDir)

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext,duration,total):
        contextMenu = []
        url = 'plugin://plugin.video.dailymotion_com/?mode=playVideo&url='+url
        print 'adding link'
        try:
            name = name.encode('utf-8')
        except: pass
        ok = True
        mode = '12'
        contextMenu.append(('[COLOR white]!!Download Currently Playing!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
                            %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))             
            
        u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
      
        if date == '':
            date = None
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description,"Aired": date, "Genre": genre, "Duration": duration })
        liz.setProperty("Fanart_Image", fanart)
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)
        return ok    
 # Thanks to AddonScriptorde
 #https://github.com/AddonScriptorDE/plugin.video.dailymotion_com/blob/master/default.py#L174
def listVideos(url):
    content = cache(url,int(addon.getSetting("dmotion")))
    content = json.loads(content)
    count = 1
    for item in content['list']:
        id = item['id']
        title = item['title'].encode('utf-8')
        desc = item['description'].encode('utf-8')
        duration = item['duration']
        user = item['owner.username']
        date = item['taken_time']
        thumb = item['thumbnail_large_url']
        views = item['views_total']
        duration = str(int(duration)/60+1)
        try:
            date = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
        except:
            date = ""
        temp = ("User: "+user+" | "+str(views)+" Views | "+date).encode('utf-8')
        try:
            desc = temp+"\n"+desc
        except:
            desc = ""
        if user == "hulu":
            pass
        elif user == "cracklemovies":
            pass
        else:
            addLink(id, title,thumb.replace("\\", ""),'', desc, user, date,'',duration,  count)
            count+=1

def re_me(data, re_patten):
    match = ''
    m = re.search(re_patten, data,re.I)
    if m != None:
        match = m.group(1)
    else:
        match = ''
    return match    
def notification(header="", message="", sleep=3000):
    """ Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i)" % ( header, message, sleep ))     
def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))
def makeRequest(url,referer=None):

    if referer:
        headers.update=({'Referer':referer})
    else:
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
# from AddonScriptorde X:\plugin.video.my_music_tv\default.py
def cache(url, duration=0):
    cacheFile = os.path.join(cacheDir, (''.join(c for c in unicode(url, 'utf-8') if c not in '/\\:?"*|<>')).strip())
    if os.path.exists(cacheFile) and duration!=0 and (time.time()-os.path.getmtime(cacheFile) < 60*60*24*duration):
        fh = xbmcvfs.File(cacheFile, 'r')
        content = fh.read()
        fh.close()
        return content
    else:
        content = makeRequest(url)
        fh = xbmcvfs.File(cacheFile, 'w')
        fh.write(content)
        fh.close()
        return content
       