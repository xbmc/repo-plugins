import sys
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import json
import urllib
from BackgroundLoader import BackgroundRotationThread

_MODE_BG_EDIT=13

class BackgroundEdit():

    def isBlackListed(self, blackList, bgInfo):
        for blocked in blackList:
            if(bgInfo["id"] == blocked["id"]):
                xbmc.log("Block List Parents Match On : " + str(bgInfo) + " : " + str(blocked))
                if(blocked["index"] == -1 or bgInfo["index"] == blocked["index"]):
                    xbmc.log("Item Blocked")
                    return True
        return False

    def showBackgrounds(self, pluginName, pluginHandle, params):
    
        xbmc.log("Shows Backgrounds")
        
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        lastDataPath = __addondir__ + "BlackListedBgLinks.json"
        
        showUrl = params.get("url")
        if(showUrl != None):
            showUrl = urllib.unquote(showUrl)
            #xbmc.Player().play(showUrl)
            return
        
        black_list = []
        
        # load blacklist data
        try:
            dataFile = open(lastDataPath, 'r')
            jsonData = dataFile.read()
            dataFile.close()        
            black_list = json.loads(jsonData)
            xbmc.log("Loaded BL : " + str(black_list))
        except:
            xbmc.log("No Blacklist found, starting with empty BL")
            black_list = []
            
        WINDOW = xbmcgui.Window( 10000 )
        
        filter = params.get("filter")
        if(filter != None):
            WINDOW.setProperty("background_edit_filter", filter)
            xbmc.executebuiltin("Container.Refresh")
            return
            
        filterType = WINDOW.getProperty("background_edit_filter")
        if(filterType == None):
            filterType = "0"

        xbmc.log("Filter Type : " + filterType)
        
        if(params.get("block") != None):

            action = params.get("action")
            index = int(params.get("index"))
            id = params.get("id")
            
            if(action == "remove"):
                newBlackList = []
                
                for blItem in black_list:
                    if(blItem["id"] == id and index == -1):
                        xbmc.log("Removing BL Item : " + str(blItem))
                    elif(blItem["id"] == id and blItem["index"] == index):
                        xbmc.log("Removing BL Item : " + str(blItem))
                    else:
                        newBlackList.append(blItem)
                        
                black_list = newBlackList
                
            else:
                newBlItem = {}
                newBlItem["id"] = id
                newBlItem["index"] = index
                
                found = False
                for blItem in black_list:
                    if(blItem["id"] == newBlItem["id"] and blItem["index"] == newBlItem["index"]):
                        found = True
                        continue
                    elif(blItem["id"] == newBlItem["id"] and blItem["index"] == -1):
                        found = True
                        continue
                        
                # if parent exclude then remove individual excludes
                if(newBlItem["index"] == -1):
                    newBlackList = []
                    for blItem in black_list:
                        if(blItem["id"] != newBlItem["id"]):
                            newBlackList.append(blItem)
                    black_list = newBlackList
            
                if(found == False):
                    xbmc.log("Adding background to BG blacklist : " + str(newBlItem))
                    black_list.append(newBlItem)
                
            stringdata = json.dumps(black_list)
            dataFile = open(lastDataPath, 'w')
            dataFile.write(stringdata)
            dataFile.close()   
            
            #sortOptions = ["SortName", "ProductionYear", "PremiereDate", "DateCreated", "CriticRating", "CommunityRating", "PlayCount", "Budget"]
            #return_value = xbmcgui.Dialog().select("Action", sortOptions)
            
            xbmc.executebuiltin("Container.Refresh")
            return
        
        backgrounds = BackgroundRotationThread()
        backgrounds.updateArtLinks()
        allbackGrounds = backgrounds.global_art_links
        
        dirItems = []
        
        for bg in allbackGrounds:
        
            url = bg["url"]
            name = bg["name"]
            id = bg["id"]
            index = bg["index"]
            list = None
            
            blackListed = self.isBlackListed(black_list, bg)
            commands = []
            
            if(blackListed):
                if(filterType == "0" or filterType == "2"):
                    list = xbmcgui.ListItem("OFF:" + name, iconImage=url, thumbnailImage=url)
                    commands.append(("UnBlock this item", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&block=true&action=remove&id=" + id +"&index=" + str(index) + ")", ))
                    commands.append(("UnBlock parent item", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&block=true&action=remove&id=" + id +"&index=-1)", ))
            else:
                if(filterType == "0" or filterType == "1"):
                    list = xbmcgui.ListItem("ON:" + name, iconImage=url, thumbnailImage=url)
                    commands.append(("Block this item", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&block=true&action=add&id=" + id +"&index=" + str(index) + ")", ))
                    commands.append(("Block parent item", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&block=true&action=add&id=" + id +"&index=-1)", ))
            
            if(list != None):
            
                commands.append(("Show ALL", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&filter=0)", ))
                commands.append(("Show ON", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&filter=1)", ))
                commands.append(("Show OFF", "Container.Update(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BG_EDIT) + "&filter=2)", ))
                list.addContextMenuItems( commands, True )
                
                action_url = pluginName + "?mode=" + str(_MODE_BG_EDIT) + "&url=" + urllib.quote(url)
                dirItems.append((action_url, list, False))
        
 
        if(len(dirItems) > 0):
            dirItems.sort()
            xbmcplugin.addDirectoryItems(pluginHandle, dirItems)
        elif(len(dirItems) == 0 and filterType != "0"):
            WINDOW.setProperty("background_edit_filter", "0")
            
        xbmcplugin.endOfDirectory(pluginHandle,cacheToDisc=False)


