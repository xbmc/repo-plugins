
#
#      Copyright (C) 2013-2015 Sean Poyser
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import urllib
import urllib2

import re
import os

import cache

import loyal_book_utils as utils


URL     = utils.URL
ADDONID = utils.ADDONID
ADDON   = utils.ADDON
TITLE   = utils.TITLE
VERSION = utils.VERSION
HOME    = utils.HOME
GETTEXT = utils.GETTEXT
ICON    = utils.ICON


GENRE         = 100
GENREMENU     = 200
BOOK          = 300
MORE          = 500
SEARCH        = 600
PLAYCHAPTER   = 400
PLAYALL       = 700
RESUME        = 800
RESUMEALL     = 900
REMOVE_RESUME = 1000


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    #call showChangeLog like this to workaround bug in openElec
    script = os.path.join(HOME, 'showChangelog.py')
    cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('changelog', script, 0)
    xbmc.executebuiltin(cmd)


def clean(text):
    text = text.replace('&#x2013;', '-')
    text = text.replace('&#x201C;', '"')
    text = text.replace('&#x201D;', '"')
    text = text.replace('&#8211;',  '-')
    text = text.replace('&#8217;',  '\'')
    text = text.replace('&#8220;',  '"')
    text = text.replace('&#8221;',  '"')
    text = text.replace('&#39;',    '\'')
    text = text.replace('&quot;',   '\'')
    text = text.replace('&amp;',    '&')
    text = text.replace('<b>',      '')
    text = text.replace('</b>',     '')

    text = text.replace('- Free at Loyal Books',  '')
    text = text.replace('- Free at Loyal ...',    '')
    text = text.replace('- Books Should Be Free', '')
    text = text.replace('- Books ...',            '')
    text = text.replace('- Free at ...',          '')
    return text


def GetHTML(url):
    return cache.getURL(url, maxSec=7*86400)


