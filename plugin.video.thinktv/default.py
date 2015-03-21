# -*- coding: utf-8 -*-
# ThinkTV PBS XBMC Addon
#
# To do: add featured, popular programs to all and a to z.

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os, string
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import cgi, gzip
from StringIO import StringIO
import json


UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.thinktv')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString


home          = addon.getAddonInfo('path').decode(UTF8)
media         = xbmc.translatePath(os.path.join(home, 'resources', 'media'))
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))

icon_featured = xbmc.translatePath(os.path.join(media, 'featured.png'))
icon_popular  = xbmc.translatePath(os.path.join(media, 'popular.png'))
icon_a_to_z   = xbmc.translatePath(os.path.join(media, 'a_to_z.png'))
icon_all_prog = xbmc.translatePath(os.path.join(media, 'all_programs.png'))
icon_search   = xbmc.translatePath(os.path.join(media, 'search.png'))
icon_next     = xbmc.translatePath(os.path.join(media, 'next.png'))
pkicon        = xbmc.translatePath(os.path.join(media, 'PBS_Kids_ICON.png'))
pkfanart      = xbmc.translatePath(os.path.join(media, 'PBS_Kids_Fanart.jpg'))

qp  = urllib.quote_plus
uqp = urllib.unquote_plus

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanname(name):    
    return name.replace('&apos;',"'").replace('&#8217;',"'").replace('&amp;','&').replace('&#39;',"'").replace('&quot;','"')

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'
defaultHeaders = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 

def getRequest(url, user_data=None, headers = defaultHeaders , alert=True):

              log("getRequest URL:"+str(url))
              if addon.getSetting('us_proxy_enable') == 'true':
                  us_proxy = 'http://%s:%s' % (addon.getSetting('us_proxy'), addon.getSetting('us_proxy_port'))
                  proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
                  if addon.getSetting('us_proxy_pass') <> '' and addon.getSetting('us_proxy_user') <> '':
                      log('Using authenticated proxy: ' + us_proxy)
                      password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                      password_mgr.add_password(None, us_proxy, addon.getSetting('us_proxy_user'), addon.getSetting('us_proxy_pass'))
                      proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
                      opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
                  else:
                      log('Using proxy: ' + us_proxy)
                      opener = urllib2.build_opener(proxy_handler)
              else:   
                  opener = urllib2.build_opener()
              urllib2.install_opener(opener)

              log("getRequest URL:"+str(url))
              req = urllib2.Request(url.encode(UTF8), user_data, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()

              except urllib2.URLError, e:
                 if alert:
                     xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__, e , 10000) )
                 link1 = ""

              if not (str(url).endswith('.zip')):
                 link1 = str(link1).replace('\n','')
              return(link1)


def getSources(fanart):
              url = '0ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              dolist = [('GF', 30017, icon_featured),('GP', 30016, icon_popular),('GA', 30012, icon_all_prog), 
                        ('GZ', 30013, icon_a_to_z), ('GQ', 30014, icon_search), ('GKS', 30015, pkicon)]

              for mode, gstr, img in dolist:
                  name = __language__(gstr)
                  liz  = xbmcgui.ListItem(name,'',img,img)
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&mode=%s' % (sys.argv[0],qp(url), mode), liz, True)


def getQuery(cat_url):
        keyb = xbmc.Keyboard('', __addonname__)
        keyb.doModal()
        if (keyb.isConfirmed()):
              qurl = qp('/search/?q=%s' % (keyb.getText()))
              getCats(qurl, '')

def getFeatured(gzurl):
              ilist = []
              pg = getRequest('http://video.pbs.org/programs/')
              a = re.compile('\("#programsCarousel"\)\.programCarousel\(.+?\:(.+?)\);',re.DOTALL).search(pg).group(1)
              a = '{"data":'+a
              b = json.loads(a)
              b = b['data']
              a = re.compile('<ul id="carouselProgramList"(.+?)</ul>', re.DOTALL).search(pg).group(1)
              c = re.compile('<li.+?href="(.+?)".+?src="(.+?)".+?alt="(.+?)".+?</li>', re.DOTALL).findall(a)
              i = 0
              for url, img, name in c:
                     name = cleanname(name).encode(UTF8)
                     plot = b[i]['description']
                     plot = cleanname(plot).encode(UTF8)
                     fanart = b[i]['background']
                     i += 1
                     mode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s&imageicon=%s&desc=%s' % (sys.argv[0],qp(url), qp(name), mode, qp(img), qp(plot))
                     liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     liz.setProperty( "Fanart_Image", fanart )
                     ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
                

