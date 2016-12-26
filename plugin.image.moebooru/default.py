import xbmcaddon

import sys, urllib, re, simplejson, time, os
import xbmc, xbmcgui, xbmcplugin

from random import randint

#__settings__ = xbmcaddon.Addon(id='script.image.moebooru')
#home = __settings__.getAddonInfo('path')
#icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )

__settings__ = xbmcaddon.Addon(id='plugin.image.moebooru')
language = __settings__.getLocalizedString

IMAGE_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('path')),'resources','images')
SHISTORY_PATH = os.path.join(xbmc.translatePath(__settings__.getAddonInfo('profile')),'search_history')
SHISTORY_DATASEP = '#preview_img#'

_MODE_LATEST = 1
_MODE_SEARCH = 2
_MODE_RANDOM = 3
_MODE_POOLS = 4
_MODE_POOL = 5
_MODE_HISTORY = 6
_MODE_ADVSEARCH = 7
_MODE_TAGS = 8

_MODE_IMAGE = 100

_GETREL = "#gEtReL#" # Needs to be 8 characters and must not be a valid tag
_GETUSR = "#gEtUsR#"

_REF_HISTORY = 1
_REF_TAGLIST = 2

# Make profile dir on first startup
if not os.path.exists(xbmc.translatePath(__settings__.getAddonInfo('profile'))):
    os.makedirs(xbmc.translatePath(__settings__.getAddonInfo('profile')))
    __settings__.openSettings() # And display the settings dialog

class moebooruApi:
    def __init__(self):
        self.pRating = ["", "safe", "questionable", "explicit", "questionableplus", "questionableless"]
        self.pOrder = ["", "score", "fav", "wide", "nonwide"]
        self.pTagOrder = ["", "date", "count", "name"]
        
    def getAdvSearch(self, search):
        advSettings = ""
        if (search.find(" order:") == -1):
            if (int(__settings__.getSetting('order')) > 0):
                advSettings += " order:" + self.pOrder[int(__settings__.getSetting('order'))]            
        if (search.find(" rating:") == -1):
            if (int(__settings__.getSetting('rating')) > 0):
                advSettings += " rating:" + self.pRating[int(__settings__.getSetting('rating'))]
        return advSettings
        
    def getImages(self, search, page=1, epp=__settings__.getSetting('epp')):
        result = []
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/post.json" + "?tags=" + urllib.quote_plus(str(search) + self.getAdvSearch(search)) + "&limit=" + str(epp) + "&page=" + str(page))
        json = simplejson.loads(raw_result.read())
        return json
        
    def getPools(self, search="", page=1):
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/pool.json" + "?query=" + urllib.quote_plus(str(search)) + "&page=" + str(page)) #TODO: Why is there a page parameter if there is no limit?
        json = simplejson.loads(raw_result.read())
        return json
        
    def getImagesFromPool(self, search, page=1):
        result = []
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/pool/show.json" + "?id=" + urllib.quote_plus(str(search)) + "&page=" + str(page))
        json = simplejson.loads(raw_result.read())
        result = json.get("posts")
        return result
        
    def getImageCount(self, search=""): # Since the JSON answer doesn't include the total post count we need to "parse" XML.
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/post.xml" + "?limit=1&tags=" + self.getAdvSearch(search))
        result = []
        result = raw_result.read().split("\"")
        return result[5]

    def getRelatedTags(self, tags): # Queries the tags related to the given ones
        json = []
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/tag/related.json" + "?tags=" + urllib.quote_plus(str(tags)))
        json = simplejson.loads(raw_result.read())
        return json
        
    def searchTags(self, search):
        json = []
        advSettings = ""
        if (int(__settings__.getSetting('tagOrder')) > 0):
            advSettings += "&order=" + self.pTagOrder[int(__settings__.getSetting('tagOrder'))]
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/tag.json" + "?name=" + urllib.quote_plus(str(search)) + advSettings)
        json = simplejson.loads(raw_result.read())
        return json