def GetHTMLDirect(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Apple-iPhone/')
    req.add_header('Referer', URL)
    response = urllib2.urlopen(req)
    html = response.read()
    response.close()
    return html


def Genre(_url, page):
    try:    view    = int(ADDON.getSetting('VIEW'))
    except: view    = 0

    try:    sort = int(ADDON.getSetting('SORT'))
    except: sort = 0

    try:    results = int(ADDON.getSetting('RESULTS'))
    except: results = 30

    requestURL = _url

    if requestURL == '%sTop_100' % URL:
        view = 0
        if page > 1:
            requestURL += '/%s' % str(page)
    else:
        requestURL += '?'

        if view == 1:
            requestURL += '&view=author'
        if sort == 1:
            requestURL += '&sort=alphabet'
        if results != 30:
            requestURL += '&results=%d' % results

        if page > 1:
            requestURL += '&page=%s' % str(page)

    html = GetHTML(requestURL)
    html = html.replace('\n', '')

    if view == 0:
        GenreTitle(html)
    if view == 1:
        GenreAuthor(html)

    AddDir(GETTEXT(30001), MORE, _url, ICON, True, page+1)



def GenreAuthor(html):
    authors = html.split('summary="Author">')

    reAuthor = '<h1>By: (.+)</h1>'
    reBook   = '<a href="/(.+?)"><img class="cover" src="/(.+?)" alt="(.+?)"></a>.+?<p>(.+?)</td>'
    reBook   = '<a href="/(.+?)"><img class="cover" src="/(.+?)" alt=".+?">.+?<a href=".+?">(.+?)</a>.+?<p>(.+?)</td>'

    for item in authors:
        author = re.compile(reAuthor).findall(item)
        if len(author) > 0:
            author = clean(author[0].split(' <font', 1)[0])
            match  = re.compile(reBook).findall(item)

            for url, image, title, summary in match:
                url     = clean(url)
                image   = clean(image)
                title   = clean(title)
                summary = clean(summary)
                AddBook(title, author, URL+url, image, summary=summary)
                           
def GenreTitle(html):
    match = re.compile('<td class="layout2-blue".+?<a href="(.+?)"><img class="layout" src="/(.+?)".?<b>(.+?)</b></a><br>(.+?)<br>').findall(html)

    for url, image, title, author in match:
        url    = clean(url)
        image  = clean(image.split('.jpg', 1)[0]+'.jpg')
        title  = clean(title)
        author = clean(author.split('</td>', 1)[0])
        AddBook(title, author, URL+url, image)



def Book(_url, title, image, author):
    html = GetHTML(_url)
    html = html.replace('\n', '')

    match = re.compile('new Playlist\((.+?)],').findall(html)
    if len(match) < 1:
        AddDir(GETTEXT(30002), 0, '', ICON, True)
        return

    if not author:
        author = ''

    contextMenu = []
    cmd         = 'XBMC.RunPlugin(' + sys.argv[0]
    cmd        += '?mode='  + str(PLAYALL)
    cmd        += '&menu='  + _url + urllib.quote_plus('||' + name + '||' + author + '||' + image)
    cmd        += ')'

    contextMenu.append((GETTEXT(30003), cmd))
    match = re.compile('name:"(.+?)".+?mp3:"(.+?)"}').findall(match[0])
    for chapter, url in match:

        if 'Chapters' in chapter:
            num = fix(chapter).split('Chapters', 1)[-1].strip()
            if len (num) > 0:
                num = ' ' + num
            chapter = GETTEXT(30020) + num

        elif 'Chapter' in chapter:
            num = fix(chapter).split('Chapter', 1)[-1].strip().split(' ')[0]
            if len (num) > 0:
                num = ' ' + num
            chapter = GETTEXT(30004) + num

        AddChapter(url, title, clean(chapter), image, contextMenu)


def PlayAll(url, name, author, image):
    html = GetHTML(url)
    html = html.replace('\n', '')

    from player import Player
    Player(xbmc.PLAYER_CORE_MPLAYER).playAll(url, html, name, author, image, ADDONID)


def PlayChapter(url, name, chapter, image): 
    from player import Player
    Player(xbmc.PLAYER_CORE_MPLAYER).playChapter(url, name, chapter, image, ADDONID)


def GenreMenu(url):
    html = GetHTML(url)
    html = html.split('summary="All Genres">')[1]
    
    match = re.compile('<tr><td class="link menu"><a href="/(.+?)"><div id=".+?" class="g-s s-desk"></div>(.+?)</a></td></tr>').findall(html)
    genres = []
    for url, genre in match:
        genres.append([genre.replace('_', ' '), url])

    #this seems to be missing from the website
    genres.append(['Erotic', 'genre/Erotica'])
    
    genres.sort()

    for item in genres:
        AddGenre(item[0], item[1])


def Search(page, keyword):
    if not keyword or keyword == '':
        keyword = GetSearch()
    if not keyword or keyword == '':
        return

    keyword  = urllib.quote_plus(keyword)
    start    = 10 * (page-1)

    url = 'https://www.google.co.uk/search?q=%s+mp3+downloads+site:www.loyalbooks.com&start=%d' % (keyword, start)

    html = GetHTMLDirect(url)
    html = html.split('Search Results', 1)[-1]

    links = html.split('class="web_result"')
    links = links[1:]

    root = URL + 'book/'
    for link in links:
        print link
        print "__________________________"
        try:
            url   = root + re.compile('%s(.+?)%%26ei' % root).search(link).group(1)
            title = re.compile('>(.+?)</a').search(link.split(url, 1)[-1]).group(1)

            AddBook(title, None, url)

        except Exception, e:
            pass

    keyword = urllib.unquote_plus(keyword)
    AddDir(GETTEXT(30001), SEARCH, 'url', ICON, True, page+1, None, keyword)
         


def GetSearch():
    kb = xbmc.Keyboard('', TITLE, False)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    return kb.getText()



def SearchOLD(page, keyword):
    if not keyword or keyword == '':
        keyword = GetSearch()
    if not keyword or keyword == '':
        return

    nResults = ADDON.getSetting('SEARCH')
    keyword  = urllib.quote_plus(keyword)
    start    = str((page-1) * int(nResults))

    url = 'http://www.google.com/cse?cx=partner-pub-5879764092668092%3Awdqcfbe9xi9&cof=FORID%3A10&num=' + nResults + '&q=' + keyword + '&start=' + start


    html = GetHTMLDirect(url)
    html = html.replace('\n', '')
    main = re.compile('<li>(.+?)</li>').findall(html)
    for item in main:
        match = re.compile('<a class="l" href="(.+?)" onmousedown=.+?target="_top">(.+?)</a>').findall(item)
        for url, title in match:
            AddBook(title, None, url)

    keyword = urllib.unquote_plus(keyword)
    AddDir(GETTEXT(30001), SEARCH, 'url', ICON, True, page+1, None, keyword)

    
def Main():   
    CheckVersion()

    AddResume()
    AddSearch()
    AddGenre(GETTEXT(30005),     'Top_100')
    AddGenre(GETTEXT(30006),     'genre/Children')
    AddGenre(GETTEXT(30007),     'genre/Fiction')
    AddGenre(GETTEXT(30008),     'genre/Fantasy')
    AddGenre(GETTEXT(30009),     'genre/Mystery')
    AddGenreMenu(GETTEXT(30010), 'genre-menu')


def RemoveResume():
    ADDON.setSetting('RESUME_INFO',    '')
    ADDON.setSetting('RESUME_CHAPTER', '0')
    ADDON.setSetting('RESUME_TIME',    '0')


def fix(text):
    ret = ''
    for ch in text:
        if ord(ch) < 128:
            ret += ch
    return ret.strip()

    

def AddResume():
    try:
        resume = ADDON.getSetting('RESUME_INFO')
        if resume == '':
            return

        resume = urllib.unquote_plus(resume)
        resume = resume.split('||')

        name  = resume[2]
        mode  = resume[1]
        url   = resume[0]
        image = resume[4]
        extra = fix(resume[3])

        resumeText = ' [I](%s)[/I]' % GETTEXT(30012)
       
        if not extra.endswith(resumeText):
            extra += resumeText

        menu = []
        cmd  = 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], REMOVE_RESUME)

        menu.append((GETTEXT(30019), cmd))

        AddDir(name, mode, url, image, isFolder=False, extra=extra, contextMenu=menu)

    except Exception, e:
        raise


