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
SHISTORY_DATASEP = '%preview_img%'

# Make profile dir on first startup
if not os.path.exists(xbmc.translatePath(__settings__.getAddonInfo('profile'))):
    os.makedirs(xbmc.translatePath(__settings__.getAddonInfo('profile')))
    __settings__.openSettings() # And display the settings dialog

class moebooruApi:
    def __init__(self):
        self.pRating = ["", "safe", "questionable", "explicit", "questionableplus", "questionableless"]
        self.pOrder = ["", "score", "fav", "wide", "nonwide"]
        
    def getAdvSearch(self, search):
        advSettings = ""
        if (search.find(" order:") == -1):
            if (int(__settings__.getSetting('order')) > 0):
                advSettings += " order:" + self.pOrder[int(__settings__.getSetting('order'))]            
        if (search.find(" rating:") == -1):
            if (int(__settings__.getSetting('rating')) > 0):
                advSettings += " rating:" + self.pRating[int(__settings__.getSetting('rating'))]
        return advSettings
        
    def getImages(self, search, page=1):
        result = []
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/post.json" + "?tags=" + urllib.quote_plus(str(search) + self.getAdvSearch(search)) + "&limit=" + str(__settings__.getSetting('epp')) + "&page=" + str(page))
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
        raw_result = urllib.urlopen(__settings__.getSetting('server') + "/post.xml" + "?limit=1&query=" + urllib.quote_plus(str(search) + self.getAdvSearch(search)))
        result = []
        result = raw_result.read().split("\"")
        return result[5]


