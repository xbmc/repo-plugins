import sys
import xbmc
import xbmcgui
import xbmcplugin
import urllib
import json
import os
import time
import datetime
import xbmcaddon
import urllib2
import traceback
from traceback import print_exc

__settings__ = xbmcaddon.Addon(id='plugin.video.sbview')
language = __settings__.getLocalizedString

handle = int(sys.argv[1])
dateFormat = "%I:%M %p %a %d %b %Y" 
#"%a %I:%M %p %Y/%m/%d"

# plugin modes
MODE_VIEW_FUTURE = 10
MODE_VIEW_HISTORY = 20
MODE_VIEW_SHOWS = 30
MODE_VIEW_SEASONS = 40
MODE_VIEW_EPISODES = 50
MODE_VIEW_EPISODE_INFO = 60

# parameter keys
PARAMETER_KEY_MODE = "mode"
PARAMETER_KEY_SHOWID = "show_id"
PARAMETER_KEY_SEASON_NUM = "season_num"
PARAMETER_KEY_EPISODE_NUM = "episode_num"

def log(line):
    #print "SBVIEW : " + line#repr(line)
    xbmc.log("SBVIEW : " + line, 0)
        
    #xbmc.log("Test", 0) #Debug
    #xbmc.log("text", 1) #Info
    #xbmc.log("Test", 2) #Notive

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                log("Param " + paramSplits[0] + "=" + paramSplits[1])
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def addDirectoryItem(name, isFolder=True, parameters={}, totalItems=1, thumbnail=""):
    
    if(thumbnail == ""):
        li = xbmcgui.ListItem(name)
    else:
        li = xbmcgui.ListItem(name, thumbnailImage=thumbnail)
    
    commands = []
    #commands.append(( "Info", "XBMC.Action(Info)", ))
    #commands.append(( "Scan", "XBMC.updatelibrary(video, '" + name + "')", ))
    #commands.append(( 'TEST', 'ActivateWindow(videolibrary, '" + name "')', ))
    #commands.append(( 'runme', 'XBMC.RunPlugin(plugin://video/myplugin)', ))
    #commands.append(( 'runother', 'XBMC.RunPlugin(plugin://video/otherplugin)', ))
    #commands.append(( "Scan", "ActivateWindow(videofiles, Movies)", ))#, '" + name + "')", ))
    li.addContextMenuItems(commands, replaceItems = True)
    
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)

    if not isFolder:
        url = name
        
    #log("Adding Directory Item: " + name + " totalItems:" + str(totalItems))
    
    #dirItem = DirectoryItem()
    
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder, totalItems=totalItems)

