import sys
import urllib
import urllib2,cookielib,re
import StringIO
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import HTMLParser
import xbmcaddon
import os
import webbrowser
import os.path
import BeautifulSoup
import json

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
__addon__        = xbmcaddon.Addon()
__addonname__    = __addon__.getAddonInfo('id')
dataroot = xbmc.translatePath('special://profile/addon_data/%s' % __addonname__ ).decode('utf-8')
cookie_file = os.path.join( dataroot,'cookies.lwp')

if not os.path.exists(dataroot):
    os.makedirs(dataroot)

cookie_jar = cookielib.LWPCookieJar(cookie_file)

def debug(text):
    dbg_file = os.path.join( dataroot,'DEBUG.txt')
    text_file = open(dbg_file, "w+")
    text_file.write(text)
    text_file.close()

if not os.path.isfile(cookie_file):
    cookie_jar.save()

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

hdr = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
}

def getFeatured(content, mode, cType):
    url = "https://newgrounds.app/featured.cache.php"
    data = None

    req = urllib2.Request(url, data, hdr)
    response = urllib2.urlopen(req)
    r = json.loads(response.read())
    #xbmcgui.Dialog().ok('DEBUG', json.dumps(r))
    for fm in r[content]:
        #xbmcgui.Dialog().ok('DEBUG', fm['content_url'])
        url = build_url({'mode': mode, 'contentID': fm['content_url']})
        li = xbmcgui.ListItem(fm['title'], iconImage=fm['thumbnail_newgrounds_url'] + fm['thumbnail'])
        li.setInfo(cType, {'title': fm['title']})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def searchContent(content, mode, cType):
    if (int(args['page'][0]) > 1): #next page
        search = args['search_term'][0]
    else: #initial search
        kb = xbmc.Keyboard('', 'search')
        kb.doModal()
        if kb.isConfirmed():
            search = kb.getText()

    nextPage = int(args['page'][0]) + 1
    url = "https://newgrounds.app/browse.cache.php?type=" + content + "&s=" + search + "&page=" + args['page'][0]
    data = None

    req = urllib2.Request(url, data, hdr)
    response = urllib2.urlopen(req)
    r = json.loads(response.read())
    for fm in r['browse_content']:
        url = build_url({'mode': mode, 'contentID': fm['content_url']})
        li = xbmcgui.ListItem(fm['title'], iconImage=fm['thumbnail_newgrounds_url'] + fm['thumbnail'])
        li.setInfo(cType, {'title': fm['title']})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': mode, 'page': nextPage, 'search_term': search})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def browseContent(content, mode, cType):
    nextPage = int(args['page'][0]) + 1
    url = "https://newgrounds.app/browse.cache.php?type=" + content + "&g=" + args['cat'][0] + "&page=" + args['page'][0]
    data = None

    req = urllib2.Request(url, data, hdr)
    response = urllib2.urlopen(req)
    r = json.loads(response.read())
    for fm in r['browse_content']:
        url = build_url({'mode': mode, 'contentID': fm['content_url']})
        li = xbmcgui.ListItem(fm['title'], iconImage=fm['thumbnail_newgrounds_url'] + fm['thumbnail'])
        li.setInfo(cType, {'title': fm['title']})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': mode, 'cat': args['cat'][0], 'page': nextPage})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

audioCats = { 'all','easy-listening','classical','jazz','solo-instrument','electronic','ambient','chipstep','dance','drum-n-bass',
                   'dubstep','house','industrial','new-wave','techno','trance','video-game','hip-hop-rap-rb','hip-hop---modern','hip-hop---olskool',
                   'nerdcore','rb','metal-rock','brit-pop','classic-rock','general-rock','grunge','heavy-metal','indie','pop','punk','other','cinematic',
                   'experimental','funk','fusion','goth','miscellaneous','ska','world','southern-flavor','bluegrass','blues','country','voice-acting',
                   'a-capella','comedy','drama','informational','spoken-word','voice-demo' }

videoCats = { 'action','comedy','comedy-original','comedy-parody','drama','experimental','informative','music-video','other','spam' }

artCats = {"all", "illustration", "fine-art", "3d-art", "pixel-art", "other"}

if mode is None:

    url = build_url({'mode': 'featured_audio'})
    li = xbmcgui.ListItem('[COLOR orange]Featured Audio[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'audio_catlist'})
    li = xbmcgui.ListItem('[COLOR orange]Browse Audio Portal[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_audio', 'page': 1, 'search_term': ' '})
    li = xbmcgui.ListItem('[COLOR orange]Search Audio Portal[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'featured_video'})
    li = xbmcgui.ListItem('[COLOR blue]Featured Videos[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'video_catlist'})
    li = xbmcgui.ListItem('[COLOR blue]Browse Video Portal[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_video', 'page': 1, 'search_term': ' '})
    li = xbmcgui.ListItem('[COLOR blue]Search Video Portal[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'featured_art'})
    li = xbmcgui.ListItem('[COLOR yellow]Featured Art[/COLOR]', iconImage='DefaultPicture.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'art_catlist', 'page': 1})
    li = xbmcgui.ListItem('[COLOR yellow]Browse Art Portal[/COLOR]', iconImage='DefaultPicture.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_art', 'page': 1, 'search_term': ' '})
    li = xbmcgui.ListItem('[COLOR yellow]Search Art Portal[/COLOR]', iconImage='DefaultPicture.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'audio_catlist':
    for cat in sorted(audioCats):
        url = build_url({'mode': 'audio_list', 'cat': cat, 'page': 1})
        li = xbmcgui.ListItem(cat, iconImage='DefaultAudio.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'video_catlist':
    for cat in sorted(videoCats):
        url = build_url({'mode': 'video_list', 'cat': cat, 'page': 1})
        li = xbmcgui.ListItem(cat, iconImage='DefaultVideo.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'art_catlist':
    for cat in sorted(artCats):
        url = build_url({'mode': 'art_list', 'cat': cat, 'page': 1})
        li = xbmcgui.ListItem(cat, iconImage='DefaultVideo.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'featured_video':
    getFeatured('featured_movies', 'video_info', 'video')

elif mode[0] == 'featured_audio':
    getFeatured('featured_audio', 'audio_info', 'audio')

elif mode[0] == 'featured_art':
    getFeatured('featured_art', 'art_info', 'art')

elif mode[0] == 'search_audio':
    searchContent('audio', 'audio_info', 'search_audio')

elif mode[0] == 'search_video':
    searchContent('movies', 'video_info', 'search_video')

elif mode[0] == 'search_art':
    searchContent('art', 'art_info', 'search_art')

elif mode[0] == 'art_list':
    browseContent('art', 'art_info', 'art_list')

elif mode[0] == 'video_list':
    browseContent('movies', 'video_info', 'video_list')

elif mode[0] == 'audio_list':
    browseContent('audio', 'audio_info', 'audio_list')

elif mode[0] == 'video_info':
    xbmc.Player().play(args['contentID'][0])

elif mode[0] == 'audio_info':
    xbmc.Player().play(args['contentID'][0])

elif mode[0] == 'art_info':
    xbmc.executebuiltin('ShowPicture(' + args['contentID'][0] + ')') 
