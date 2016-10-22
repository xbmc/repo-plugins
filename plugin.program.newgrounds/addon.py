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

def get_request(url, data=None):
    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    # Debug
    req = urllib2.Request(url, data, hdr)
    response = urllib2.urlopen(req)
    data = response.read()
    cookie_jar.save(cookie_file, ignore_discard=True, ignore_expires=False)
    response.close()
    return data

def readURL (url):
    values = { }
    if xbmcplugin.getSetting(addon_handle,'everyone') == 'true':
        values.update({'view_suitability_e' : 'on'})
    if xbmcplugin.getSetting(addon_handle,'teen') == 'true':
        values.update({'view_suitability_t' : 'on'})
    if xbmcplugin.getSetting(addon_handle,'mature') == 'true':
        values.update({'view_suitability_m' : 'on'})
    if xbmcplugin.getSetting(addon_handle,'adult') == 'true':
        values.update({'view_suitability_a' : 'on'})

    #xbmcgui.Dialog().ok('DEBUG', xbmcplugin.getSetting(addon_handle,'adult'))

    cookie_jar.load(cookie_file, ignore_discard=True, ignore_expires=True)
    COOKIEHANDLER = urllib2.HTTPCookieProcessor(cookie_jar) 
    OPENER = urllib2.build_opener(COOKIEHANDLER)

    REQ = urllib2.Request(url, headers=hdr)

    RESPONSE = OPENER.open(REQ,urllib.urlencode(values))

    return RESPONSE.read()

def login ():
    url = 'https://www.newgrounds.com/passport/mode/iframe/appsession'

    if 'You have successfully signed in!' in get_request(url):
        #xbmcgui.Dialog().ok('DEBUG', 'we are already logged in')
        return 'You have successfully signed in!'

    values = {
        'username' : xbmcplugin.getSetting(addon_handle,'username'),
        'password' : xbmcplugin.getSetting(addon_handle,'password'),
        'remember' : '1'
    }

    #try:
    #    page = urllib2.urlopen(req)
    #except urllib2.HTTPError, e:
    #    xbmcgui.Dialog().ok('ERROR', e.fp.read())
    return get_request(url, urllib.urlencode(values))

audioCats = { 'all','easy-listening','classical','jazz','solo-instrument','electronic','ambient','chipstep','dance','drum-n-bass',
                   'dubstep','house','industrial','new-wave','techno','trance','video-game','hip-hop-rap-rb','hip-hop---modern','hip-hop---olskool',
                   'nerdcore','rb','metal-rock','brit-pop','classic-rock','general-rock','grunge','heavy-metal','indie','pop','punk','other','cinematic',
                   'experimental','funk','fusion','goth','miscellaneous','ska','world','southern-flavor','bluegrass','blues','country','voice-acting',
                   'a-capella','comedy','drama','informational','spoken-word','voice-demo' }

videoCats = { 'action','comedy','comedy-original','comedy-parody','drama','experimental','informative','music-video','other','spam' }