def getPopular(gzurl):
              ilist = []
              azheaders = defaultHeaders
              azheaders['X-Requested-With'] = 'XMLHttpRequest'
              pg = getRequest('http://video.pbs.org/programs/more',None, azheaders)
              a = json.loads(pg)
              b = a['programs_data']
              a = a['template']
              c = re.compile('<li.+?href="(.+?)".+?src="(.+?)".+?alt="(.+?)".+?</li>', re.DOTALL).findall(a)
              i = 0
              for url, img, name in c:
                     name = cleanname(name).encode(UTF8)
                     plot = b[i]['description']
                     plot = cleanname(plot).encode(UTF8)
                     i += 1
                     mode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s&imageicon=%s&desc=%s' % (sys.argv[0],qp(url), qp(name), mode, qp(img), qp(plot))
                     liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     ilist.append((u, liz, True))
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
                
def showAtoZ(azurl):
        ilist = []
        for a in azurl:
              name = a
              plot = ''
              url  = a
              mode = 'GA'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon)
              liz.setInfo( 'Video', { "Title": name, "Plot": plot })
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

                
def getAtoZ(gzurl):
              ilist = []
              azheaders = defaultHeaders
              azheaders['X-Requested-With'] = 'XMLHttpRequest'
              pg = getRequest('http://video.pbs.org/programs/list',None, azheaders)
              a = json.loads(pg)
              for y in gzurl:
                try:
                  b = a[y]
                  for x in b:
                     fullname = cleanname('%s [%s]' %(x['title'], x['video_count'])).encode(UTF8)
                     name = cleanname(x['title']).encode(UTF8)
                     plot = cleanname(x['producer']).encode(UTF8)
                     url = ('program/%s' % (x['slug'])).encode(UTF8)
                     mode = 'GV'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(fullname, '','DefaultFolder.png', icon)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     ilist.append((u, liz, True))
                except:
                  pass
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getVids(gvurl,catname, img=None, plot=None):
              if img  == None:
                 img = icon
              else:
                 img = uqp(img)
              gvurl = uqp(gvurl)
              pg = getRequest('http://video.pbs.org/%s' % (gvurl))
              dolist = [('episodes','<h2>Full Episodes',30020), ('shorts','<h2>Clips', 30021), ('previews', '<h2>Previews', 30022)]
              for gtype, gfind, gindex in dolist:
                if gfind in pg:
                  url = '%s/%s/' % (gvurl, gtype)
                  name = __language__(gindex)
                  if plot == None:
                     plot = name
                  else:
                     plot = uqp(plot)

                  mode = 'GC'
                  liz  = xbmcgui.ListItem(name,'',img,img)
                  liz.setInfo( 'Video', { "Title": catname, "Plot": plot })
                  xbmcplugin.addDirectoryItem(int(sys.argv[1]), '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), catname, mode), liz, True)


def getCats(gcurl, catname):
              ilist = []
              gcurl = uqp(gcurl)
              if 'search/?q=' in gcurl:
                chsplit = '&'
                gcurl = gcurl.replace(' ','+')
              else:
                chsplit = '?'
              pg = getRequest('http://video.pbs.org/%s' % (gcurl))
              epis = re.compile('data-videoid="(.+?)".+?data-title="(.+?)".+?src="(.+?)".+?class="description">(.+?)<(.+?)</li>').findall(pg)
              for url,name,img,desc,dur in epis:
                     if 'class="duration"' in dur:
                        dur = re.compile('<p class="duration">(.+?)</p>').search(dur).group(1)
                        dur = dur.strip()
                        if ':' in dur:
                          durs = dur.split(':',1)
                          dur = int(durs[0])
                          if ':' in durs[1]:
                             durs = durs[1].split(':',1)
                             dur = (dur*60)+int(durs[0])
                          dur = str(dur)
                     else:
                        dur = ''
                     name = cleanname(name)
                     plot = cleanname(desc)
                     mode = 'GS'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
                     liz.setInfo( 'Video', { "Title": name, "Studio" : catname, "Plot": plot, "Duration": dur})
                     liz.setProperty('IsPlayable', 'true')
                     ilist.append((u, liz, False))
              try:
                  nps = re.compile('visiblePage"><a href="(.+?)">(.+?)<').findall(pg)
                  (url, name) = nps[len(nps)-1]
                  if name == 'Next':
                     url = url.split(chsplit,1)[1]
                     url = qp(gcurl.split(chsplit,1)[0]+chsplit+url)
                     name = '[COLOR blue]%s[/COLOR]' % name
                     plot = name
                     mode = 'GC'
                     u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(name), mode)
                     liz=xbmcgui.ListItem(name, '','DefaultFolder.png', icon_next)
                     liz.setInfo( 'Video', { "Title": name, "Plot": plot })
                     ilist.append((u, liz, True))
              except:
                  pass
              xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))


