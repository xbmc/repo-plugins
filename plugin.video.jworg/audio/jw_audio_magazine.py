import jw_common
import jw_config

from BeautifulSoup import BeautifulSoup 
import urllib
import sys
import re

import xbmcgui
import xbmcplugin

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
            }
        ]

        # Support for simpliefied study edition of watchtower [english, spanish, ...]
        language = jw_config.language
        if jw_config.const[language]["has_simplified_edition"] == True :
            items.append ({   "title" : jw_common.t(30030),  
                "mode"  : "open_magazine_index",    
                "pub_filter" : "ws" ,
                "year_filter" : "",
            })

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

        title_text  = jw_common.cleanUpText( item["title"] )
        listItem    = xbmcgui.ListItem( title_text )     

        params      = {
            "content_type"  : "audio", 
            "mode"          : item["mode"],
            "pub_filter"	: item["pub_filter"],
            "year_filter"   : item["year_filter"]
        } 

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(
            handle      = jw_config.plugin_pid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )  
    
    xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


def showMagazineFilteredIndex(pub_filter = None, year_filter = None):

    language        = jw_config.language

    magazine_url    = jw_common.getUrl(language) 
    magazine_url    = magazine_url + jw_config.const[language]["magazine_index"] 
    magazine_url    = magazine_url + "?pubFilter=" + pub_filter .strip() + "&yearFilter=" + year_filter.strip()
    
    html            = jw_common.loadUrl(magazine_url) 

    soup            = BeautifulSoup(html)
    publications    = soup.findAll("div", { "class" : re.compile(r'\bPublicationIssue\b') })

    for publication in publications :

        cover_title = publication.find("span", { "class" : re.compile(r'\bperiodicalTitleBlock\b') })

        issue_date = cover_title.find("span", { "class" : re.compile(r'\bissueDate\b') }).contents[0].encode("utf-8")
        issue_date = jw_common.cleanUpText(issue_date)
        try :
            # wp and g
            issue_title = cover_title.find("span", { "class" : re.compile(r'\bcvrTtl\b') }).contents[0].encode("utf-8")
        except :
            # w (study edtion)
            issue_title = cover_title.find("span", { "class" : re.compile(r'\bpubName\b') }).contents[0].encode("utf-8")

        issue_title = jw_common.cleanUpText(issue_title)

        json_url = None
        try :
            json_url = publication.find("a", { "class" : re.compile(r'\bstream\b') }).get('data-jsonurl')
        except :
            pass

        # placeholder if cover is missing
        cover_url = "http://assets.jw.org/themes/content-theme/images/thumbProduct_placeholder.jpg"
        try :
            cover_url = publication.findAll("img")[1].get('src')
        except :
            pass 

        listItem    = xbmcgui.ListItem( 
            label           = issue_date + ": " + issue_title,
            thumbnailImage  = cover_url
        ) 

        params      = {
            "content_type"  : "audio", 
            "mode"          : "open_magazine_json",
            "json_url"      : json_url,
        } 

        url = jw_config.plugin_name + '?' + urllib.urlencode(params)

        xbmcplugin.addDirectoryItem(
            handle      = jw_config.plugin_pid, 
            url         = url, 
            listitem    = listItem, 
            isFolder    = True 
        )

    xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