if mode is None:
    login() #debug code below if needed
    #if 'You have successfully signed in!' in login():
    #    xbmcgui.Dialog().ok('DEBUG', 'logged in!')

    #li = xbmcgui.ListItem('[B]-- AUDIO PORTAL --[/B]', iconImage='DefaultAudio.png')
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url='#', listitem=li, isFolder=False)

    url = build_url({'mode': 'featured_audio'})
    li = xbmcgui.ListItem('[COLOR orange]Featured Audio[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'audio_catlist'})
    li = xbmcgui.ListItem('[COLOR orange]Browse Audio Portal[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_audio', 'page': 1, 'search_term': ' '})
    li = xbmcgui.ListItem('[COLOR orange]Search Audio Portal[/COLOR]', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    #li = xbmcgui.ListItem('[B]-- VIDEO PORTAL --[/B]', iconImage='DefaultVideo.png')
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url='#', listitem=li, isFolder=False)

    url = build_url({'mode': 'featured_video'})
    li = xbmcgui.ListItem('[COLOR blue]Featured Videos[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'video_catlist'})
    li = xbmcgui.ListItem('[COLOR blue]Browse Video Portal[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_video', 'page': 1, 'search_term': ' '})
    li = xbmcgui.ListItem('[COLOR blue]Search Video Portal[/COLOR]', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    #li = xbmcgui.ListItem('[B]-- ART PORTAL --[/B]', iconImage='DefaultPicture.png')
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url='#', listitem=li, isFolder=False)

    url = build_url({'mode': 'featured_art'})
    li = xbmcgui.ListItem('[COLOR yellow]Featured Art[/COLOR]', iconImage='DefaultPicture.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'art_list', 'page': 1})
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

elif mode[0] == 'search_audio':
    name = ''
    if int(args['page'][0]) > 1:
        name = args['search_term'][0]
    else:
        kb = xbmc.Keyboard('', 'search')
        kb.doModal()
        if kb.isConfirmed():
            name = kb.getText()
            #xbmcgui.Dialog().ok('DEBUG', name)

    content = readURL('http://www.newgrounds.com/audio/search/title/' + urllib.quote_plus(name) + '/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<li><div class="audio-wrapper">(.*?)<\/li>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        image = re.compile('\img src="([^"]+)"').findall(newContent)
        audioID = re.compile('href="\/audio\/listen\/([^"]+)"').findall(newContent)
        artist = re.compile('<strong>([^"]*)<\/strong>').findall(newContent)
        title = re.compile('<h4>([^"]*)<\/h4>').findall(newContent)

        theTitle = title[0]
        try:
		    theArtist = artist[0]
        except IndexError:
		    theArtist = "N/A"

        try:
		    theImage = image[0]
        except IndexError:
		    theImage = "http://img.ngfiles.com/defaults/icon-audio-smaller.png"

        for aID in audioID:
            url = build_url({'mode': 'audio_info', 'audioID': aID})
            li = xbmcgui.ListItem(theTitle + ' by ' + theArtist, iconImage=theImage)
            li.setInfo('audio', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
            break

    url = build_url({'mode': 'search_audio', 'page': nextPage, 'search_term': name})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'featured_video':
    content = readURL('http://www.newgrounds.com')
    #debug(content)

    grabContent = re.compile('<a id="fp_movie(.*?)<\/a>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('alt="([^"]*)"').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        videoID = re.compile('href="http:\/\/www.newgrounds.com\/portal\/view\/([^"]*)"').findall(newContent)

        for vID in videoID:
            url = build_url({'mode': 'video_info', 'videoID': vID})
            li = xbmcgui.ListItem(title[0], iconImage=thumb[0])
            li.setInfo('video', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'featured_audio':
    content = readURL('http://www.newgrounds.com')
    #debug(content)

    grabContent = re.compile('<td style="background-image: url(.*?)<\/div>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        image = re.compile('\(([^"]+)\)').findall(newContent)
        title = re.compile('<td>([^"]*)<\/td>').findall(newContent)
        audioID = re.compile('<a href="http:\/\/www.newgrounds.com\/audio\/listen\/([^"]+)">([^"]+)<\/a>').findall(newContent)
        artist = re.compile('<div>\n<a href="http://([^"]+).newgrounds.com"').findall(newContent)
        category = re.compile('</td>\n<td>([^"]+)</td>\n<td>').findall(newContent)

        for aID,title in audioID:
            url = build_url({'mode': 'audio_info', 'audioID': aID})
            li = xbmcgui.ListItem(title + ' by ' + artist[0] + ' [' + category[0] + ']', iconImage=image[0])
            li.setInfo('audio', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'featured_art':
    content = readURL('http://www.newgrounds.com')
    #debug(content)

    grabContent = re.compile('<a href="http:\/\/www.newgrounds.com\/art\/view\/(.*?)<\/a>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('alt="([^"]*) by ').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        artID = re.compile('([^"]*)" class="rated-([^"]*) ').findall(newContent)
        artist = re.compile('<strong><span></span>by (.*?)</strong>').findall(newContent)

        for aID,rated in artID:
            url = build_url({'mode': 'art_info', 'artID': aID})
            li = xbmcgui.ListItem(HTMLParser.HTMLParser().unescape(title[0]) + ' by ' + artist[0] + " [" + rated.upper() + "]", iconImage=thumb[0])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'search_video':
    name = ''
    if int(args['page'][0]) > 1:
        name = args['search_term'][0]
    else:
        kb = xbmc.Keyboard('', 'search')
        kb.doModal()
        if kb.isConfirmed():
            name = kb.getText()
            #xbmcgui.Dialog().ok('DEBUG', name)

    content = readURL('http://www.newgrounds.com/portal/search/movies/' + urllib.quote_plus(name) + '/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<li class="movie">(.*?)<\/li>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('alt="([^"]*)"').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        descncat = re.compile('<span>([^"]*)<\/span>').findall(newContent)
        videoID = re.compile('<a href="\/portal\/view\/([^"]*)">').findall(newContent)

        for vID in videoID:
            url = build_url({'mode': 'video_info', 'videoID': vID})
            li = xbmcgui.ListItem(HTMLParser.HTMLParser().unescape(title[0]), iconImage=thumb[0])
            li.setInfo('video', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
            break

    url = build_url({'mode': 'search_video', 'page': nextPage, 'search_term': name})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'search_art':
    name = ''
    if int(args['page'][0]) > 1:
        name = args['search_term'][0]
    else:
        kb = xbmc.Keyboard('', 'search')
        kb.doModal()
        if kb.isConfirmed():
            name = kb.getText()
            #xbmcgui.Dialog().ok('DEBUG', name)

    content = readURL('http://www.newgrounds.com/art/search/' + urllib.quote_plus(name) + '/page/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<a href="\/art\/view\/(.*?)<\/a>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('alt="([^"]*) by ').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        rated = re.compile('class="([^"]*)"').findall(newContent)
        artID = re.compile('([^"]*)" class="rated-([^"]*)').findall(newContent)
        artist = re.compile('<strong><span></span>by (.*?)</strong>').findall(newContent)

        for aID,rated in artID:
            url = build_url({'mode': 'art_info', 'artID': aID})
            li = xbmcgui.ListItem(HTMLParser.HTMLParser().unescape(title[0]) + ' by ' + artist[0] + " [" + rated.upper() + "]", iconImage=thumb[0])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search_art', 'page': nextPage, 'search_term': name})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultPhoto.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'art_list':
    content = readURL('http://www.newgrounds.com/art/browse/page/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<a href="\/art\/view\/(.*?)<\/a>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('alt="([^"]*) by ').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        rated = re.compile('class="([^"]*)"').findall(newContent)
        artID = re.compile('([^"]*)" class="rated-([^"]*)').findall(newContent)
        artist = re.compile('<strong><span></span>by (.*?)</strong>').findall(newContent)

        for aID,rated in artID:
            url = build_url({'mode': 'art_info', 'artID': aID})
            li = xbmcgui.ListItem(HTMLParser.HTMLParser().unescape(title[0]) + ' by ' + artist[0] + " [" + rated.upper() + "]", iconImage=thumb[0])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'art_list', 'page': nextPage})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultPhoto.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'art_info':
    content = readURL('http://www.newgrounds.com/art/view/' + args['artID'][0])
    file = re.compile('src=\"http:\\/\\/art.ngfiles.com\\/images\\/(.*?)\\"').findall(content)
    xbmc.executebuiltin('ShowPicture(' + 'http://art.ngfiles.com/images/' + file[0] + ')') 

