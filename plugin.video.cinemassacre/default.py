import xbmcplugin, xbmcgui, xbmcaddon
import urllib, urllib2, re
import showEpisode, sys, os#, random
try: import StorageServer
except: import storageserverdummy as StorageServer
import CommonFunctions as common
import thisCommonFunctions as common2

cache = StorageServer.StorageServer("cinemassacre", 24)
#cache.dbg = True
#common.dbg = True
addon = xbmcaddon.Addon(id='plugin.video.cinemassacre')

thisPlugin = int(sys.argv[1])

baseLink = "http://cinemassacre.com/"

defaultsXML = os.path.join(addon.getAddonInfo('path'), 'resources',"defaults.xml")
dontShowTheseUrls = []
defaultFolderIcons = {"default":os.path.join(addon.getAddonInfo('path'), "icon.png"),"list":[]}

def retFileAsString(fileName):
    file = common.openFile(fileName, "r")
    tmpContents = file.read()
    file.close()
    return tmpContents
    
def getDefaultIcons():
    xmlContents = retFileAsString(defaultsXML)
    iconList =  common2.parseDOM(xmlContents, "icons")
    iconUrlList =  common2.parseDOM(iconList, "icon", ret="url")
    iconImgList =  common2.parseDOM(iconList, "icon", ret="image")
    
    retList = []
    for i in range(0,len(iconUrlList)):
        retList.append({"url": iconUrlList[i], "image": os.path.join(addon.getAddonInfo('path'), 'resources', 'images', iconImgList[i])})
    return retList

def getNotShownUrls():
    xmlContents = retFileAsString(defaultsXML)
    exclList =  common2.parseDOM(xmlContents, "excludeUrls")
    urlList =  common2.parseDOM(exclList, "url")
    
    retList = []
    for url in urlList:
        retList.append(url)
    return retList

def excludeUrl(url):
    for notUrl in dontShowTheseUrls:
      if notUrl in url:
        return True
    return False

def checkDefaultIcon(url):
    possibleIcon = ""
    for defaultIcon in defaultFolderIcons["list"]:
        if (defaultIcon["url"] in url) and (len(defaultIcon["image"]) > len(possibleIcon)):
            possibleIcon = defaultIcon["image"]
    if len(possibleIcon) == 0:
        possibleIcon = defaultFolderIcons["default"]
    return possibleIcon
    
def addEpisodeListToDirectory(epList):
    print "Adding Video List: %s" % epList
    for episode in epList:
        if not excludeUrl(episode['url']):
            addDirectoryItem(remove_html_special_chars(episode['title']), {"action" : "episode", "link": episode['url']}, episode['thumb'], False)
    xbmcplugin.endOfDirectory(thisPlugin)        
    
def extractEpisodeImg(episode):
    linkImage = common2.parseDOM(episode, "div", attrs={"class": "video-tnail"})
    linkImage = common2.parseDOM(linkImage, "img", ret="src")
    linkImageTmp = re.compile('src=([^&]*)', re.DOTALL).findall(linkImage[0])
    if len(linkImageTmp)>0:
        if linkImageTmp[0][:1] != "/":
            linkImageTmp[0] = "/" + linkImageTmp[0]
        linkImage = baseLink+linkImageTmp[0]
    else:
        if (len(linkImage[0]) > 0) and (baseLink in linkImage[0]):
            linkImage = linkImage[0]
        else:
            linkImage = ""
    return linkImage

def pageInCache(episodeList,link):
    storedList = cache.get(link)
    try:
        storedList = eval(storedList)
    except:
        storedList = []
    if (len(storedList) >= len(episodeList)):
        for i in range(0,len(episodeList)):
            if episodeList[i] != storedList[i]:
                return []
        print "Using Stored Cache Page"
        return storedList
    return []
    
def mainPage():
    global thisPlugin
    addDirectoryItem(addon.getLocalizedString(30000), {"action" : "recent", "link": ""}, defaultFolderIcons["default"])  
    subMenu(baseLink)

def subMenu(link,row='[]'):
    global thisPlugin
    link = urllib.unquote(link)
    page = load_page(link)
    mainMenu = extractMenu(page,urllib.unquote(row))
    
    if not len(mainMenu):
        return showPage(link) # If link has no sub categories then display video list
    
    if len(link) != len(baseLink) and (link != '#'):
      addDirectoryItem(addon.getLocalizedString(30001), {"action" : "show", "link": link}, defaultFolderIcons["default"]) # All Videos Link
    
    for menuItem in mainMenu:
        menu_name = remove_html_special_chars(menuItem['name']);
        menu_link = menuItem['link'];
        if excludeUrl(menu_link):
           continue
        menu_icon = checkDefaultIcon(menu_link)
        addDirectoryItem(menu_name, {"action" : "submenu", "link": menu_link, "row": menuItem['row']}, menu_icon)
        
    xbmcplugin.endOfDirectory(thisPlugin)

