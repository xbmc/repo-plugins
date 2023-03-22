from __future__ import print_function

import xbmc,xbmcgui

#main plugin library

from resources.lib import gui
from resources.lib.art_clean import clean_cache_art
from resources.lib import utils as ut
from resources.lib import json_storage
from resources.lib import ampache_connect

def initializeServer():
    jsStorServer = json_storage.JsonStorage("servers.json")
    serverData = jsStorServer.getData()
    if serverData:
        pass
    else:
        xbmc.log( "AmpachePlugin::initializeServer: no servers file",xbmc.LOGDEBUG)
        serverData["servers"] = {}
        tempd = {}
        tempd["0"] = {}
        serverData["servers"].update(tempd)
        serverData["servers"]["0"]["name"] = "Develop Demo"
        serverData["servers"]["0"]["url"] = "http://develop.ampache.dev/"
        serverData["servers"]["0"]["use_api_key"] = "false"
        serverData["servers"]["0"]["enable_password"] = "true"
        serverData["servers"]["0"]["username"] = "kodi_demo"
        serverData["servers"]["0"]["password"] = "aNNKvApsECw7Tpc"
        serverData["servers"]["0"]["api_key"] = ""
        serverData["current_server"] = "0"
        jsStorServer.save(serverData)
 

#input: serverData and title
#output: number of server in data
def serversDialog(data,title=''):
    templist = []
    showlist = []
    dialog = xbmcgui.Dialog()
    for i in data["servers"]:
        item = data["servers"][i]["name"]
        if i == data["current_server"]:
            item = item + " *" 
        showlist.append(item)
        templist.append(data["servers"][i]["name"])
    ret = dialog.select(title, showlist)
    i_temp= ""
    if ret == -1:
        return False
    for i in data["servers"]:
        if(data["servers"][i]["name"]) == templist[ret]:
            i_temp = i
    return i_temp 

def showServerData(data,title=ut.tString(30168)):
    padding_size = 20
    #order of the data
    ordlist = ["name","url","username","enable_password","password","use_api_key","api_key"]
    #name to display
    dispList = [ut.tString(30181),ut.tString(30182),ut.tString(30183),ut.tString(30184),ut.tString(30185),ut.tString(30186),ut.tString(30187)]
    templist = []
    showlist = []
    n = 0
    dialog = xbmcgui.Dialog()
    for i in ordlist:
        templist.append(i)
        pad_i =  dispList[n] + " "*(padding_size - len(i))
        tempStr = pad_i + data[i]
        showlist.append(tempStr)
        n = n + 1
    ret = dialog.select(title, showlist)
    i_temp= ""
    if ret == -1:
        return False
    for i in data:
        if i == templist[ret]:
            i_temp = i
    return i_temp

def switchServer():
    jsStorServer = json_storage.JsonStorage("servers.json")
    serverData = jsStorServer.getData()
    i_curr = serversDialog(serverData,ut.tString(30169))
    if i_curr == False:
        return
    xbmc.executebuiltin("PlayerControl(Stop)")
    serverData["current_server"] = i_curr
    jsStorServer.save(serverData)
    #clean cache_art, the server is different, so the cache is invalid
    clean_cache_art()
    #if we switch, reconnect
    try:
        ampacheConnect = ampache_connect.AmpacheConnect()
        ampacheConnect.AMPACHECONNECT(showok=True)
    except:
        pass

def addServer():
    xbmc.log("AmpachePlugin::addServer" , xbmc.LOGDEBUG )
    jsStorServer = json_storage.JsonStorage("servers.json")
    serverData = jsStorServer.getData()
    if len(list(serverData["servers"])) > 0:
        #choose the max number of the server list plus one
        stnum = str(max([int(i) for i in list(serverData["servers"])])+1)
    else:
        #empty list
        stnum = "0"
    username = ""
    password = ""
    apikey = ""
    enablepassword = True
    is_api_key = False
    tempd = {}
    tempd[stnum] = {}
    serverData["servers"].update(tempd)
    servername = gui.getFilterFromUser(ut.tString(30170))
    if servername == False:
        return False
    url = gui.getFilterFromUser(ut.tString(30171))
    if url == False:
        return False
    dialog = xbmcgui.Dialog()
    is_api_key = dialog.yesno(ut.tString(30189),ut.tString(30173))
    if is_api_key == True:
        apikey = gui.getFilterFromUser(ut.tString(30174))
        if apikey == False:
            return False
    else:
        username = gui.getFilterFromUser(ut.tString(30175))
        if username == False:
            return False
        enablepassword = dialog.yesno(ut.tString(30189),ut.tString(30177))
        if enablepassword == True:
            password = gui.getFilterFromUser(ut.tString(30178))
            if password == False:
                return False
    serverData["servers"][stnum]["name"] = servername
    serverData["servers"][stnum]["url"] = url
    serverData["servers"][stnum]["use_api_key"] = ut.int_to_strBool(is_api_key)
    serverData["servers"][stnum]["username"] = username
    serverData["servers"][stnum]["enable_password"] = ut.int_to_strBool(enablepassword)
    serverData["servers"][stnum]["password"] = password
    serverData["servers"][stnum]["api_key"] = apikey
    jsStorServer.save(serverData)
    showServerData(serverData["servers"][stnum])
    return True
    
def deleteServer():
    jsStorServer = json_storage.JsonStorage("servers.json")
    serverData = jsStorServer.getData()
    i_rem = serversDialog(serverData,ut.tString(30179))
    if i_rem == False:
        return False
    dialog = xbmcgui.Dialog()
    confirm = dialog.yesno(ut.tString(30189),ut.tString(30188))
    if confirm:
        #replace old server position with the latest server in the list
        repl_num = str(max([int(i) for i in list(serverData["servers"])]))
        serverData["servers"][i_rem] = serverData["servers"][repl_num].copy()
        del serverData["servers"][repl_num]
        jsStorServer.save(serverData)
        return True
    else:
        return False

def modifyServer():
    jsStorServer = json_storage.JsonStorage("servers.json")
    serverData = jsStorServer.getData()
    i = serversDialog(serverData,ut.tString(30180))
    if i == False:
        return
    while True:
        if xbmc.Monitor().abortRequested():
            return
        key = showServerData(serverData["servers"][i])
        if key == False:
            break
        elif key == "use_api_key":
            dialog = xbmcgui.Dialog()
            value_int = dialog.yesno(ut.tString(30189),ut.tString(30173))
            value = ut.int_to_strBool(value_int)
        elif key == "enable_password":
            dialog = xbmcgui.Dialog()
            value_int = dialog.yesno(ut.tString(30189),ut.tString(30177))
            value = ut.int_to_strBool(value_int)
        elif key == "name":
            value = gui.getFilterFromUser(ut.tString(30181))
        elif key == "url":
            value = gui.getFilterFromUser(ut.tString(30182))
        elif key == "username":
            value = gui.getFilterFromUser(ut.tString(30183))
        elif key == "password":
            value = gui.getFilterFromUser(ut.tString(30185))
        elif key == "api_key":
            value = gui.getFilterFromUser(ut.tString(30187))
        else:
            pass
        if value != False:
            serverData["servers"][i][key] = value
    xbmc.executebuiltin("PlayerControl(Stop)")
    jsStorServer.save(serverData)
    #just to be sure, having potentially changed default server
    try:
        ampacheConnect = ampache_connect.AmpacheConnect()
        ampacheConnect.AMPACHECONNECT()
    except:
        pass