def getShow(gsurl):
              pg = getRequest('http://video.pbs.org/videoInfo/%s/?format=json' % (uqp(gsurl)))
              a  =  json.loads(pg)
              suburl = a['closed_captions_url']
              log("suburl = "+str(suburl))
              url = a['recommended_encoding']['url']
              pg = getRequest('%s?format=json' % url)
              url = json.loads(pg)['url']
              if ('.m3u8' in url) and addon.getSetting('vid_res') == '1':
                 try:
                   url = url.split('hls-64-800k',1)[0]
                   url += 'hls-2500k.m3u8'
                 except:
                   pass
              xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))

              if (suburl != "") and ('dfxp' in suburl) and (addon.getSetting('sub_enable') == "true"):
                 profile = addon.getAddonInfo('profile').decode(UTF8)
                 subfile = xbmc.translatePath(os.path.join(profile, 'PBSSubtitles.srt'))
                 prodir  = xbmc.translatePath(os.path.join(profile))
                 if not os.path.isdir(prodir):
                    os.makedirs(prodir)

                 pg = getRequest(suburl)
                 if pg != "":
                   ofile = open(subfile, 'w+')
                   captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>').findall(pg)
                   idx = 1
                   for cstart, cend, caption in captions:
                     cstart = cstart.replace('.',',')
                     cend   = cend.replace('.',',').split('"',1)[0]
                     caption = caption.replace('<br/>','\n').replace('&gt;','>')
                     ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
                     idx += 1
                   ofile.close()
                   xbmc.sleep(5000)
                   xbmc.Player().setSubtitles(subfile)

def getPBSKidsShows():
        ilist=[]
        pg = getRequest('http://pbskids.org/pbsk/video/api/getShows/?callback=&destination=national&return=images')
        pg = pg.strip('()')
        a = json.loads(pg)['items']
        for b in a:
              name = b['title']
              plot = b['description']
              url  = b['cove_slug']
              ages = 'Ages %s' % b['age_range']
              img = b['images']['program-kids-square']['url']
              mode = 'GKC'
              u = '%s?url=%s&name=%s&mode=%s&img=%s' % (sys.argv[0],qp(url), qp(name), mode, qp(img))
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": name, "Studio": ages, "Plot": plot })
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def getPBSKidsCats(kcurl, kcname, img):
        ilist=[]
        dolist = [('episode', 30020), ('clip', 30021)]
        for kctype, iname in dolist:
              name = __language__(iname)
              url = 'http://pbskids.org/pbsk/video/api/getVideos/?callback=&startindex=1&endindex=200&program=%s&type=%s&category=&group=&selectedID=&status=available&player=flash&flash=true' % (kcname.replace('-',' ').replace('&','&amp;'), kctype)
              mode = 'GKV'
              u = '%s?url=%s&name=%s&mode=%s' % (sys.argv[0],qp(url), qp(kcname), mode)
              liz=xbmcgui.ListItem(name, '','DefaultFolder.png', img)
              liz.setInfo( 'Video', { "Title": kcname, "Plot": name })
              ilist.append((u, liz, True))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))
          
def getPBSKidsVids(kvurl,kvname):
        ilist=[]
        pg = getRequest(uqp(kvurl).replace(' ','+').replace('&amp;','%26'))
        pg = pg.strip('()')
        a = json.loads(pg)['items']
        for b in a:
               name = b['title']
               plot = b['description']
               img  = b['images']['kids-mezzannine-16x9']['url']
               try:
                 captions = b['captions']['srt']['url']
               except:
                 captions = ''
               try:
                  url = b['videos']['flash']['mp4-2500k']['url']
               except:
                  try:
                     url = b['videos']['flash']['mp4-1200k']['url']
                  except:
                     url = b['videos']['flash']['url']
               mode = 'PKP'
               u = '%s?url=%s&captions=%s&mode=%s' % (sys.argv[0],qp(url),qp(captions), mode)

               liz=xbmcgui.ListItem(name, plot,'DefaultFolder.png', img)
               liz.setInfo( 'Video', { "Title": name, "Studio" : kvname, "Plot": plot})
               liz.setProperty('IsPlayable', 'true')
               ilist.append((u, liz, False))
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), ilist, len(ilist))

def playPBSKidsVid(purl, captions):
        html = getRequest('%s?format=json' % uqp(purl))
        url = json.loads(html)['url']
        try:
             url = 'http://kids.video.cdn.pbs.org/videos/%s' % url.split(':videos/',1)[1]
        except:
             pass

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))
        if (captions != "") and (addon.getSetting('sub_enable') == "true"):
            xbmc.sleep(5000)
            xbmc.Player().setSubtitles(captions)

        



# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode',None)

if mode==  None:  getSources(p('fanart'))
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='GF':  getFeatured(p('url'))
elif mode=='GP':  getPopular(p('url'))
elif mode=='GA':  getAtoZ(p('url'))
elif mode=='GQ':  getQuery(p('url'))
elif mode=='GZ':  showAtoZ(p('url'))
elif mode=='GS':  getShow(p('url'))
elif mode=='GC':  getCats(p('url'),p('name'))
elif mode=='GV':  getVids(p('url'),p('name'),p('imageicon',None),p('desc',None))
elif mode=='GKS': getPBSKidsShows()
elif mode=='GKC': getPBSKidsCats(p('url'),p('name'),p('img'))
elif mode=='GKV': getPBSKidsVids(p('url'),p('name'))
elif mode=='PKP': playPBSKidsVid(p('url'),p('captions'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

