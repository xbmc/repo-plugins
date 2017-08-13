import os, sys, urllib, requests, re, htmlentitydefs, hashlib, time
if sys.version < '2.7.3': #If crappy html.parser, use internal version. Using internal version on ATV2 crashes as of XBMC 12.2, so that's why we test version
    import HTMLParser #analysis:ignore
import bs4  # @UnresolvedImport
import functools

from xbmcswift2 import Plugin, xbmc
plugin = Plugin()

__version__ = plugin.addon.getAddonInfo('version')
T = plugin.addon.getLocalizedString
CACHE_PATH = xbmc.translatePath(os.path.join(plugin.addon.getAddonInfo('profile'),'cache'))
FANART_PATH = xbmc.translatePath(os.path.join(plugin.addon.getAddonInfo('profile'),'fanart'))
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)
if not os.path.exists(FANART_PATH): os.makedirs(FANART_PATH)
ADDON_PATH = xbmc.translatePath(plugin.addon.getAddonInfo('path'))
plugin_fanart = os.path.join(ADDON_PATH,'fanart.jpg')

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.17'
USER_AGENT_MOBILE = 'Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10'

HEADERS = {'User-Agent':USER_AGENT}

def ERROR(msg):
    plugin.log.error('ERROR: {0}'.format(msg))
    import traceback
    plugin.log(traceback.format_exc())

charCodeFilter = re.compile('&#(\d{1,5});',re.I)
charNameFilter = re.compile('&(\w+?);')

def cUConvert(m): return unichr(int(m.group(1)))
def cTConvert(m):
    return unichr(htmlentitydefs.name2codepoint.get(m.group(1),32))

def convertHTMLCodes(html):
    try:
        html = charCodeFilter.sub(cUConvert,html)
        html = charNameFilter.sub(cTConvert,html)
    except:
        pass
    return html

def content(content_type):
    def methodWrap(func):
        @functools.wraps(func)
        def inner(*args,**kwargs):
            plugin.set_content(content_type)
            return func(*args,**kwargs)
        return inner
    return methodWrap

@plugin.cached()
def getPage(url,referer='http://geekandsundry.com'):
    headers = HEADERS.copy()
    headers['referer'] = referer
    return requests.get(url,headers=headers).text

def getSoup(html,default_parser="html5lib"):
    try:
        soup = bs4.BeautifulSoup(html, default_parser)
        plugin.log.info('Using: %s' % default_parser)
    except:
        soup = bs4.BeautifulSoup(html,"html.parser")
        plugin.log.info('Using: html.parser')
    return soup

@plugin.route('/')
def showMain():
    items = []
    items.append({'label':T(32100),'path':plugin.url_for('showNewest')})
    items.append({'label':T(32103),'path':plugin.url_for('showAllShows')})
    return items

def getShowIcon(url):
    outnameBase = url.rstrip('/').rsplit('/',1)[-1]
    outname = outnameBase + '.png'
    outfan = outnameBase + '.url'
    outfile = os.path.join(FANART_PATH,outfan)

    if os.path.exists(outfile):
        with open(outfile,'r') as f: return f.read(), os.path.join(FANART_PATH,outname)

    default = 'http://geekandsundry.com/wp-content/themes/Geek_and_Sundry/img/fallbacks/646x538.jpg'
    html = getPage(url)
    soup = getSoup(html)
    iconDiv = soup.select('div.archive-image')
    if not iconDiv: return default, default
    iconImg = iconDiv[0].img
    if not iconImg: return ''
    src = iconImg.get('src')
    if not src: return default, default
    base, fname = src.rsplit('/',1)
    fbase, ext = fname.rsplit('.',1)
    fbase = fbase.rsplit('-',1)[0]
    final = base + '/' + fbase + '.' + ext
    with open(outfile,'w') as f: f.write(final)
    return final, createFanart(final,url)

