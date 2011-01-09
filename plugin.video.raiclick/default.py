'''
    RaiClick for XBMC 1.1.1
    Copyright (C) 2005-2011 Angelo Conforti <angeloxx@angeloxx.it>
    http://www.angeloxx.it
    
    Lo script e' un semplice browser del sito rai.tv, tutti i diritti
    sono di proprieta' della RAI
    
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

import sys, xbmc, xbmcaddon, xbmcgui, urllib, xbmcplugin
import raiclicklib

# plugin constants
__version__ = "1.1.0"
__plugin__ = "RAIClick-" + __version__
__author__ = "angeloxx"
__url__ = "www.xbmc.com"
__svn_url__ = ""
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = "34731"
__settings__ = xbmcaddon.Addon(id='plugin.video.raiclick')
__language__ = __settings__.getLocalizedString
__dbg__ = __settings__.getSetting( "debug" ) == "true"


    
def addDir(name,url,mode):
  u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
  ok=True
  liz=xbmcgui.ListItem(name)
  liz.setInfo( type="Video", infoLabels={ "Title": name} )
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok  

def addLink(name,url,mode):
  u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
  ok=True
  liz=xbmcgui.ListItem(name)
  liz.setInfo( type="Video", infoLabels={ "Title": name} )
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
  return ok    

def getParameters(parameterString):
  commands = {}
  splitCommands = parameterString[parameterString.find('?')+1:].split('&')
  for command in splitCommands:
    if (len(command) > 0):
      splitCommand = command.split('=')
      name = splitCommand[0]
      value = splitCommand[1]
      commands[name] = value

  return commands

if (__name__ == "__main__"):  
  params = getParameters(sys.argv[2])
  if not params.get('mode') or not params.get('url'):
    items = raiclicklib.listThemes()
    for item in items:
      print "raiclick: add theme %s" % (item)
      addDir(item,item,1)
  else:
    url = urllib.unquote_plus(params.get("url"))
    mode = int(params.get('mode'))
    print "raiclick: called with mode=%s and url=%s" % (mode,url)

    if mode == 1:
      items = raiclicklib.listThemeItems(url)
      for item in items:
        print "raiclick: add themeItem %s as %s" % (item[1],item[0])
        addDir(item[1],item[0],2)
        
    if mode == 2:
      items = raiclicklib.listSubItems(url)
      for item in items:
        print "raiclick: add themeSubItems %s as %s" % (item[1],item[0])
        addDir(item[1],item[0],3)      

    if mode == 3:
      items = raiclicklib.listItems(url)
      for item in items:
        print "raiclick: add videoItem %s as %s" % (item[1],item[0])
        # Per ora di date non se ne parla
        addLink(item[1],item[0],4)

    if mode == 4:
      # Playbaaaaaack
      movieUrl = raiclicklib.openMovie(raiclicklib.urlBase % url)
      print "raiclick: playback %s" % (movieUrl)
      xbmc.Player().play(movieUrl)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
sys.modules.clear()

