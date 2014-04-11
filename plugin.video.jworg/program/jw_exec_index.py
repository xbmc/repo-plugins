import datetime
import urllib

import jw_config
import jw_common

import xbmcgui
import xbmcplugin

# List of available executable  services
def showExecIndex():

    language        = jw_config.language

    # 1. Dailiy Text
    now             = datetime.datetime.now()
    date_for_json   = str(now.year) + "/" + str(now.month) + "/" + str(now.day)
    date_format     = jw_config.const[language]["date_format"]
    title           = jw_common.t(30012)  + " - " + now.strftime(date_format)
    listItem        = xbmcgui.ListItem( title )
    params          = {
        "content_type"  : "executable", 
        "mode"          : "open_daily_text",
        "date"          : date_for_json
    } 
    url = jw_config.plugin_name + '?' + urllib.urlencode(params)
    xbmcplugin.addDirectoryItem(
        handle      = jw_config.plugin_pid, 
        url         = url, 
        listitem    = listItem, 
        isFolder    = False 
    )  

    # 2. Week program
    title           = jw_common.t(30034)  
    listItem        = xbmcgui.ListItem( title )
    params          = {
        "content_type"  : "executable", 
        "mode"          : "open_week_program",
        "date"          : date_for_json
    } 
    url = jw_config.plugin_name + '?' + urllib.urlencode(params)
    xbmcplugin.addDirectoryItem(
        handle      = jw_config.plugin_pid, 
        url         = url, 
        listitem    = listItem, 
        isFolder    = False
    )   
    
    # 3. News
    title           = jw_common.t(30032)  
    listItem        = xbmcgui.ListItem( title )
    params          = {
        "content_type"  : "executable", 
        "mode"          : "open_news_index",
    } 
    url = jw_config.plugin_name + '?' + urllib.urlencode(params)
    xbmcplugin.addDirectoryItem(
        handle      = jw_config.plugin_pid, 
        url         = url, 
        listitem    = listItem, 
        isFolder    = True
    )  
          
    # 4. Activities
    title           = jw_common.t(30037)  
    listItem        = xbmcgui.ListItem( title )
    params          = {
        "content_type"  : "executable", 
        "mode"          : "open_activity_index",
    } 
    url = jw_config.plugin_name + '?' + urllib.urlencode(params)
    xbmcplugin.addDirectoryItem(
        handle      = jw_config.plugin_pid, 
        url         = url, 
        listitem    = listItem, 
        isFolder    = True
    )      

    xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