@plugin.route('/all/')
@content('tvshows')
@plugin.cached()
def showAllShows():
    url = 'http://geekandsundry.com/shows/'
    try:
        html = getPage(url)
    except:
        ERROR('Failed getting main page')
        xbmc.executebuiltin('Notification(%s,%s,%s,%s)' % ('Geek & Sundry',T(32101),3,plugin.addon.getAddonInfo('icon')))  # @UndefinedVariable #For xbmcswift2
        return

    items = []

    soup = getSoup(html)
    div = soup.select('div.shelf')
    if not div: return
    anchors = div[0].findAll('a')
    import xbmcgui
    first = True
    donePath = os.path.join(FANART_PATH,'done')
    if os.path.exists(donePath): first = False
    with open(donePath,'w') as f: f.write(str(time.time()))
    if first:
        d = xbmcgui.DialogProgress()
        d.create('Loading shows','Initializing...')
    total = len(anchors)
    for i, a in enumerate(anchors):
        try:
            title = convertHTMLCodes(a.findAll(text=True)[0])
        except:
            ERROR('Failed to get show title')
            continue

        surl = a.get('href')
        if first:
            if d.iscanceled(): break
            d.update(int((i/float(total))*100),'Initializing:',title)
        fanart, icon = getShowIcon(surl)
        status = ''
#        statusdisp = status
#        if 'Air' in status:
#            statusdisp = '[COLOR green]{0}[/COLOR]'.format(status)
#        elif 'Hiatus' in status:
#            statusdisp = '[COLOR FFAAAA00]{0}[/COLOR]'.format(status)
#        plot = '{0}: [B]{1}[/B][CR][CR]{2}'.format(T(32102),statusdisp,idict.get('desc'))
        mode = 'showShow'
        items.append(   {   'label':title,
                            'path':plugin.url_for(mode,url=surl),
                            'icon':icon,
                            'properties':{'fanart_image':fanart},
                            'info':{'Plot':'','status':status}
                        }
        )

    return items

@plugin.route('/show/<url>')
@content('episodes')
@plugin.cached()
def showShow(url):
    if not url: return False
    html = getPage(url)
    soup = getSoup(html)
    pages = soup.select('a.page-numbers')
    lastPage = 1
    if pages:
        try:
            lastPage = int(pages[-1].string)
        except:
            pass

    items = []
    for page in range(1,lastPage+1):
        if not soup:
            pageURL = url + 'page/{0}/'.format(page)
            html = getPage(pageURL,referer=url)
            soup = getSoup(html)

        for a in soup.select('a.post'):
            contentDiv = a.select('div.content-type')
            if contentDiv:
                content = contentDiv[0].string.strip()
                if not content.lower() == 'show':
                    continue
            title = a.h2.contents[0].strip()
            icon = ''
            imgdiv = a.select('div.grid_image')
            if imgdiv:
                icon = imgdiv[0].get('data-2x2') or ''

            epURL = a.get('href') or ''
            items.append(    {  'label':convertHTMLCodes(title),
                                'path':plugin.url_for('showVideoURL',url=epURL),
                                'icon':icon,
                                'properties':{'fanart_image':icon,},
                                'is_playable': True
                            }
            )

        soup = None
    return items

@plugin.cached_route('/newest/')
def showNewest():
    items = []
    url = 'http://www.youtube.com/user/geekandsundry/videos'
    html = getPage(url)
    soup = getSoup(html)
    results = soup.findAll('h3')
    for i in results:
        if not i.get('class'): continue
        a = i.find('a')
        if not a: continue

        href = a.get('href') or ''
        ID = href.split('=',1)[-1]
        thumb = 'http://i1.ytimg.com/vi/%s/0.jpg' % ID
        items.append(    {  'label':convertHTMLCodes(a.get('title','')),
                            'path':plugin.url_for('showVideo',ID=ID),
                            'icon':thumb,
                            'is_playable': True
                        }
        )
    return items

@plugin.route('/play_url/<url>')
def showVideoURL(url):
    if not url:
        plugin.set_resolved_url(None)
        return
    html = getPage(url)

    try:
        soup = getSoup(html)
        vidDiv = soup.select('div.video-wrapper')[0]

        # Get all the script and iframe tags in this wrapper and check for the one which has the brightcove player script
        scripts = vidDiv.find_all(['script', 'iframe'])
        checkForBrightcovePlayer = lambda script: script.get("src") and script.get("src").split(":", 1)[-1].startswith("//players.brightcove.net")
        vidScript = filter(checkForBrightcovePlayer, scripts)[0]

        if vidScript and vidScript.get('src'):
            src = vidScript.get('src')
            if not src.startswith('http'):
                src = 'http:' + src

            if vidScript.name == 'iframe':
                ID = re.search("videoId=([^&']+)", src).group(1)
                player = ''
            else:
                ID = vidDiv.video.get('data-video-id')
                player = vidDiv.video.get('data-player')

            return showBrightcoveVideo(ID,player,src)
    except IndexError:
        pass

    try:
        ID = re.search('(?is)<iframe.+?src="[^"]+?embed/(?P<id>[^/"]+)".+?</iframe>',html).group(1)
    except:
        ID = re.search('href="http://youtu.be/(?P<id>[^"]+)"',html).group(1)
    showVideo(ID)

