import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import urllib, urllib2, re, os
import CommonFunctions as common
import thisCommonFunctions as common2
import Queue
import threading
import copy
import urlresolver
import pickle
from cache import cache

addon = xbmcaddon.Addon()
thisPlugin = int(sys.argv[1])
BASEURL = 'http://cinemassacre.com/'
USERAGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1'
DEFAULT_PARAMS = {
  'action':'main',
  'nav':[],
  'url':''
}
addonDataFolder = xbmc.translatePath("special://profile/addon_data/{0}".format(addon.getAddonInfo('id')))
if not os.path.isdir(addonDataFolder):
  os.mkdir(addonDataFolder)
dbLocation = os.path.join(addonDataFolder,"cache.db")

cacheDb = cache(dbLocation)

logo = {
'default':'logo.png',
'/category/avgn/':'avgn.png',
'/category/boardjames/':'boardJ.png',
'/category/ykwb/':'ykwbs.png'
}

class cine(object):

  def downloadPage(self,url,data=None):
    xbmc.log("downloading page: %s" % url, xbmc.LOGDEBUG)
    retries = 0
    page = None
    while retries < 10:
      retries = retries + 1
      try:
        if data == None:
          req = urllib2.Request(url)
        else:
          req = urllib2.Request(url,data)
          req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('User-Agent', USERAGENT)
        response = urllib2.urlopen(req, timeout=30)
        page = response.read()
        response.close()
        return page
      except:
        xbmc.log("Error downloading page. Attempt %s / 10" % str(retries))
      
  def extractNav(self,dom):
    navItem = re.compile('^<a href="([^\"\']*?)">([^<]*?)</a>').findall(dom)[0]
    navTmp = common2.parseDOM(dom, "ul", attrs={"class": "sub-menu"})
    children = []
    if len(navTmp) > 0:
      navTmp = common2.parseDOM(navTmp[0], "li")
      for a in navTmp:
        children.append(self.extractNav(a))
    ret = {'title':navItem[1], 'url':navItem[0], 'children':children}
    return ret
  
  def getNav(self):
    mainPage = self.downloadPage(BASEURL)
    navList = common2.parseDOM(mainPage, "div", attrs={"id": "navArea"})
    navList = common2.parseDOM(navList[0], "ul", attrs={"id": "menu-main-menu"})
    navList = common2.parseDOM(navList[0], "li")
    extracted = []
    for a in navList:
      extracted.append(self.extractNav(a))
    return extracted
    
  def addToDir(self, title, params, folder=True):
    #folder=True
    title = self.remove_html_special_chars(title)
    image = os.path.join(addon.getAddonInfo('path'), 'resources', 'images', logo['default'])

    if 'image' in params.keys():
      image = params['image']
    
    li = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
    url = sys.argv[0] + '?' + urllib.urlencode(params)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)
      
  def showNav(self, offset=[]):
    
    if len(offset) == 0:
      self.addToDir('Recent Videos', {'action':'recent','url':'#'})
      
    navbar = self.getNav()
    parent = {'url':'#'}
    
    for a in offset:
      parent = navbar[a]
      navbar = navbar[a]['children']
      
    tmpOffset2 = 0
    
    if parent['url'] != '#':
      self.addToDir('All Videos', {'action':'display','url':parent['url']})
    
    for a in navbar:
      tmpOffset = []
      for b in offset:
        tmpOffset.append(b)
      tmpOffset.append(tmpOffset2)
      actionType = 'main'
      if len(a['children']) == 0:
        actionType = 'display'
      params = {'action':actionType,'nav':repr(tmpOffset),'url':a['url']}
      for q in logo.keys():
        if q in a['url']:
          params['image'] = os.path.join(addon.getAddonInfo('path'), 'resources', 'images', logo[q])
          break
      self.addToDir(a['title'], params)
      tmpOffset2 = tmpOffset2 + 1
      
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
  def getParams(self):
    param = DEFAULT_PARAMS
    paramstring = sys.argv[2]
    xbmc.log("Parameter String: %s" % paramstring, xbmc.LOGDEBUG)
    if len(paramstring) >= 2:
      paramstring = paramstring.replace('?', '')
      parampairs = paramstring.split('&')
      for i in range(len(parampairs)):
        splitpair = parampairs[i].split('=')
        if len(splitpair) == 2:
          param[splitpair[0]] = urllib.unquote(splitpair[1].replace('+',' '))
          if splitpair[0] == 'nav':
            param['nav'] = eval(param['nav'])
            for d in range(len(param['nav'])):
              param['nav'][d] = int(param['nav'][d])
    
    return param
  
  def videoList(self, url, nextPage=1, pageCat=None, pageTotal=None):
    
    postUrl = BASEURL + 'wp-admin/admin-ajax.php'
    postData = 'action=infinite_scroll&page_no={0}&cat={1}&loop_file=loop'
    if pageCat == None:
      vidPage = self.downloadPage(url)
      pageTotal = re.compile('var total = (\d+?);').findall(vidPage)[0]
      pageCat = re.compile('var cat = (\d+?);').findall(vidPage)[0]
    vidList = []
    
    vidList.append(self.downloadPage(postUrl,postData.format(nextPage,pageCat)))
      
    linkList = []
    for a in vidList:
      episodes = common2.parseDOM(a, "div", attrs={"class": "archiveitem"})
      for episode in episodes:
        episode = episode.encode('ascii', 'ignore')
        episode_link = common2.parseDOM(episode, "a", ret="href")[0]
        episode_title = common2.parseDOM(episode, "a")[0]
        episode_title = re.compile('<div>([^<]*?)</div>').findall(episode_title)[0]
        try:
            episode_img = common2.parseDOM(episode, "img", ret="src")[0]
        except:
            episode_img = ""
        linkList.append({"title":episode_title, "url":episode_link, "thumb":episode_img})
    
    links = self.vidLinks(linkList)
    
    for link in links:
      if 'vidUrl' in link.keys():
        self.addToDir(link['title'], {'action':'playVideo','url':link['vidUrl'], 'name':link['title'],'image':link['thumb']}, False)
      else:
        xbmc.log("Skipping - NO Vid Url: %s" % str(repr(link)), xbmc.LOGDEBUG)
    
    if int(nextPage) < int(pageTotal):
      self.addToDir("Next Page", {'action':'display','url':url,'nextPage':str(nextPage+1)}, True)
      
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  def vidLinks(self, links):
    maxThreads = 10
    inQ = Queue.Queue()
    outQ = Queue.Queue()
    
    for link in links:
      
      inQ.put(link['url'])
      
    threadList = []
    cacheLock = threading.Lock()
    for i in range(maxThreads):
      t = threading.Thread(target=self.checkVidLink, args = (inQ,outQ,cacheLock))
      t.start()
      threadList.append(t)
      
    for t in threadList:
      t.join()
      
    modifiedLinks = []
    while not outQ.empty():
      checkedLink = outQ.get(False)

      for i in range(len(links)):
        if links[i]['url'] == checkedLink['url']:
          if len(checkedLink['vidUrl']) == 1:
            links[i]['vidUrl'] = checkedLink['vidUrl'][0]
          else:
            new = copy.deepcopy(links[i])
            possibles = [
              {'inUrl':'screenwavemedia.com/play/','prefix':'[ScreenWaveMedia]','count':0},
              {'inUrl':'youtube.com','prefix':'[YouTube]','count':0},
              {'inUrl':'blip.tv','prefix':'[Blip.tv]','count':0},
              {'inUrl':'gametrailers.com','prefix':'[GameTrailers]','count':0}
            ]
            newLinks = []
            for a in checkedLink['vidUrl']:
              tmp = copy.deepcopy(new)
              tmp['vidUrl'] = a
              for b in possibles:
                if b['inUrl'] in a:
                  cancelFor = False
                  for c in newLinks:
                    if a == c['vidUrl']:
                      cancelFor = True
                      break
                  if cancelFor:
                    break
                  prefix = b['prefix']
                  if b['count'] > 0:
                    prefix = prefix + ' [' + str(b['count']) + ']'
                  tmp['title'] = prefix + tmp['title']
                  newLinks.append(tmp)
                  b['count'] = b['count'] + 1
                  break
            modifiedLinks.append({'index': i, 'links': newLinks})

    retLinks = []
    for a in range(len(links)):
      addedMod = False
      for b in modifiedLinks:
        if b['index'] == a:
          for c in b['links']:
            retLinks.append(c)
          addedMod = True
          break
      if not addedMod:
        retLinks.append(links[a])

    return retLinks
      
  def checkVidLink(self,inQ,outQ, cacheLock):
    
    while not inQ.empty():
      link = inQ.get(False)
      cacheLock.acquire()
      cacheTest = cacheDb.get(link)
      cacheLock.release()
      if cacheTest:
        vidLink = pickle.loads(cacheTest)
      else:
        vidPage = self.downloadPage(link)
        vidLink = self.getVidLink(vidPage)
        cacheLock.acquire()
        cacheDb.save(link, pickle.dumps(vidLink))
        cacheLock.release()
        
      if len(vidLink) > 0:
        outQ.put({'url':link,'vidUrl':vidLink})
        
  def getVidLink(self,vidPage):
    link = []
    player = common2.parseDOM(vidPage, "div", attrs={"class": "videoarea"})
    if player:
      playerLink = common2.parseDOM(player, "iframe", ret='src')
      if len(playerLink) > 0:
        if type(playerLink) == type(''):
          link.append(playerLink)
        elif type(playerLink) == type([]):
          for a in playerLink:
            link.append(a)
        else:
          xbmc.log("##ERROR## Found div videoarea, but no valid link")
      else:
        xbmc.log("##ERROR## Found div videoarea, but no iframe")
    else:
      player = common2.parseDOM(vidPage, "div", attrs={"class": "entry-content"})
      if player:
        if type(player) == type([]):
          player = player[0]
        playerLink = re.compile('\=[\'\"]([^\'\"]*?gametrailers.com/video/[^\'\"]*)').findall(player)
        for a in playerLink:
          link.append(a)
        playerLink = re.compile('\=[\'\"]([^\'\"]*?blip.tv/play/[^\'\"]*)').findall(player)
        for a in playerLink:
          link.append(a)
        playerLink = re.compile('\=[\'\"]([^\'\"]*?youtube.com/watch[^\'\"]*)').findall(player)
        for a in playerLink:
          link.append(a)
    return link
    
  def remove_html_special_chars(self, inputStr):
    inputStr = common.replaceHTMLCodes(inputStr)
    inputStr=inputStr.strip()
    return common.makeAscii(inputStr)
    
  def playVideo(self, params):

    link = params['url']
    image = params['image']
    name = self.remove_html_special_chars(params['name'])
    
    providers = (
        {"function":self.showEpisodeBlip, "inurl":"blip.tv/play/"},
        {"function":self.showEpisodeYoutube, "inurl":"youtube.com"},
        {"function":self.showEpisodeGametrailers, "inurl":"gametrailers.com/video"},
        {"function":self.showEpisodeScreenwave, "inurl":"screenwavemedia.com/"},
    )
    for a in providers:
      if a['inurl'] in link:
        stream_url = a['function'](link)
        item = xbmcgui.ListItem(label=name, iconImage=image, thumbnailImage=image, path=stream_url)
        xbmc.Player().play(stream_url, item)
    
  def showEpisodeGametrailers(self, videoUrl):
    _regex_extractVideoGametrailerId = re.compile("<meta property=\"og:video\" content=\"(http://media.mtvnservices.com/fb/mgid:arc:video:gametrailers.com:(.*?)\.swf)\" />");
    _regex_extractVideoGametrailerStreamURL = re.compile("<rendition bitrate=\"(.*?)\".*?<src>(.*?)</src>.*?</rendition>",re.DOTALL)

    videoPage = self.downloadPage(videoUrl)
    swfUrl = _regex_extractVideoGametrailerId.search(videoPage).group(1)

    #GET the 301 redirect URL
    req = urllib2.Request(swfUrl)
    response = urllib2.urlopen(req)
    swfUrl = response.geturl()
    videoId = _regex_extractVideoGametrailerId.search(videoPage).group(2)

    feedUrl = "http://udat.mtvnservices.com/service1/dispatch.htm?feed=mediagen_arc_feed&account=gametrailers.com&mgid=mgid%3Aarc%3Acontent%3Agametrailers.com%3A"+videoId+"&site=gametrailers.com&segment=0&mgidOfMrssFeed=mgid%3Aarc%3Acontent%3Agametrailers.com%3A"+videoId

    videoFeed = self.downloadPage(feedUrl)
    videoStreamUrls = _regex_extractVideoGametrailerStreamURL.finditer(videoFeed)

    curStream = None
    curBitrate = 0
    for stream in videoStreamUrls:
        streamUrl = stream.group(2)
        streamBitrate = int(stream.group(1))
        if streamBitrate>curBitrate:
            curStream = streamUrl.replace(" ","%20")
            curBitrate = streamBitrate

    swfUrl = swfUrl.replace("&geo=DE","&geo=US")
    swfUrl = swfUrl.replace("geo%3dDE%26","geo%3dUS%26")

    stream_url = curStream + " swfUrl="+swfUrl+" swfVfy=1"
    if curStream is not None:
      return stream_url
        
  def showEpisodeYoutube(self, videoItem):

    videoItem = videoItem.replace('https://','http://')
    if videoItem.startswith('//'):
      videoItem = 'http:' + videoItem
      
    media = urlresolver.HostedMediaFile(url=videoItem)
    return media.resolve()
    
  def showEpisodeBlip(self, videoLink):
    playerPage = self.downloadPage(videoLink)
    video = re.compile('data-episode-id=[\'\"]([^\'\"]*?)[\'\"]', re.DOTALL).findall(playerPage)
    rssUrl = ''
    if video:
      rssUrl = 'http://blip.tv/rss/flash/' + video[0]
    else:
      video = re.compile('config.embedParams = {[^}]*?}', re.DOTALL).findall(playerPage)
      if len(video) > 0:
        video = re.compile('[\'\"]file[\'\"]:[\'\"]([^\'\"]*?)[\'\"]', re.DOTALL).findall(video[0])[0]
      else:
        req = urllib2.Request(videoLink)
        response = urllib2.urlopen(req)
        fullURL = response.geturl()
        video = re.compile('file=(.*?)$', re.DOTALL).findall(fullURL)[0]
        if '&' in video:
          video = video.split('&')[0]
        
      rssUrl = urllib.unquote(video)
      
    playerPage = self.downloadPage(rssUrl)
    urlsGroup = common2.parseDOM(playerPage, "media:group")
    #media:content
    urlContent = common2.parseDOM(urlsGroup, "media:content", ret='isDefault')
    defI = 0
    for i in range(len(urlContent)):
      if urlContent[i] == 'true':
        defI = i
    urlContent = common2.parseDOM(urlsGroup, "media:content", ret='url')

    return urlContent[defI]
    
  def showEpisodeScreenwave(self, videoItem):
    tmpContent = self.downloadPage(videoItem)

    filesVal = re.compile('file(?:[\'|\"]*):(?:[\s|\'|\"]*)([^\'|\"]*)', re.DOTALL).findall(tmpContent)

    for i in range(0,len(filesVal)):
        if ("high" in filesVal[i]) and ("mp4" in filesVal[i]):
            return filesVal[i]
    
  def main(self):
    params = self.getParams()
    if params['action'] == 'main':
      self.showNav(params['nav'])
    elif params['action'] == 'display':
      nextPage = 1
      if 'nextPage' in params.keys():
        nextPage = int(params['nextPage'])
      self.videoList(params['url'], nextPage)
    elif params['action'] == 'recent':
      self.videoList(None, 1, 0, 1)
    elif params['action'] == 'playVideo':
      self.playVideo(params)
      xbmcplugin.endOfDirectory(int(sys.argv[1]))
      
    else:
      self.showNav()

main = cine()
main.main()