def recentPage():
    global thisPlugin
    pageUrl = baseLink + "wp-admin/admin-ajax.php"
    pageData = "action=infinite_scroll&loop_file=loop"
    page = load_page(pageUrl,pageData)
    linkList = extractEpisodes(page)
    newLinkList = []
    pDialog = xbmcgui.DialogProgress(10101)
    ret = pDialog.create('Cinemassacre', 'Loading Recent Videos', '', 'Retrieved 0 Videos')
    curItm = 0
    for chk in linkList:
      curItm = curItm + 1
      link = urllib.unquote(chk['url'])
      page = load_page(link)
      if showEpisode.showEpisode(page,False) == True:
        newLinkList.append(chk)
      pDialog.update((curItm * 100) / len(linkList),'Loading Recent Videos', '', 'Retrieved '+str(len(newLinkList))+' Videos')
    addEpisodeListToDirectory(newLinkList)
    
def extractMenu(page,row='[]'):
    navList = common2.parseDOM(page, "div", attrs={"id": "navArea"})
    navList = common2.parseDOM(navList[0], "ul", attrs={"id": "menu-main-menu"})
    navList = common2.parseDOM(navList[0], "li")
    row2 = eval(row)
    tempCont = navList
    for i in row2:
        tempCont = common2.parseDOM(tempCont[i], "li")

    retList = []
    for i in range(0,len(tempCont)):
        tmpRow = eval(row)
        tmpRow.append(i)
        testNav = re.compile('^<a href="([^\"\']*?)">([^<]*?)</a>').findall(tempCont[i])
        try:
            retList.append({"name": testNav[0][1],"link": testNav[0][0], "row":repr(tmpRow)})
        except: print "extractMenu: list index out of range"
    return retList

def showPage(link):
    global thisPlugin
    link = urllib.unquote(link)
    page = load_page(link)
    # Some pages has the newest video in a "Featured Video" section
    show = common2.parseDOM(page, "div", attrs={"id": "featuredImg"})
    try:
        fTitle = common2.parseDOM(show, "span", attrs={"id": "archiveCaption"})[0]
        fTitle = common2.parseDOM(fTitle, "a")[0]
        fLink = common2.parseDOM(show, "a", ret="href")[0]
        fImg = common2.parseDOM(show, "img", ret="src")[0]
    except: print "No featured video found"

    show = common2.parseDOM(page, "div", attrs={"id": "postlist"})
    episodeList = extractEpisodes(show)
    episodeList.insert(0, {"title":fTitle, "url":fLink, "thumb":fImg})
    #cache.delete(link)
    
    ##Check first page against cache
    cachedPage = pageInCache(episodeList,link) # Returns empty list if cache differs
    if (len(cachedPage)>0):
        episodeList = cachedPage
        show = None
    
    if (show != None):
        curPage = int(re.compile('var count = (\d+?);').findall(page)[0])
        pageTotal = int(re.compile('var total = (\d+?);').findall(page)[0])
        pageCat = re.compile('var cat = (\d+?);').findall(page)[0]
        nextPageUrl = baseLink + "wp-admin/admin-ajax.php"
		
        while (curPage <= pageTotal):
            pageData = "action=infinite_scroll&page_no="+ str(curPage) + '&cat=' + pageCat + '&loop_file=loop'
            page = load_page(nextPageUrl,pageData)
            linkList = extractEpisodes(page)
            episodeList = episodeList + linkList
            curPage += 1

    cache.set(link, repr(episodeList)) #update cache
    addEpisodeListToDirectory(episodeList)

def extractEpisodes(show):
    episodes = common2.parseDOM(show, "div", attrs={"class": "archiveitem"})
    linkList = []
    for episode in episodes:
        episode = episode.encode('ascii', 'ignore')
        episode_link = common2.parseDOM(episode, "a", ret="href")[0]
        if excludeUrl(episode_link):
            continue
        episode_title = common2.parseDOM(episode, "a")[0]
        episode_title = re.compile('<div>([^<]*?)</div>').findall(episode_title)[0]
        try:
            episode_img = common2.parseDOM(episode, "img", ret="src")[0]
        except:
            episode_img = ""
        linkList.append({"title":episode_title, "url":episode_link, "thumb":episode_img})
    return linkList

def playEpisode(link):
    link = urllib.unquote(link)
    page = load_page(link)
    showEpisode.showEpisode(page)

def load_page(url, data=None):
    print "Getting page: " + url
    if len(url)<5:
        url = baseLink
    if data!=None:
      req = urllib2.Request(url,data)
      req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
      req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)# + "&randTok=" + str(random.randint(1000, 10000))
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

def remove_html_special_chars(inputStr):
    inputStr = common.replaceHTMLCodes(inputStr)
    inputStr=inputStr.strip()
    return common.makeAscii(inputStr)
    
def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    
    return param

dontShowTheseUrls = getNotShownUrls()
defaultFolderIcons["list"] = getDefaultIcons()

if not sys.argv[2]:
    mainPage()
else:
    params = get_params()
    if params['action'] == "show":
        print "Video List"
        showPage(params['link'])
    elif params['action'] == "submenu":
        print "Menu"
        subMenu(params['link'],params['row'])
    elif params['action'] == "recent":
        print "Recent list"
        recentPage()
    elif params['action'] == "episode":
        print "Episode"
        playEpisode(params['link'])
    else:
        mainPage()