def show_root_menu():

    addDirectoryItem(name=language(30110), parameters={ PARAMETER_KEY_MODE: MODE_VIEW_SHOWS }, isFolder=True)
    addDirectoryItem(name=language(30111), parameters={ PARAMETER_KEY_MODE: MODE_VIEW_FUTURE }, isFolder=True)
    addDirectoryItem(name=language(30112), parameters={ PARAMETER_KEY_MODE: MODE_VIEW_HISTORY }, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def get_api_result(sbUrl):

    try:
    
        apiResponce = urllib2.urlopen(sbUrl)
        apiDataString = apiResponce.read()
        apiResponce.close()

        result = eval(apiDataString)
        
        resultString = result.get("result")
        resultMessage = result.get("message")
        
        if(resultString != "success"):
            xbmcgui.Dialog().ok("API Request Error", resultString, resultMessage)
            log(resultString + " - " + resultMessage)
        
        return result
        
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #formatted_lines = traceback.format_exc().splitlines()
        xbmcgui.Dialog().ok("API Request Error", str(exc_type), str(exc_value))
        log(str(exc_type) + " - " + str(exc_value))
        return {}
    
def view_shows():

    sbUrl = get_sb_url()
    sbUrl += "?cmd=shows"
    
    result = get_api_result(sbUrl)
    
    data = result.get('data')
    if(data == None):
        data = []
        
    show_list = []   
    
    for item in data:
        show_name = result["data"][item]["show_name"]
        show_tvdbid = result["data"][item]["tvdbid"]        
        show = {}
        show["name"] = show_name
        show["tvdbid"] = show_tvdbid
        show_list.append(show)
        
    show_list = sorted(show_list)
    
    for item in show_list:
        name = item["name"]
        id = item["tvdbid"]
        thumbnailUrl = get_thumbnail_url(id)
        addDirectoryItem(name, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_SEASONS, PARAMETER_KEY_SHOWID: id }, isFolder=True, thumbnail=thumbnailUrl)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def view_episode_info():

    show_id = params.get(PARAMETER_KEY_SHOWID, "0")
    season_num = params.get(PARAMETER_KEY_SEASON_NUM, "0")
    episode_num = params.get(PARAMETER_KEY_EPISODE_NUM, "0")
    
    sbUrl = get_sb_url()
    sbUrl += "?cmd=episode&tvdbid=" + show_id + "&season=" + season_num + "&episode=" + episode_num + "&full_path=1"
    
    result = get_api_result(sbUrl)
    
    data = result.get('data')
    if(data == None):
        data = []       
    
    line01 = "Air Date : " + data["airdate"]
    line02 = "Status   : " + data["status"] + " - " + data["quality"] + " - " + data["file_size_human"]
    line03 = data["location"]
    
    if(line03 != "" and line03.rfind('\\') > 0):
        line03 = line03[line03.rfind('\\')+1:]
    
    xbmcgui.Dialog().ok("Episode Info", line01, line02, line03)

def view_episodes():

    show_id = params.get(PARAMETER_KEY_SHOWID, "0")
    season_num = params.get(PARAMETER_KEY_SEASON_NUM, "0")
    
    sbUrl = get_sb_url()
    sbUrl += "?cmd=show.seasons&tvdbid=" + show_id + "&season=" + season_num
    
    result = get_api_result(sbUrl)
    
    data = result.get('data')
    if(data == None):
        data = []    
    
    show_list_numbers = []
    for item in data:
        show_list_numbers.append(int(item))
        
    show_list_numbers = sorted(show_list_numbers)
    
    for showNum in show_list_numbers:
        epp_name = data[str(showNum)]["name"]
        epp_status = data[str(showNum)]["status"]
        epp_number = season_num + "x" + str(showNum)
        thumbnailUrl = get_thumbnail_url(show_id)
        addDirectoryItem(epp_number + " " + epp_name + " (" + epp_status + ")", parameters={ PARAMETER_KEY_MODE: MODE_VIEW_EPISODE_INFO, PARAMETER_KEY_SHOWID: show_id, PARAMETER_KEY_SEASON_NUM: season_num, PARAMETER_KEY_EPISODE_NUM: str(showNum) }, isFolder=True, thumbnail=thumbnailUrl)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def view_seasons():
    
    show_id = params.get(PARAMETER_KEY_SHOWID, "0")
    
    sbUrl = get_sb_url()
    sbUrl += "?cmd=show.seasonlist&tvdbid=" + show_id
    
    result = get_api_result(sbUrl)
    
    data = result.get('data')
    if(data == None):
        data = []

    season_list = []
    for season in data:
        season_list.append(int(season))
        
    season_list = sorted(season_list)
    
    for season in season_list:
        season_num = str(season)
        thumbnailUrl = get_thumbnail_url(show_id)
        addDirectoryItem("Season " + season_num, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_EPISODES, PARAMETER_KEY_SHOWID: show_id, PARAMETER_KEY_SEASON_NUM: season_num }, isFolder=True, thumbnail=thumbnailUrl)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def get_sb_url():

    prot = xbmcplugin.getSetting(handle, "prot")
    if(prot == "0"):
        sbUrl = "http://"
    elif(prot == "1"):
        sbUrl = "https://"
        
    host = xbmcplugin.getSetting(handle, "host")
    sbUrl += host
    
    port = xbmcplugin.getSetting(handle, "port")
    sbUrl += ":" + port    
    
    sbUrl += "/api/"
    
    guid = xbmcplugin.getSetting(handle, "guid")
    
    sbUrl += guid + "/"
    
    return sbUrl
    