class moebooruSession:
    def __init__(self):
        self.api = moebooruApi()
        self.max_history = int(float(__settings__.getSetting('shistorySize')))
    def addDir(self,name,url,mode,iconimage,page=1,tot=0,sort=0, q="newsearch"):
        #u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&name="+urllib.quote_plus(name)+"&q="+urllib.quote_plus(str(q))
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&q="+urllib.quote_plus(str(q))
        liz=xbmcgui.ListItem(name, 'test',iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="image", infoLabels={"Title": name,"Label":str(sort)} )
        if mode == 2: # This also includes the search button itself... but who cares?
            contextMenu = [(language(33001), xbmc.translatePath('XBMC.RunScript(special://home/addons/plugin.image.moebooru/default.py,rmFromHistory,'+q+')'))]
            liz.addContextMenuItems(contextMenu)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=tot)

    def addImage(self, iId, url, mode, iconimage, tot=0):
        liz=xbmcgui.ListItem(iId, iconImage="DefaultImage.png", thumbnailImage=iconimage)
        liz.setInfo( type="image", infoLabels={ "Id": iId })
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=tot)

    def CATEGORIES(self):
        self.addDir(language(31001),'latest',1,os.path.join(IMAGE_PATH,'latest.png'),sort=0)
        self.addDir(language(31002),'search',2,os.path.join(IMAGE_PATH,'search.png'),sort=0)
        self.addDir(language(31003),'random',3,os.path.join(IMAGE_PATH,'random.png'),sort=0)
        self.addDir(language(31004),'pools',4,os.path.join(IMAGE_PATH,'pools.png'),sort=0)
        # 5 is used for pools
        # NYI: self.addDir('Advanced Search','advSearch',7,os.path.join(IMAGE_PATH,'search.png'),sort=0)
        self.addDir(language(31005),'history',6,os.path.join(IMAGE_PATH,'search_history.png'),sort=0)
        return True
        
    def SEARCH(self, query="", page=1):
        kbd = xbmc.Keyboard('',language(34001))
        if query=="newsearch":
            kbd.doModal()
            if (kbd.isConfirmed()):
                query = kbd.getText()
                xbmc.executebuiltin("Container.Refresh(%s?mode=2&url=search&q=%s)" % (sys.argv[0], query))
                return False;
            else:
                return False
        else:
            images = self.api.getImages(query, page)
            
            for img in images:
                self.addImage(str(img.get("id","")),img.get("jpeg_url", ""),100,img.get("preview_url",""), len(images))
            if query!="" and page == 1 and kbd.isConfirmed() and len(images) > 0: # Only add newly entered things and only add these, if results were found
                 self.conf_appendList(SHISTORY_PATH, query + SHISTORY_DATASEP + img.get("preview_url",os.path.join(IMAGE_PATH,'search.png')))
            if float(len(images)) == float(__settings__.getSetting('epp')): # If we loaded the max. number of images that we can, we assume there are more
                self.addDir(language(32002),'search',2,os.path.join(IMAGE_PATH,'more.png'),page=int(page)+1,sort=0, q=query)
            return True
    def ADVSEARCH(self, query="", page=1):
        print "NYI"
        return True
    def LATEST(self,page=1):
        self.SEARCH("",page)
        return True
    def HISTORY(self):
        for item in self.conf_getList(SHISTORY_PATH):
            item = item.split(SHISTORY_DATASEP)
            imgUrl=item[1]
            query=item[0]
            self.addDir(query,'search',2,imgUrl,sort=0, q=query)
        return True
    def POOLS(self, query="", page=1):
        kbd = xbmc.Keyboard('',language(34001))
        if query=="":
            self.addDir(language(35001),'pools',4,os.path.join(IMAGE_PATH,'search.png'),sort=0, q="newquery")
        if query=="newquery":
            kbd.doModal()
            if (kbd.isConfirmed()):
                query = kbd.getText()
                xbmc.executebuiltin("Container.Refresh(%s?mode=4&url=pools&q=%s)" % (sys.argv[0], query))
                return False
            else:
                return False
        else:
            pools = self.api.getPools(query,page)
            for pool in pools:
                name=pool.get("name","error")
                pId=pool.get("id","0")
                try:
                    previewUrl = os.path.join(IMAGE_PATH,'pools.png')
                    print str(__settings__.getSetting('previewPools'))
                    if str(__settings__.getSetting('previewPools')) == "true":
                        imgs = self.api.getImagesFromPool(str(pId))
                        previewUrl = imgs[0].get('preview_url')
                    self.addDir(str(name).replace("_"," "),'pool',5,previewUrl,sort=0, q=str(pId), tot=len(pools))
                except:
                    print language(40001)

        if str(len(pools))=="20":
            self.addDir(language(32002),'pools',4,os.path.join(IMAGE_PATH,'more.png'),page=int(page)+1,sort=0, q=query)
        return True
    def POOL(self, query="", page=1):
        images = self.api.getImagesFromPool(query, page)
        for img in images:
            self.addImage(str(img.get("id","")),img.get("jpeg_url", ""),100,img.get("preview_url",""), tot=len(images))
        return True
    def RANDOM(self):
        page=randint(1,int(self.api.getImageCount()) // int(float(__settings__.getSetting('epp'))))
        print "RAND:" + str(page)
        images = self.api.getImages(" rating:all", page) # "rating all" is required because we can currently not get the amount of images for a specific search.
        for img in images:
            self.addImage(str(img.get("id","")),img.get("jpeg_url", ""),100,img.get("preview_url",""), tot=len(images))
        self.addDir(language(32002),'random',3,os.path.join(IMAGE_PATH,'more.png'),sort=0)
        return True
        
    def conf_getList(self, config_file):
        if not os.path.exists(config_file): return []
        fobj = open(config_file,'r')
        history = fobj.read()
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
    print "MOE: FULL PATH=" + sys.argv[2]
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

    print language(40201) + " " + str(url) + "?" + str(query) + " [" + str(name) + "] @ mode " + str(mode) + ", page " + str(page)

    update_dir = False
    success = True
    cache = True

    if mode==None or url==None or len(url)<1:
        success = moe.CATEGORIES()
    elif mode==1:
        success = moe.LATEST(page)
    elif mode==2:
        success = moe.SEARCH(query, page)
    elif mode==3:
        success = moe.RANDOM()
    elif mode==4:
        if query=="newsearch":
            query=""
        success = moe.POOLS(query, page)
    elif mode==5:
        success = moe.POOL(query, page)
    elif mode==6:
        success = moe.HISTORY()
    elif mode==7:
        success = moe.ADVSEARCH()
        
    xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=success,updateListing=update_dir,cacheToDisc=cache)
    xbmc.executebuiltin("Container.SetViewMode(500)") # I don't really like this but I did not find any way to set the default layout.
    
# Create the interface
moe = moebooruSession()

if sys.argv[1] == "rmFromHistory":
    moe.conf_rmEntry(SHISTORY_PATH, sys.argv[2])
    xbmc.executebuiltin("Container.Refresh()")
else:
    main()