def AddSearch():
    AddDir(GETTEXT(30011), SEARCH, 'url', ICON, True)


def AddGenre(label, url, page=1):
    AddDir(label, GENRE, URL+url, ICON, True, int(page))


def AddGenreMenu(label, url):
    AddDir(label, GENREMENU, URL+url, ICON, True)    


def AddBook(title, author, url, image=None, summary=None):
    if image:
        image = URL+image
    else:
        image = ICON

    AddDir(title, BOOK, url, image, True, extra=author, summary=summary) 


def AddChapter(url, title, chapter, image, contextMenu=None):
    AddDir(title, PLAYCHAPTER, url, image, False, extra=chapter, contextMenu=contextMenu)
   

def AddDir(name, mode, url, image, isFolder, page=1, extra=None, keyword=None, contextMenu=None, summary=None):
    name = clean(name)
    label = name
    if extra:
        label = label + ' - ' + extra

    u  = sys.argv[0] 
    u += '?mode='  + str(mode)
    u += '&url='   + urllib.quote_plus(url)
    u += '&name='  + urllib.quote_plus(name) 
    u += '&image=' + urllib.quote_plus(image) 
    u += '&page='  + str(page) 

    if extra:
        u += '&extra=' + urllib.quote_plus(extra)
    else:
        extra = ''

    if keyword:
        u += '&keyword=' + urllib.quote_plus(keyword) 

    liz = xbmcgui.ListItem(label, iconImage=image, thumbnailImage=image)

    #infoLabels = {}
    #liz.setInfo(type='music', infoLabels=infoLabels)

    if contextMenu:
        liz.addContextMenuItems(contextMenu)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)


def Refresh():
    xbmc.executebuiltin('Container.Refresh')


def clearResume():
    ADDON.setSetting('RESUME_INFO',    '')
    ADDON.setSetting('RESUME_CHAPTER', '0')
    ADDON.setSetting('RESUME_TIME',    '0')
    

def get_params(path):
    params = {}
    path   = path.split('?', 1)[-1]
    pairs  = path.split('&')

    for pair in pairs:
        split = pair.split('=')
        if len(split) > 1:
            params[split[0]] = split[1]

    return params


params = get_params(sys.argv[2])

mode    = None
url     = None
name    = None
extra   = None
image   = None
page    = None
keyword = None
menu    = None

try:    mode = int(params['mode'])
except: pass

try:    url = urllib.unquote_plus(params['url'])
except: pass

try:    name = urllib.unquote_plus(params['name'])
except: pass

try:    extra = urllib.unquote_plus(params['extra'])
except: pass

try:    image = urllib.unquote_plus(params['image'])
except: pass

try:    page = int(params['page'])
except: pass

try:    keyword = urllib.unquote_plus(params['keyword'])
except: pass

try:    menu = urllib.unquote_plus(params['menu'])
except: pass

utils.log(sys.argv[2])
utils.log(mode)
utils.log(url)
utils.log(name)
utils.log(extra)
utils.log(image)
utils.log(page)
utils.log(keyword)
utils.log(menu)


if mode == BOOK:
    Book(url, name, image, extra)


elif mode == PLAYCHAPTER:
    clearResume()
    PlayChapter(url, name, extra, image)


elif mode == GENRE:
    Genre(url, page)


elif mode == MORE:
    Genre(url, page)


elif mode == GENREMENU:
    GenreMenu(url)


elif mode == SEARCH:
    Search(page, keyword)


elif mode == PLAYALL:
    items = menu.split('||')
    clearResume()
    PlayAll(items[0], items[1], items[2], items[3])


elif mode == RESUME:
    PlayChapter(url, name, extra, image)
    Refresh()

elif mode == RESUMEALL:
    PlayAll(url, name, extra, image)


elif mode == REMOVE_RESUME:
    RemoveResume()
    Refresh()


else:
    Main()

        
xbmcplugin.endOfDirectory(int(sys.argv[1]))