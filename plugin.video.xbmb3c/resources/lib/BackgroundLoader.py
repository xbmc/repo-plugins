#################################################################################################
# Start of BackgroundRotationThread
# Sets a backgound property to a fan art link
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
import urllib2
import random
import time

_MODE_BASICPLAY=12

class BackgroundRotationThread(threading.Thread):

    movie_art_links = []
    tv_art_links = []
    music_art_links = []
    global_art_links = []
    item_art_links = {}
    current_movie_art = 0
    current_tv_art = 0
    current_music_art = 0
    current_global_art = 0
    current_item_art = 0
    linksLoaded = False
    logLevel = 0
   
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C BackgroundRotationThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C BackgroundRotationThread -> " + msg)
    
    def run(self):
        self.logMsg("Started")
        
        try:
            self.loadLastBackground()
        except Exception, e:
            self.logMsg("loadLastBackground Exception : " + str(e), level=0)
            
        WINDOW = xbmcgui.Window( 10000 )
        filterOnParent_Last = WINDOW.getProperty("MB3.Background.Collection")
        
        last_id = ""
        self.updateArtLinks()
        self.setBackgroundLink(filterOnParent_Last)
        lastRun = datetime.today()
        itemLastRun = datetime.today()
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
        if(backgroundRefresh < 10):
            backgroundRefresh = 10
            
        itemBackgroundRefresh = 5
        lastUserName = ""

        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            td2 = datetime.today() - itemLastRun
            secTotal = td.seconds
            secTotal2 = td2.seconds
            
            addonSettings2 = xbmcaddon.Addon(id='plugin.video.xbmb3c')
            userName = addonSettings2.getSetting('username')  
            xbmc.log("Server details string : (" + userName + ") (" + lastUserName + ")")
            
            Collection = WINDOW.getProperty("MB3.Background.Collection")
            if(secTotal > backgroundRefresh or filterOnParent_Last != Collection or userName != lastUserName):
                lastUserName = userName
                if(self.linksLoaded == False):
                    self.updateArtLinks()
                lastRun = datetime.today()
                filterOnParent_Last = Collection
                backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
                self.setBackgroundLink(Collection)
                if(backgroundRefresh < 10):
                    backgroundRefresh = 10
            
            # update item BG every 7 seconds
            if(secTotal2 > itemBackgroundRefresh):
                self.setItemBackgroundLink()
                itemLastRun = datetime.today()
                
            # update item BG on selected item changes
            current_id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
            if current_id != last_id:
                self.setItemBackgroundLink()
                itemLastRun = datetime.today()
                last_id = current_id
                
            xbmc.sleep(1000)
        
        try:
            self.saveLastBackground()
        except Exception, e:
            self.logMsg("saveLastBackground Exception : " + str(e), level=0)  
            
        self.logMsg("Exited")

    def loadLastBackground(self):
        
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'r')
        jsonData = dataFile.read()
        dataFile.close()
        
        self.logMsg(jsonData)
        result = json.loads(jsonData)
        
        WINDOW = xbmcgui.Window( 10000 )
        if(result.get("global") != None):
            self.logMsg("Setting Global Last : " + str(result.get("global")), level=2)
            WINDOW.setProperty("MB3.Background.Global.FanArt", result.get("global")["url"])       

        if(result.get("movie") != None):
            self.logMsg("Setting Movie Last : " + str(result.get("movie")), level=2)
            WINDOW.setProperty("MB3.Background.Movie.FanArt", result.get("movie")["url"])      
            
        if(result.get("tv") != None):
            self.logMsg("Setting TV Last : " + str(result.get("tv")), level=2)
            WINDOW.setProperty("MB3.Background.TV.FanArt", result.get("tv")["url"])    

        if(result.get("music") != None):
            self.logMsg("Setting Music Last : " + str(result.get("music")), level=2)
            WINDOW.setProperty("MB3.Background.Music.FanArt", result.get("music")["url"])   

    def saveLastBackground(self):
    
        data = {}
        if(len(self.global_art_links) > 0):
            data["global"] = self.global_art_links[self.current_global_art]
        if(len(self.movie_art_links) > 0):
            data["movie"] = self.movie_art_links[self.current_movie_art]
        if(len(self.tv_art_links) > 0):
            data["tv"] = self.tv_art_links[self.current_tv_art]
        if(len(self.music_art_links) > 0):
            data["music"] = self.music_art_links[self.current_music_art]

        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )            
            
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'w')
        stringdata = json.dumps(data)
        self.logMsg("Last Background Links : " + stringdata)
        dataFile.write(stringdata)
        dataFile.close()        
    
    def setBackgroundLink(self, filterOnParent):
        
        # load the background blacklist
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        lastDataPath = __addondir__ + "BlackListedBgLinks.json"
        
        black_list = []
        
        # load blacklist data
        try:
            dataFile = open(lastDataPath, 'r')
            jsonData = dataFile.read()
            dataFile.close()        
            black_list = json.loads(jsonData)
            self.logMsg("Loaded Background Black List : " + str(black_list))
        except:
            self.logMsg("No Background Black List found, starting with empty Black List")
            black_list = []    


        WINDOW = xbmcgui.Window( 10000 )
        
        if(len(self.movie_art_links) > 0):
            self.logMsg("setBackgroundLink index movie_art_links " + str(self.current_movie_art + 1) + " of " + str(len(self.movie_art_links)), level=2)
            artUrl =  self.movie_art_links[self.current_movie_art]["url"]
            WINDOW.setProperty("MB3.Background.Movie.FanArt", artUrl)
            self.logMsg("MB3.Background.Movie.FanArt=" + artUrl)
            self.current_movie_art = self.current_movie_art + 1
            if(self.current_movie_art == len(self.movie_art_links)):
                self.current_movie_art = 0         
        
        if(len(self.tv_art_links) > 0):
            self.logMsg("setBackgroundLink index tv_art_links " + str(self.current_tv_art + 1) + " of " + str(len(self.tv_art_links)), level=2)
            artUrl =  self.tv_art_links[self.current_tv_art]["url"]
            WINDOW.setProperty("MB3.Background.TV.FanArt", artUrl)
            self.logMsg("MB3.Background.TV.FanArt=" + artUrl)
            self.current_tv_art = self.current_tv_art + 1
            if(self.current_tv_art == len(self.tv_art_links)):
                self.current_tv_art = 0
                
        if(len(self.music_art_links) > 0):
            self.logMsg("setBackgroundLink index music_art_links " + str(self.current_music_art + 1) + " of " + str(len(self.music_art_links)), level=2)
            artUrl =  self.music_art_links[self.current_music_art]["url"] 
            WINDOW.setProperty("MB3.Background.Music.FanArt", artUrl)
            self.logMsg("MB3.Background.Music.FanArt=" + artUrl)
            self.current_music_art = self.current_music_art + 1
            if(self.current_music_art == len(self.music_art_links)):
                self.current_music_art = 0
            
        if(len(self.global_art_links) > 0):
            next, nextItem = self.findNextLink(self.global_art_links, black_list, self.current_global_art, filterOnParent)
            backGroundUrl = nextItem["url"]
            posterUrl = nextItem["poster"]
            actionUrl = nextItem["action"]
            self.current_global_art = next
            WINDOW.setProperty("MB3.Background.Global.FanArt", backGroundUrl)
            self.logMsg("MB3.Background.Global.FanArt=" + backGroundUrl)
            WINDOW.setProperty("MB3.Background.Global.FanArt.Poster", posterUrl)
            self.logMsg("MB3.Background.Global.FanArt.Poster=" + posterUrl)    
            WINDOW.setProperty("MB3.Background.Global.FanArt.Action", actionUrl)
            self.logMsg("MB3.Background.Global.FanArt.Action=" + actionUrl)    
                
    def isBlackListed(self, blackList, bgInfo):
        for blocked in blackList:
            if(bgInfo["id"] == blocked["id"]):
                self.logMsg("Block List Parents Match On : " + str(bgInfo) + " : " + str(blocked), level=1)
                if(blocked["index"] == -1 or bgInfo["index"] == blocked["index"]):
                    self.logMsg("Item Blocked", level=1)
                    return True
        return False
           
    def findNextLink(self, linkList, blackList, startIndex, filterOnParent):
        currentIndex = startIndex
        
        isBlacklisted = True
        isParentMatch = False
        
        #xbmc.log("findNextLink : filterOnParent=" + str(filterOnParent) + " isParentMatch=" + str(isParentMatch))
        
        while(isBlacklisted or isParentMatch == False):
        
            currentIndex = currentIndex + 1
            
            if(currentIndex == len(linkList)):
                currentIndex = 0
                
            if(currentIndex == startIndex):
                return (currentIndex, linkList[currentIndex]) # we checked everything and nothing was ok so return the first one again                

            isBlacklisted = self.isBlackListed(blackList, linkList[currentIndex])
            isParentMatch = True
            if(filterOnParent != None and filterOnParent != ""):
                isParentMatch = filterOnParent in linkList[currentIndex]["collections"]
             
        nextIndex = currentIndex + 1
        
        if(nextIndex == len(linkList)):
            nextIndex = 0    

        return (nextIndex, linkList[currentIndex])
    
    def updateArtLinks(self):
        t1 = time.time()
        result01 = self.updateCollectionArtLinks()
        t2 = time.time()
        result02 = self.updateTypeArtLinks()
        t3 = time.time()
        diff = t2 - t1
        xbmc.log("TIMEDIFF01 : " + str(diff))
        diff = t3 - t2
        xbmc.log("TIMEDIFF02 : " + str(diff))
        
        if(result01 and result02):
            xbmc.log("BackgroundRotationThread Update Links Worked")
            self.linksLoaded = True
        else:
            xbmc.log("BackgroundRotationThread Update Links Failed")
            self.linksLoaded = False
            
        
    def updateActionUrls(self):
        xbmc.log("BackgroundRotationThread updateActionUrls Called")
        WINDOW = xbmcgui.Window( 10000 )
        
        for x in range(0, 10):
            contentUrl = WINDOW.getProperty("xbmb3c_collection_menuitem_content_" + str(x))
            if(contentUrl != None):
                index = contentUrl.find("SessionId=(")
                if(index > -1):
                    index = index + 11
                    index2 = contentUrl.find(")", index+1)
                    timeNow = time.time()
                    newContentUrl = contentUrl[:index] + str(timeNow) + contentUrl[index2:]
                    xbmc.log("xbmb3c_collection_menuitem_content_" + str(x) + "=" + newContentUrl)
                    WINDOW.setProperty("xbmb3c_collection_menuitem_content_" + str(x), newContentUrl)
    
    def updateCollectionArtLinks(self):
        self.logMsg("updateCollectionArtLinks Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')    
        
        # get the user ID
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users?format=json"
        
        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return False  
        
        result = []
        
        try:
            result = json.loads(jsonData)
        except Exception, e:
            self.logMsg("jsonload : " + str(e) + " (" + jsonData + ")", level=2)
            return False
        
        userid = ""
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")    
                break        
        
        self.logMsg("updateCollectionArtLinks UserID : " + userid)
        
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/Root?format=json"
        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateCollectionArtLinks urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return False
            
        self.logMsg("updateCollectionArtLinks UserData : " + str(jsonData), 2)
        result = json.loads(jsonData)
        
        parentid = result.get("Id")
        self.logMsg("updateCollectionArtLinks ParentID : " + str(parentid), 2)
            
        userRootPath = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?ParentId=" + parentid + "&SortBy=SortName&Fields=CollectionType&format=json"
        try:
            requesthandle = urllib.urlopen(userRootPath, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateCollectionArtLinks urlopen : " + str(e) + " (" + userRootPath + ")", level=0)
            return False
            
        self.logMsg("updateCollectionArtLinks userRootPath : " + str(jsonData), 2)            
        result = json.loads(jsonData)
        result = result.get("Items")
    
        artLinks = {}
        collection_count = 0
        
        # process collections
        for item in result:
        
            collectionType = item.get("CollectionType", "")
            name = item.get("Name")
            
            self.logMsg("updateCollectionArtLinks Processing Collection : " + name + " of type : " + collectionType, level=2)
            
            WINDOW = xbmcgui.Window( 10000 )
            
            #####################################################################################################
            # Process collection item menu item
            timeNow = time.time()
            contentUrl = "plugin://plugin.video.xbmb3c?mode=16&ParentId=" + item.get("Id") + "&CollectionType=" + collectionType + "&SessionId=(" + str(timeNow) + ")"
            actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=21&ParentId=" + item.get("Id") + "&Name=" + name + ",return)"
            xbmc.log("COLLECTION actionUrl: " + actionUrl)
            WINDOW.setProperty("xbmb3c_collection_menuitem_name_" + str(collection_count), name)
            WINDOW.setProperty("xbmb3c_collection_menuitem_action_" + str(collection_count), actionUrl)
            WINDOW.setProperty("xbmb3c_collection_menuitem_collection_" + str(collection_count), name)
            WINDOW.setProperty("xbmb3c_collection_menuitem_content_" + str(collection_count), contentUrl)
            #####################################################################################################

            #####################################################################################################
            # Process collection item backgrounds
            collectionUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?ParentId=" + item.get("Id") + "&IncludeItemTypes=Movie,Series,MusicArtist&Fields=ParentId&Recursive=true&CollapseBoxSetItems=false&format=json"

            try:
                requesthandle = urllib2.urlopen(collectionUrl, timeout=60)
                jsonData = requesthandle.read()
                requesthandle.close()   
            except Exception, e:
                self.logMsg("updateCollectionArtLinks urlopen : " + str(e) + " (" + collectionUrl + ")", level=0)
                return False    

            collectionResult = json.loads(jsonData)

            collectionResult = collectionResult.get("Items")
            if(collectionResult == None):
                collectionResult = []   
        
            for col_item in collectionResult:
                
                id = col_item.get("Id")
                name = col_item.get("Name")
                images = col_item.get("BackdropImageTags")
                
                if(images != None and len(images) > 0):
                    stored_item = artLinks.get(id)
                    
                    if(stored_item == None):
                    
                        stored_item = {}
                        collections = []
                        collections.append(item.get("Name"))
                        stored_item["collections"] = collections
                        links = []
                        images = col_item.get("BackdropImageTags")
                        parentID = col_item.get("ParentId")
                        name = col_item.get("Name")
                        if (images == None):
                            images = []
                        index = 0
                        
                        # build poster image link
                        posterImage = ""
                        actionUrl = ""
                        if(col_item.get("Type") == "Movie"):
                            imageTag = col_item.get("ImageTags").get("Primary")
                            posterImage = "http://localhost:15001/?id=" + str(id) + "&type=Primary" + "&tag=" + imageTag
                            url =  mb3Host + ":" + mb3Port + ',;' + id
                            url = urllib.quote(url)
                            #actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + " ,return)"
                            actionUrl = "RunPlugin(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + ")"

                        elif(col_item.get("Type") == "Series"):
                            imageTag = col_item.get("ImageTags").get("Primary")
                            posterImage = "http://localhost:15001/?id=" + str(id) + "&type=Primary" + "&tag=" + imageTag
                            actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=21&ParentId=" + id + "&Name=" + name + ",return)"
                        
                        for backdrop in images:
                          
                            info = {}
                            info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
                            info["poster"] = posterImage
                            info["action"] = actionUrl
                            info["index"] = index
                            info["id"] = id
                            info["parent"] = parentID
                            info["name"] = name
                            links.append(info)
                            index = index + 1   

                        stored_item["links"] = links
                        artLinks[id] = stored_item
                    else:
                        stored_item["collections"].append(item.get("Name"))
            #####################################################################################################
            
            collection_count = collection_count +1
            
        # build global link list
        final_global_art = []
        
        for id in artLinks:
            item = artLinks.get(id)
            collections = item.get("collections")
            links = item.get("links")
            
            for link_item in links:
                link_item["collections"] = collections
                final_global_art.append(link_item)
                #xbmc.log("COLLECTION_DATA GROUPS " + str(link_item))
        
        self.global_art_links = final_global_art
        random.shuffle(self.global_art_links)
        self.logMsg("Background Global Art Links : " + str(len(self.global_art_links)))        
        
        return True
        
    def updateTypeArtLinks(self):
        self.logMsg("updateTypeArtLinks Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        # get the user ID
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users?format=json"
        
        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateTypeArtLinks urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return False
        
        result = []
        
        try:
            result = json.loads(jsonData)
        except Exception, e:
            self.logMsg("jsonload : " + str(e) + " (" + jsonData + ")", level=2)
            return False
        
        userid = ""
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")    
                break
        
        self.logMsg("updateTypeArtLinks UserID : " + userid)

        # load Movie BG
        moviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Movie&format=json"

        try:
            requesthandle = urllib2.urlopen(moviesUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateTypeArtLinks urlopen : " + str(e) + " (" + moviesUrl + ")", level=0)
            return False

        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG Movie Image Info : " + str(info), level=2)
              
              if (info not in self.movie_art_links):
                  self.movie_art_links.append(info)
              index = index + 1
        
        random.shuffle(self.movie_art_links)
        self.logMsg("Background Movie Art Links : " + str(len(self.movie_art_links)))

        # load TV BG links
        tvUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Series&format=json"

        try:
            requesthandle = urllib2.urlopen(tvUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateTypeArtLinks urlopen : " + str(e) + " (" + tvUrl + ")", level=2)
            return False
        
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG TV Image Info : " + str(info), level=2)
              
              if (info not in self.tv_art_links):
                  self.tv_art_links.append(info)    
              index = index + 1
              
        random.shuffle(self.tv_art_links)
        self.logMsg("Background Tv Art Links : " + str(len(self.tv_art_links)))

        # load music BG links
        musicUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=MusicArtist&format=json"
        
        try:
            requesthandle = urllib2.urlopen(musicUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateTypeArtLinks urlopen : " + str(e) + " (" + musicUrl + ")", level=0)
            return False
        
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG Music Image Info : " + str(info), level=2)

              if (info not in self.music_art_links):
                  self.music_art_links.append(info)
              index = index + 1
              
        random.shuffle(self.music_art_links)
        self.logMsg("Background Music Art Links : " + str(len(self.music_art_links)))
        
        #
        # build a map indexed by id that contains a list of BG art for each item
        # this is used for selected item BG rotation
        #
        self.item_art_links = {}
        
        # add movie BG links
        for bg_item in self.movie_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list
                
        # add TV BG links
        for bg_item in self.tv_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list 

        # add music BG links
        for bg_item in self.music_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list
        
        
        return True
        
    def setItemBackgroundLink(self):
    
        id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
        self.logMsg("setItemBackgroundLink ItemGUID : " + id, 2)
    
        WINDOW = xbmcgui.Window( 10000 )
        if id != None and id != "":    
    
            listOfBackgrounds = self.item_art_links.get(id)
            
            # if for some reson the item is not in the cache try to load it now
            if(listOfBackgrounds == None or len(listOfBackgrounds) == 0):
                self.loadItemBackgroundLinks(id)
            
            listOfBackgrounds = self.item_art_links.get(id)
            
            if(listOfBackgrounds != None and len(listOfBackgrounds) > 0):
                self.logMsg("setItemBackgroundLink index " + str(self.current_item_art) + " of " + str(len(listOfBackgrounds)), level=2)
                try: 
                    artUrl = listOfBackgrounds[self.current_item_art]["url"] 
                except IndexError:
                    self.current_item_art = 0
                    artUrl = listOfBackgrounds[self.current_item_art]["url"] 
                    
                WINDOW.setProperty("MB3.Background.Item.FanArt", artUrl)
                self.logMsg("setItemBackgroundLink MB3.Background.Item.FanArt=" + artUrl, 2)
                
                self.current_item_art = self.current_item_art + 1
                if(self.current_item_art == len(listOfBackgrounds)):
                    self.current_item_art = 0
                    
            else:
                self.logMsg("setItemBackgroundLink Resetting MB3.Background.Item.FanArt", 2)
                WINDOW.clearProperty("MB3.Background.Item.FanArt")            
                    
        else:
            self.logMsg("setItemBackgroundLink Resetting MB3.Background.Item.FanArt", 2)
            WINDOW.clearProperty("MB3.Background.Item.FanArt")
            
    def loadItemBackgroundLinks(self, id):
    
        self.logMsg("loadItemBackgroundLinks Called for id" + id)
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')
        userName = addonSettings.getSetting('username')
        
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users?format=json"   

        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()
        except Exception, e:
            self.logMsg("loadItemBackgroundLinks urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return 
            
        result = []
        
        try:
            result = json.loads(jsonData)
        except Exception, e:
            self.logMsg("loadItemBackgroundLinks jsonload : " + str(e) + " (" + jsonData + ")", level=2)
            return              
        
        userid = ""
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")
                break            
    
        itemUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/" + id + "?Fields=ParentId&format=json"
        
        try:
            requesthandle = urllib2.urlopen(itemUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()
        except Exception, e:
            self.logMsg("loadItemBackgroundLinks urlopen : " + str(e) + " (" + itemUrl + ")", level=0)
            return

        item = json.loads(jsonData)
        
        if(item == None):
            item = []

        #for item in result:
        images = item.get("BackdropImageTags")
        id = item.get("Id")
        parentID = item.get("ParentId")
        origid = id
        name = item.get("Name")
        
        if (images == None or images == []):
          images = item.get("ParentBackdropImageTags")
          id = item.get("ParentId")
          if (images == None):
            images = []
            
        index = 0
     
        newBgLinks = []
        for backdrop in images:
            info = {}
            info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
            info["index"] = index
            info["id"] = id
            info["parent"] = parentID
            info["name"] = name
            self.logMsg("BG Item Image Info : " + str(info), level=2)
            newBgLinks.append(info)
            index = index + 1

        if(len(newBgLinks) > 0):
            self.item_art_links[origid] = newBgLinks
           
    