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

import os, sys
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import data as Data
from data import DataItem

_ = xbmcaddon.Addon(id="plugin.video.nrk").getLocalizedString

def nodes(baseUrl, handle):
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=live",    xbmcgui.ListItem(_(30101)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=latest",  xbmcgui.ListItem(_(30102)), True);
    xbmcplugin.addDirectoryItem(handle, baseUrl+"?node=letters", xbmcgui.ListItem("A-Å"), True);
    xbmcplugin.endOfDirectory(handle)

def node_live(baseUrl, handle):
    dataItems = Data.getLive()
    create(baseUrl, handle, dataItems)
    
def node_latest(baseUrl, handle):
    dataItems = Data.getLatest()
    create(baseUrl, handle, dataItems)

def node_url(baseUrl, handle, url):
    dataItems = Data.getByUrl(url)
    create(baseUrl, handle, dataItems)
    
def node_letter(baseUrl, handle, letter):
    dataItems = Data.getByLetter(letter)
    create(baseUrl, handle, dataItems)
    
def node_letters(baseUrl, handle):
    #TODO: move this to data layer
    letters = range(ord('a'), ord('z'))
    letters.append(ord('1'))
    letters.append(ord('2'))
    letters.append(ord('3'))
    letters.append(ord('7'))
    letters.append(230) #æ
    letters.append(216) #ø
    letters.append(229) #å
      
    listItems = []
    for l in letters:
        ch = unichr(l)
        url = baseUrl + "?letter=" + ch
        listItems.append( (url, xbmcgui.ListItem(ch.upper()), True) )
    
    xbmcplugin.addDirectoryItems(handle=handle, items=listItems)
    xbmcplugin.endOfDirectory(handle)
    
def create(baseUrl, handle, dataItems):
    listItems = []
    for e in dataItems:
        l = xbmcgui.ListItem(e.title)
        l.setInfo( type="Video", infoLabels={"title": e.title} )
        l.setProperty("IsPlayable", str(e.isPlayable));
        isdir = not(e.isPlayable)
        if isdir: url = baseUrl + "?url=" + e.url
        else: url = e.url
        listItems.append( (url, l, isdir) )
    xbmcplugin.addDirectoryItems(handle=handle, items=listItems)
    xbmcplugin.endOfDirectory(handle)
    

if ( __name__ == "__main__" ):
    arg = sys.argv[2].split('=', 1)

    if (arg[0] == "?node"):
        if(arg[1] == "live"):
            node_live(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "letters"):
            node_letters(sys.argv[0], int(sys.argv[1]))
        elif(arg[1] == "latest"):
            node_latest(sys.argv[0], int(sys.argv[1]))
    
    elif (arg[0] == "?letter"):
        node_letter(sys.argv[0], int(sys.argv[1]), arg[1])
        
    elif (arg[0] == "?url"):
        node_url(sys.argv[0], int(sys.argv[1]), arg[1])
    
    else:
        nodes(sys.argv[0], int(sys.argv[1]))
    