elif mode[0] == 'video_list':
    content = readURL('http://www.newgrounds.com/movies/browse/genre/' + args['cat'][0] + '/interval/year/sort/score/page/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<a href="\/portal\/view\/(.*?)<\/a>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        title = re.compile('<strong>([^"]*)<\/strong>').findall(newContent)
        thumb = re.compile('src="([^"]*)"').findall(newContent)
        descncat = re.compile('<span>([^"]*)<\/span>').findall(newContent)
        videoID = re.compile('([^"]*)" class="rated-').findall(newContent)

        for vID in videoID:
            url = build_url({'mode': 'video_info', 'videoID': vID})
            li = xbmcgui.ListItem(HTMLParser.HTMLParser().unescape(title[0]), iconImage=thumb[0])
            li.setInfo('video', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'video_list', 'cat': args['cat'][0], 'page': nextPage})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'video_info':
    content = readURL('http://www.newgrounds.com/portal/view/' + args['videoID'][0])
    file = re.compile('uploads.ungrounded.net(.*?)"').findall(content)
    #xbmcgui.Dialog().ok('DEBUG', 'http://uploads.ungrounded.net' + file[0].replace('\\', ''))

    for f in file:
        if not ".swf" in f:
            xbmc.Player().play('http://uploads.ungrounded.net' + f.replace('\\', '')) #file 3 is always mobile compatible?
    
elif mode[0] == 'audio_list':
    content = readURL('http://www.newgrounds.com/audio/browse/genre/' + args['cat'][0] + '/page/' + args['page'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    grabContent = re.compile('<li><div class="audio-wrapper">(.*?)<\/div><\/li>', re.DOTALL).findall(content)
    #xbmcgui.Dialog().ok('DEBUG', grabContent[0])
    nextPage = int(args['page'][0]) + 1

    for newContent in grabContent:
        #xbmcgui.Dialog().ok('DEBUG', newContent)
        image = re.compile('src="([^"]+)"').findall(newContent)
        title = re.compile('<span>([^"]*) <\/span>').findall(newContent)
        audioID = re.compile('href="\/audio\/listen\/([^"]+)"').findall(newContent)
        artist = re.compile('<strong>([^"]+)<\/strong>').findall(newContent)
        category = re.compile('<div class="detail-genre">([^"]*) <\/div>').findall(newContent)

        for aID in audioID:
            url = build_url({'mode': 'audio_info', 'audioID': aID})
            li = xbmcgui.ListItem(re.sub('[^A-Za-z0-9 {}()-]+', '', title[0]) + ' by ' + artist[0] + ' [' + re.sub('[^A-Za-z0-9 ]+', '', category[0]) + ']', iconImage=image[0])
            li.setInfo('audio', { 'title': title[0] })
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'audio_list', 'foldername': 'Audio', 'cat': args['cat'][0], 'page': nextPage})
    li = xbmcgui.ListItem('NEXT PAGE >', iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'audio_info':
    content = readURL('http://www.newgrounds.com/audio/listen/' + args['audioID'][0])
    #xbmcgui.Dialog().ok('DEBUG', content)

    # All of this WORKS! But, I want to keep the user on the list page for now.
    #title = re.compile(',"name":"([^"]+)",').findall(content)
    file = re.compile('url":"([^"]+)",').findall(content)
    #artist = re.compile(',"artist":"([^"]+)"').findall(content)
    #icon = re.compile(',"icon":"([^"]+)"').findall(content)

    #li = xbmcgui.ListItem("NAME: " + urllib.unquote(title[0]).decode('utf8'), iconImage=icon[0].replace('\\', ''))
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li)
    #xbmcplugin.endOfDirectory(addon_handle)

    #li = xbmcgui.ListItem("AUTHOR: " + urllib.unquote(artist[0]).decode('utf8'), iconImage=icon[0].replace('\\', ''))
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li)
    #xbmcplugin.endOfDirectory(addon_handle)

    #li = xbmcgui.ListItem("FILE: " + file[0].replace('\\', ''), iconImage=icon[0].replace('\\', ''))
    #xbmcplugin.addDirectoryItem(handle=addon_handle, url="", listitem=li)
    #xbmcplugin.endOfDirectory(addon_handle)

    xbmc.Player().play(file[0].replace('\\', ''))