def get_thumbnail_url(show_id):
 
    sbUrl = get_sb_url()
    sbUrl += "?cmd=show.getposter&tvdbid=" + str(show_id)
    
    return sbUrl
    
def view_future():

    sbUrl = get_sb_url()
    sbUrl += "future"
    
    result = get_api_result(sbUrl)
    
    data = result.get('data')
    if(data == None):
        data = []
    
    # process the missed
    missed = data.get('missed')
    if(missed == None):
        missed = []

    for item in missed:
        airDate = str(item["airdate"]) + " " + str(item["airs"])
        airTime = time.strptime(airDate, "%Y-%m-%d %A %I:%M %p")
        airTimeString = time.strftime(dateFormat, airTime)
        nameString = "Missed - " + str(item["show_name"]) + " " + str(item["season"]) + "x" + str(item["episode"]) + " - " + str(airTimeString)
        thumbnailUrl = get_thumbnail_url(item["tvdbid"])
        addDirectoryItem(nameString, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_FUTURE }, isFolder=True, thumbnail=thumbnailUrl)
        
    # process the soon
    soon = data.get('soon')
    if(soon == None):
        soon = []

    for item in soon:
        airDate = str(item["airdate"]) + " " + str(item["airs"])
        airTime = time.strptime(airDate, "%Y-%m-%d %A %I:%M %p")
        airTimeString = time.strftime(dateFormat, airTime)
        nameString = "Soon - " + str(item["show_name"]) + " " + str(item["season"]) + "x" + str(item["episode"]) + " - " + str(airTimeString)
        thumbnailUrl = get_thumbnail_url(item["tvdbid"])
        addDirectoryItem(nameString, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_FUTURE }, isFolder=True, thumbnail=thumbnailUrl)
        
    # process the soon
    later = data.get('later')
    if(later == None):
        later = []

    for item in later:
        airDate = str(item["airdate"]) + " " + str(item["airs"])
        airTime = time.strptime(airDate, "%Y-%m-%d %A %I:%M %p")
        airTimeString = time.strftime(dateFormat, airTime)
        nameString = "Later - " + str(item["show_name"]) + " " + str(item["season"]) + "x" + str(item["episode"]) + " - " + str(airTimeString)
        thumbnailUrl = get_thumbnail_url(item["tvdbid"])
        addDirectoryItem(nameString, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_FUTURE }, isFolder=True, thumbnail=thumbnailUrl)

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def view_history():

    sbUrl = get_sb_url()
    sbUrl += "history/?limit=20"
    
    result = get_api_result(sbUrl)

    data = result.get('data')
    if(data == None):
        data = []

    for item in data:
        nameString = str(item["date"]) + " - " + str(item["show_name"]) + " " + str(item["season"]) + "x" + str(item["episode"]) + " - " + str(item["status"])
        thumbnailUrl = get_thumbnail_url(item["tvdbid"])
        addDirectoryItem(nameString, parameters={ PARAMETER_KEY_MODE: MODE_VIEW_HISTORY }, isFolder=True, thumbnail=thumbnailUrl)

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
# set up all the variables
params = parameters_string_to_dict(sys.argv[2])
mode = int(urllib.unquote_plus(params.get(PARAMETER_KEY_MODE, "0")))

# Depending on the mode do stuff
if not sys.argv[2]:
    ok = show_root_menu()
elif mode == MODE_VIEW_FUTURE:
    ok = view_future()
elif mode == MODE_VIEW_HISTORY:
    ok = view_history()
elif mode == MODE_VIEW_SHOWS:
    ok = view_shows()
elif mode == MODE_VIEW_SEASONS:
    ok = view_seasons()    
elif mode == MODE_VIEW_EPISODES:
    ok = view_episodes()        
elif mode == MODE_VIEW_EPISODE_INFO:
    ok = view_episode_info()        