@plugin.route('/play/<ID>')
def showVideo(ID):
    url = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(ID)
    plugin.set_resolved_url({'path':url,'info':{'type':'Video'}})

def showBrightcoveVideo(ID,player,src):
    script = getPage(src)
    baseURLMatch = re.search('baseUrl:"([^"]*)"',script)
    accountID = re.search('accountId:"([^"]*)"',script).group(1)
    policyKey = re.search('policyKey:"([^"]*)"',script).group(1)

    if baseURLMatch:
        baseURL = baseURLMatch.group(1)
        plugin.log.info('Using parsed baseURL')
    else:
        baseURL = 'https://edge.api.brightcove.com/playback/v1/'

    url = '{0}{1}/{2}/{3}/{4}'.format(baseURL,'accounts',accountID,'videos',ID)
    headers = HEADERS.copy()
    headers['BCOV-Policy'] = policyKey
    data = requests.get(url,headers=headers).json()
    maxHeight = 0
    url = ''
    alt = ''
    for source in data['sources']:
        if source.get('container') == 'M2TS' and not alt:
            alt = source['src']
        if 'src' in source and 'height' in source and maxHeight < source['height']: #Only sources with src are mp4 files, others are rtmp
            url = source['src']
            maxHeight = source['height']
    if not url: return

    if alt: url = alt
    #rtmp://[wowza-ip-address]:[port]/[application]/[appInstance]/[prefix]:[path1]/[path2]/[streamName]

    referer = 'http://players.brightcove.net/{account}/{player}_default/index.html?videoId={videoid}'.format(account=accountID,player=player,videoid=ID)

    url += '|User-Agent={0}&Referer={1}&Origin={2}'.format(urllib.quote(USER_AGENT_MOBILE),urllib.quote(referer),urllib.quote('http://players.brightcove.net'))
    plugin.set_resolved_url({'path':url,'info':{'type':'Video'}})

def hasPIL():
    return False
    try:
        import PIL #@analysis:ignore
        return True
    except:
        return False

def createFanart(url,page_url):
    if not hasPIL(): return url

    outname = page_url.rstrip('/').rsplit('/',1)[-1] + '.png'

    outfile = os.path.join(FANART_PATH,outname)
    if os.path.exists(outfile): return outfile
    if not url: return ''
    workfile = os.path.join(CACHE_PATH,'work.png')
#    urllib.urlretrieve(url, workfile)
    response = requests.get(url, stream=True, headers=HEADERS)
    import shutil
    with open(workfile, 'wb') as f:
        shutil.copyfileobj(response.raw, f)
    del response

    try:
        from PIL import Image # @UnresolvedImport
        image=Image.open(workfile)
        non_transparent=Image.new('RGBA',image.size,(255,255,255,255))
        try:
            non_transparent.paste(image,None,mask=image)
        except ValueError:
            image.save(outfile,'PNG')
            return outfile
        non_transparent.save(outfile,'PNG')
        return outfile
    except ImportError:
        pass
    except:
        ERROR('')
    return url

def tileImage(w,h,source):
    from PIL import Image # @UnresolvedImport
    source = Image.open(source).convert('RGBA')
    sw,sh = source.size
    target = Image.new('RGBA',(w,h),(0,0,0,255))
    x = 10
    y = 0
    switch = False
    while x < w:
        while y < h:
            nx = x  # @UnusedVariable
            ny = y
            nw = sw
            nh = sh
            paste = source
            if x + sw > w or y + sh > h or y < 0 or x < 0:
                if x + sw > w: nw = sw - (w - x)
                if y + sh > h: nh = sh - (h - y)
                if x < 0: nx = abs(x)  #@analysis:ignore
                if y < 0: ny = abs(y)
                paste = source.copy()
                paste.crop((0,ny,nw,nh))
            target.paste(paste,(x,y),paste)
            y+= sh + 15
        switch = not switch
        if switch:
            y = int(sw/2) * -1
        else:
            y = 0
        x+=sw + 10
    return target

def extractEpisode(title,url):
    test = re.search('(?i)(?:ep|#)(\d+)',title)
    if not test: test = re.search('(?i)_E(\d+)\.',url)
    if not test: test = re.search('[_\.]\d*(\d\d)\.',url)
    if test: return test.group(1)
    return ''

if __name__ == '__main__':
    plugin.run()