class moebooruSession:
    def __init__(self):
        self.api = moebooruApi()
        self.max_history = int(float(__settings__.getSetting('shistorySize')))
    def addDir(self,name,url,mode,iconimage,page=1,tot=0,sort=0, q="newsearch", ref=0):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&q="+urllib.quote_plus(str(q))
        liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="image", infoLabels={"Title": name,"Label":str(sort)} )
        contextMenu = []
        if ref == _REF_HISTORY or ref == _REF_TAGLIST: # The related tags button
            contextMenu.append ([language(30521), xbmc.translatePath('Container.Update(%s?mode=%s&url=tags&q=%s)' % (sys.argv[0], _MODE_TAGS, _GETREL + q))])
        if ref == _REF_HISTORY:
            contextMenu.append([language(30600), xbmc.translatePath('XBMC.RunScript(special://home/addons/plugin.image.moebooru/default.py,rmFromHistory,'+q+')')])
        liz.addContextMenuItems(contextMenu)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)

    def addImage(self, iId, url, mode, iconimage, tot=0, relatedTags=""):
        liz=xbmcgui.ListItem(iId, iconImage="DefaultImage.png", thumbnailImage=iconimage)
        liz.setInfo( type="image", infoLabels={ "Id": iId })
        if (mode == _MODE_IMAGE) and (relatedTags != ""):
            contextMenu = [(language(30601), xbmc.translatePath('Container.Update(%s?mode=%s&url=tags&q=%s)' % (sys.argv[0], _MODE_TAGS, relatedTags)))]
            liz.addContextMenuItems(contextMenu)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

    def CATEGORIES(self):
        self.addDir(language(30500),'latest',_MODE_LATEST,os.path.join(IMAGE_PATH,'latest.png'),sort=0)
        self.addDir(language(30501),'search',_MODE_SEARCH,os.path.join(IMAGE_PATH,'search.png'),sort=0)
        self.addDir(language(30502),'random',_MODE_RANDOM,os.path.join(IMAGE_PATH,'random.png'),sort=0)
        self.addDir(language(30503),'pools',_MODE_POOLS,os.path.join(IMAGE_PATH,'pools.png'),sort=0)
        # 5 is used for pools
        # NYI: self.addDir('Advanced Search','advSearch',7,os.path.join(IMAGE_PATH,'search.png'),sort=0)
        self.addDir(language(30504),'tags',_MODE_TAGS,os.path.join(IMAGE_PATH,'tags.png'),sort=0, q=(_GETUSR + "newquery"))
        self.addDir(language(30505),'history',_MODE_HISTORY,os.path.join(IMAGE_PATH,'search_history.png'),sort=0)
        return True
        
    def SEARCH(self, query="", page=1):
        kbd = xbmc.Keyboard('',language(30700))
        if query=="newsearch":
            kbd.doModal()
            if (kbd.isConfirmed()):
                query = kbd.getText()
                xbmc.executebuiltin("Container.Refresh(%s?mode=%s&url=search&q=%s)" % (sys.argv[0], _MODE_SEARCH, query))
            return False
        else:
            images = self.api.getImages(query, page)
            
            if len(images) == 0: # No results -> suggestions
                xbmc.executebuiltin("Notification(" + language(30702) + ")")
                self.TAGS(_GETUSR + query)
            if page == 1 and query[:query.find(" ")] != "" and len(images) > 0: # Display the related tags button only on the first page and if we are not viewing "latest".
                self.addDir(language(30521),'tags',_MODE_TAGS,os.path.join(IMAGE_PATH,'tags.png'),sort=0, q=_GETREL + query)
            for img in images:
                self.addImage(str(img.get("id","")),"http:" + img.get("jpeg_url", ""),_MODE_IMAGE,"http:" + img.get("preview_url",""), len(images), relatedTags = img.get("tags",""))
            if query[:query.find(" ")] != "" and page == 1 and kbd.isConfirmed() and len(images) > 0: # Only add newly entered things and only add these, if results were found
                 self.conf_appendList(SHISTORY_PATH, query + SHISTORY_DATASEP + "http:" + img.get("preview_url",os.path.join(IMAGE_PATH,'search.png')))
            if float(len(images)) == float(__settings__.getSetting('epp')): # If we loaded the max. number of images that we can, we assume there are more
                self.addDir(language(30520),'search',_MODE_SEARCH,os.path.join(IMAGE_PATH,'more.png'),page=int(page)+1,sort=0, q=query)
            return True
    def ADVSEARCH(self, query="", page=1):
        print "NYI"
        return True
    def LATEST(self,page=1):
        self.SEARCH(" order:latest",page)
        return True
    def HISTORY(self):
        for item in self.conf_getList(SHISTORY_PATH):
            item = item.split(SHISTORY_DATASEP)
            imgUrl=item[1]
            query=item[0]
            self.addDir(query,'search',_MODE_SEARCH,imgUrl,sort=0, q=query, ref=_REF_HISTORY)
        return True
    def POOLS(self, query="", page=1):
        kbd = xbmc.Keyboard('',language(30700))
        if query=="":
            self.addDir(language(30530),'pools',_MODE_POOLS,os.path.join(IMAGE_PATH,'search.png'),sort=0, q="newquery")
        if query=="newquery":
            kbd.doModal()
            if (kbd.isConfirmed()):
                query = kbd.getText()
                xbmc.executebuiltin("Container.Refresh(%s?mode=%s&url=pools&q=%s)" % (sys.argv[0], _MODE_POOLS, query))
            return False
        else:
            pools = self.api.getPools(query,page)
            for pool in pools:
                name=pool.get("name","error")
                pId=pool.get("id","0")
                try:
                    previewUrl = os.path.join(IMAGE_PATH,'pools.png')
                    if str(__settings__.getSetting('previewPools')) == "true":
                        imgs = self.api.getImagesFromPool(str(pId))
                        previewUrl = "http:" + imgs[0].get('preview_url')
                    self.addDir(str(name).replace("_"," "),'pool',_MODE_POOL,previewUrl,sort=0, q=str(pId), tot=len(pools))
                except:
                    print language(30900)

        if str(len(pools))=="20":
            self.addDir(language(30520),'pools',_MODE_POOLS,os.path.join(IMAGE_PATH,'more.png'),page=int(page)+1,sort=0, q=query)
        return True
    def POOL(self, query="", page=1):
        images = self.api.getImagesFromPool(query, page)
        for img in images:
            self.addImage(str(img.get("id","")),"http:" + img.get("jpeg_url", ""),_MODE_IMAGE,"http:" + img.get("preview_url",""), tot=len(images), relatedTags = img.get("tags",""))
        return True
    def RANDOM(self):
        page=randint(1,int(self.api.getImageCount()) // int(float(__settings__.getSetting('epp'))))
        images = self.api.getImages("", page)
        for img in images:
            self.addImage(str(img.get("id","")),"http:" + img.get("jpeg_url", ""),_MODE_IMAGE,"http:" + img.get("preview_url",""), tot=len(images), relatedTags = img.get("tags",""))
        self.addDir(language(30520),'random',_MODE_RANDOM,os.path.join(IMAGE_PATH,'more.png'),sort=0)
        return True
    def TAGS(self, query):
        typ = 0 # 0=list
        
        # Secton for related tags
        if (query[:8] == _GETREL):
            query = query[8:]
            typ = 1 # 1=relTags
            
        # Section for user input
        elif (query[:8] == _GETUSR):
            query = query[8:]
            typ = 2 #2=searchTag
            if (query == "newquery"):
                kbd = xbmc.Keyboard('',language(30701))
                kbd.doModal()
                if (kbd.isConfirmed()):
                    query = _GETUSR + kbd.getText()
                    xbmc.executebuiltin("Container.Refresh(%s?mode=%s&url=tags&q=%s)" % (sys.argv[0], _MODE_TAGS, query))
                return False
            else:
                tags = self.api.searchTags(query)
                lst = []
                for tag in tags:
                    lst.append(tag.get("name"))
                tags = lst
        
        # Parse the completed list / query the related things
        if typ == 0 or typ == 1:
            tags = query.split(" ")
        if (typ == 1):
            query = self.api.getRelatedTags(query)
            lst = []
            for tag in tags:
                temp = query.get(tag)
                if temp:
                    for subtag in temp:
                        lst.append(subtag[0])
            tags = lst
        
        # General output
        for tag in tags:
            previewUrl = os.path.join(IMAGE_PATH,'search.png')
            if str(__settings__.getSetting('previewTags')) == "true":
                imgs = self.api.getImages(tag, epp=1)
                if (len(imgs) > 0):
                    previewUrl = "http:" + imgs[0].get('preview_url')
            self.addDir(tag,'search',_MODE_SEARCH,previewUrl,sort=0, q=tag, ref=_REF_TAGLIST, tot=len(tags))
        return True
    
    def conf_getList(self, config_file):
        if not os.path.exists(config_file): return []
        fobj = open(config_file,'r')
        history = fobj.read()
        if ("%preview_img%" in history): # Required when updating from any version older than 0.8
            history = history.replace("%preview_img%", SHISTORY_DATASEP)
        fobj.close()
        return history.splitlines()
    def conf_appendList(self, config_file, item):
        content = self.conf_getList(config_file)
        content.insert(0,item)
        content = content[0:self.max_history]
        self.conf_save(config_file, content)
    def conf_save(self, config_file, content):
        fobj = open(config_file,'w')
        fobj.write('\n'.join(content))
        fobj.close()
    def conf_rmEntry(self, config_file, itemToRemove):
        out = []
        content = self.conf_getList(config_file)
        for item in content:
            if str(item.split(SHISTORY_DATASEP)[0]) != str(itemToRemove):
                out.insert(len(out), item)
        self.conf_save(config_file, out)

# copied from the google image plugin (thanks)
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
            if (len(splitparams))==1:
                param[splitparams[0]]=""
                            
    return param

def main():
    # Get all parameters (current path etc.)
    params = get_params()
    url=None
    name=None
    mode=None
    page=1
    query="newsearch"

    try:
            url=urllib.unquote_plus(params["url"])
    except:
            pass
    try:
            name=urllib.unquote_plus(params["name"])
    except:
            pass
    try:
            mode=int(params["mode"])
    except:
            pass
    try:
            page=int(params["page"])
    except:
            pass
    try:
            query=urllib.unquote_plus(params["q"])
    except:
            pass

    print language(30901) + " " + str(url) + "?" + str(query) + " [" + str(name) + "] @ mode " + str(mode) + ", page " + str(page)

    update_dir = False
    success = True
    cache = True

    if mode==None or url==None or len(url)<1:
        success = moe.CATEGORIES()
    elif mode == _MODE_LATEST:
        success = moe.LATEST(page)
    elif mode == _MODE_SEARCH:
        success = moe.SEARCH(query, page)
    elif mode == _MODE_RANDOM:
        success = moe.RANDOM()
    elif mode == _MODE_POOLS:
        if query=="newsearch":
            query=""
        success = moe.POOLS(query, page)
    elif mode == _MODE_POOL:
        success = moe.POOL(query, page)
    elif mode == _MODE_HISTORY:
        success = moe.HISTORY()
    elif mode == _MODE_ADVSEARCH:
        success = moe.ADVSEARCH()
    elif mode == _MODE_TAGS:
        success = moe.TAGS(query)
        
    xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)
    xbmc.executebuiltin("Container.SetViewMode(500)") # I don't really like this but I did not find any way to set the default layout.
    
# Create the interface
moe = moebooruSession()

if sys.argv[1] == "rmFromHistory":
    moe.conf_rmEntry(SHISTORY_PATH, sys.argv[2])
    xbmc.executebuiltin("Container.Refresh()")
else:
    main()
