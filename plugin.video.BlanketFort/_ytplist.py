import urllib
import urllib2,json
import xbmcvfs
import requests,time
import os,xbmc,xbmcaddon,xbmcgui,re
addon = xbmcaddon.Addon('plugin.video.SimpleKore')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
cacheDir = os.path.join(profile, 'cachedir')
clean_cache=os.path.join(cacheDir,'cleancacheafter1month')
headers=dict({'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:32.0) Gecko/20100101 Firefox/32.0'})

if not cacheDir.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')) and not os.path.isdir(cacheDir):
    os.mkdir(cacheDir)
if xbmcvfs.exists(clean_cache) and (time.time()-os.path.getmtime(clean_cache) > 60*60*24*30):
    print 'time of creation of ff',str(time.time()-os.path.getmtime(clean_cache))
    import shutil
    shutil.rmtree(cacheDir)    
else:
    with open(clean_cache,'w') as f:
        f.write('') 
utubeid  = 'www.youtube.*?v(?:=|%3D)([0-9A-Za-z_-]{11})'
def YoUTube(page_data,youtube=None,duration=None,max_page=20,nosave=None):
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Updating list', 'Downloading ...') 
    base_yt_url  ='http://gdata.youtube.com/feeds/api'
    if 'search' in page_data:
        youtube = youtube.replace(' ','+')#Lana Del Rey
        build_url= base_yt_url + '/videos?q=%s&max-results=50&v=2&alt=json&orderby=published&start-index=%s'
        if  addon.getSetting('searchlongvideos') == 'true':            #duration: #medium or long
            build_url = base_yt_url + '/videos?q=%s&max-results=20&v=2&alt=json&duration=long&start-index=%s' 
      
    else:
        build_url = 'http://www.youtube.com/watch?v=%s' %page_data
    count = 1
    allurls ={}
    for i in range(1,max_page):
        url = build_url %(youtube,str(count))
        #print url
        try:
            content = cache(url,int(addon.getSetting("Youtube")))
            print len(content)
            
            jcontent = json.loads(content)
            entry = jcontent['feed']['entry']
        except Exception:
            break
        for myUrl in entry:
            count += 1
            allitem = 'item' + str(count)
            item = {}
            item['title']= removeNonAscii(myUrl['title']['$t']).encode('utf-8')
            item['date']= myUrl['published']['$t'].encode('utf-8')
            try:
                item['desc']= removeNonAscii(myUrl['media$group']['media$description']['$t']).encode('utf-8')
            except Exception:
                desc = 'UNAVAIABLE'
            link = myUrl['link'][0]['href'].encode('utf-8','ignore')
            item['url']= re_me(link,utubeid)
            allurls[allitem] = item
        print len(allurls)
    if nosave:
        return allurls
    pDialog.close()
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
def makeRequest(url,referer=None,post=None,body={}):

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
        