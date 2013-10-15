import xbmcgui
import xbmcplugin

import urllib

import jw_config
import jw_common

# List of available audio services
def showAudioIndex():
    
    items = [
        {"title" : jw_common.t(30010),  "mode"  : "open_bible_index",            "start" : None },
        {"title" : jw_common.t(30025),  "mode"  : "open_magazine_index",         "start" : None },
        {"title" : jw_common.t(30011),  "mode"  : "open_music_index",            "start" : 0 },
        {"title" : jw_common.t(30013),  "mode"  : "open_drama_index",            "start" : 0 },
        {"title" : jw_common.t(30014),  "mode"  : "open_dramatic_reading_index", "start" : 0 },
    ]

    for item in items:
        listItem    = xbmcgui.ListItem( item["title"] )     
        params      = {
            "content_type"  : "audio", 
            "mode"          : item["mode"]
        } 
        if item["start"] is not None:
            params["start"] = item["start"]

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(
            handle      = jw_config.pluginPid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )  
    
    xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)


# Track list
def showAudioJson(json_url):

    language        = jw_config.language
    language_code   = jw_config.const[language]["lang_code"]
    json_url        = "http://www.jw.org" + json_url
    json            = jw_common.loadJsonFromUrl(json_url)
    cover_image     = json["pubImage"]["url"]
    
    for mp3 in json["files"][language_code]["MP3"]:
        url     = mp3["file"]["url"]
        title   = jw_common.cleanUpText(mp3["title"])

        # Skip 'zip' files
        if mp3["mimetype"] != "audio/mpeg":
            continue;

        listItem = xbmcgui.ListItem(
            label           = title,
            thumbnailImage  = cover_image
        )

        listItem.setInfo(
            type        = 'Music', 
            infoLabels  = {'Title': title }
        )

        xbmcplugin.addDirectoryItem(
            handle      = jw_config.pluginPid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = False
        )  

    xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)    