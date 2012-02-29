# -*- coding: utf-8 -*-
'''
    NRK plugin for XBMC
    Copyright (C) 2010 Thomas Amland

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import data as Data
from data import DataItem

addon = xbmcaddon.Addon(id="plugin.video.nrk")
Data.setQuality(int(addon.getSetting("quality")))
_ = addon.getLocalizedString

def nodes(baseUrl, handle):
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=live",     xbmcgui.ListItem(_(30101)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=letters",  xbmcgui.ListItem(_(30103)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=genres",   xbmcgui.ListItem(_(30104)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=latest",   xbmcgui.ListItem(_(30102)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=topweek",  xbmcgui.ListItem(_(30106)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=topmonth", xbmcgui.ListItem(_(30107)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=toptotal", xbmcgui.ListItem(_(30108)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=search",   xbmcgui.ListItem(_(30105)), True);
    xbmcplugin.endOfDirectory(handle)

def node_live(baseUrl, handle):
    dataItems = Data.getLive()
    create(baseUrl, handle, dataItems)
    
def node_latest(baseUrl, handle):
    dataItems = Data.getLatest()
    create(baseUrl, handle, dataItems)
    
def node_letters(baseUrl, handle):
    dataItems = Data.getLetters()
    create(baseUrl, handle, dataItems)
    
def node_genres(baseUrl, handle):
    dataItems = Data.getGenres()
    create(baseUrl, handle, dataItems)
    
def node_topWeek(baseUrl, handle):
    dataItems = Data.getMostWatched(7)
    create(baseUrl, handle, dataItems)
    
def node_topMonth(baseUrl, handle):
    dataItems = Data.getMostWatched(30)
    create(baseUrl, handle, dataItems)
    
def node_topTotal(baseUrl, handle):
    dataItems = Data.getMostWatched(9999)
    create(baseUrl, handle, dataItems)
    
def node_search(baseUrl, handle):
    kb = xbmc.Keyboard()
    kb.doModal()
    if (kb.isConfirmed()):
        text = kb.getText()
        dataItems = Data.getSearchResults(text)
        create(baseUrl, handle, dataItems)

def node_url(baseUrl, handle, url):
    dataItems = Data.getByUrl(url)
    create(baseUrl, handle, dataItems)
    
    
def create(baseUrl, handle, dataItems):
    listItems = []
    for e in dataItems:
        l = xbmcgui.ListItem(e.title, thumbnailImage=e.thumb)
        l.setInfo( type="Video", infoLabels={"title": e.title, "plot":e.description, "tvshowtitle":e.title} )
        l.setProperty("IsPlayable", str(e.isPlayable))
        
        isdir = not(e.isPlayable)
        if isdir:
            url = baseUrl + "?url=" + e.url
        else:
            url = e.url
        listItems.append( (url, l, isdir) )
        
    xbmcplugin.addDirectoryItems(handle=handle, items=listItems)
    xbmcplugin.endOfDirectory(handle)
    

if ( __name__ == "__main__" ):
    #using episodes because most skins expects 16/9 thumbs for this
    xbmcplugin.setContent(int(sys.argv[1]), "episodes")
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    
    arg = sys.argv[2].split('=', 1)

    if (arg[0] == "?node"):
        if(arg[1] == "live"):
            node_live(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "letters"):
            node_letters(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "latest"):
            node_latest(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "genres"):
            node_genres(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "search"):
            node_search(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "topweek"):
            node_topWeek(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "topmonth"):
            node_topMonth(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "toptotal"):
            node_topTotal(sys.argv[0], int(sys.argv[1]))
    
    elif (arg[0] == "?url"):
        node_url(sys.argv[0], int(sys.argv[1]), arg[1])
    
    else:
        xbmcplugin.setContent(int(sys.argv[1]), "files")
        nodes(sys.argv[0], int(sys.argv[1]))
