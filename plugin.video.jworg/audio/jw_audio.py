import xbmc
import xbmcgui
import xbmcplugin

import urllib

import jw_config
import jw_common

# List of available audio services
def showAudioIndex():
    
    items = [
        {"title" : jw_common.t(30010),
            "mode"  : "open_bible_index",
            "enable" :  jw_config.const[jw_config.language]["bible_index_audio"],
            "start" : None },
        {"title" : jw_common.t(30025),
            "mode"  : "open_magazine_index",
            "enable" : jw_config.const[jw_config.language]["magazine_index"],
            "start" : None },
        {"title" : jw_common.t(30011),
            "mode"  : "open_music_index",
            "enable" : True,
            "start" : 0 },
        {"title" : jw_common.t(30013),
            "mode"  : "open_drama_index",
            "enable" : True,
            "start" : 0 },
        {"title" : jw_common.t(30014),
            "mode"  : "open_dramatic_reading_index",   
            "enable" : True,
            "start" : 0 },
    ]

    for item in items:

        # Case Afrikaans: has no bible audio !
        if item["enable"] == False :
            continue;

        listItem    = xbmcgui.ListItem( item["title"] )     
        params      = {
            "content_type"  : "audio", 
            "mode"          : item["mode"]
        } 
        if item["start"] is not None:
            params["start"] = item["start"]

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(
            handle      = jw_config.plugin_pid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )  
    
    xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


# Track list
# Used by magazine, musics, dramas, and dramatic bible reading
# Not used by bible
def showAudioJson(json_url):

    language        = jw_config.language
    language_code   = jw_config.const[language]["lang_code"]
    json_url        = "http://www.jw.org" + json_url
    json            = jw_common.loadJsonFromUrl(url = json_url, ajax = False)
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
            handle      = jw_config.plugin_pid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = False
        )  

    # If there is only one audio item in the json, I start playing
    # Otherwise the standard item list will be generated
    if len(json["files"][language_code]["MP3"]) == 1 :

        xbmc.Player().play(item=url, listitem=listItem)
        return;


    xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)    