import jw_common
import jw_config

import urllib
import sys
import re

import xbmcgui
import xbmcplugin

print sys.argv

def showMagazineFilterIndex(pub_filter = None):

    if pub_filter is None:

        items = [
            {   "title" : jw_common.t(30026),  
                "mode"  : "open_magazine_index",    
                "pub_filter" : " " ,
                "year_filter" : "",
            },
            {   "title" : jw_common.t(30027),  
                "mode"  : "open_magazine_index",    
                "pub_filter" : "g"  ,
                "year_filter" : "",
            },
            {   "title" : jw_common.t(30028),  
                "mode"  : "open_magazine_index",    
                "pub_filter" : "wp" ,
                "year_filter" : "",
            },
            {   "title" : jw_common.t(30029),  
                "mode"  : "open_magazine_index", 	
                "pub_filter" : "w"  ,
                "year_filter" : "",
            },
            {   "title" : jw_common.t(30030),  
                "mode"  : "open_magazine_index",    
                "pub_filter" : "ws" ,
                "year_filter" : "",
            },
        ]

    if pub_filter is not None :

        items = []

        for year in [" ", "2014", "2013", "2012"]: 
            title = year
            if title == " " :
                title = jw_common.t(30031)

            items.append ({  
                "title"         : title,  
                "mode"          : "open_magazine_index",    
                "pub_filter"    : pub_filter,
                "year_filter"   : year
            })

    for item in items:

        if item["title"] == "-" :
            continue

        listItem    = xbmcgui.ListItem( item["title"] )     

        params      = {
            "content_type"  : "audio", 
            "mode"          : item["mode"],
            "pub_filter"	: item["pub_filter"],
            "year_filter"   : item["year_filter"]
        } 

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(
            handle      = jw_config.pluginPid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )  
    
    xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)


def showMagazineFilteredIndex(pub_filter = None, year_filter = None):

    language        = jw_config.language
    magazine_url    = jw_config.const[language]["magazine_index"] + "?pubFilter=" + pub_filter .strip() + "&yearFilter=" + year_filter.strip()
    html            = jw_common.loadUrl(magazine_url) 

    # Grep issue date and publication title
    regexp_issue = "<span class='issueDate'>([^<]+)</span> (<span class='cvrTtl'>([^<]+)</span>)?"
    issues = re.findall(regexp_issue, html)      

    # The following regexp use two 'generic spaces' \s to filter out unwanted items
    regexp_json = '\s\sdata-jsonurl="([^"]+)"'
    json = re.findall(regexp_json, html)

    # Cover
    regexp_cover = "data-img-size-md='(http://assets.jw.org/assets/[^.]+md\.jpg)'"
    cover = re.findall(regexp_cover, html)

    count = 0
    for issue in issues:

        title = issue[0]
        if issue[2].strip() != "":
            title = title + " - " + issue[2]

        listItem    = xbmcgui.ListItem( 
            label           = title,
            thumbnailImage  = cover[count]
        )     

        params      = {
            "content_type"  : "audio", 
            "mode"          : "open_magazine_json",
        } 
        try:
            params["json_url"] = json[count]
        except:
            params["json_url"] = None

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)

        xbmcplugin.addDirectoryItem(
            handle      = jw_config.pluginPid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )  

        count = count +1
    
    xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)