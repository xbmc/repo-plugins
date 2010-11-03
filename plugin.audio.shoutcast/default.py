#/*
# *      Copyright (C) 2010 Team XBMC
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import urllib2,string,xbmc,xbmcgui,xbmcplugin, xbmcaddon
from xml.dom import minidom
from urllib import quote_plus
import unicodedata

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.shoutcast')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Shoutcast"
__addonid__      = "plugin.audio.shoutcast"
__author__        = "Team XBMC"

BASE_URL = 'http://yp.shoutcast.com/sbin/newxml.phtml'


def INDEX():
  req = urllib2.Request(BASE_URL)
  response = urllib2.urlopen(req)
  link=response.read()
  response.close()
  for stat in minidom.parseString(link).firstChild.getElementsByTagName('genre'):
    name = stat.attributes["name"].value
    addDir(name)

def RESOLVE(id):
  url = "%s?genre=%s" % (BASE_URL, quote_plus(id),)
  log("RESOLVE URL: %s" % url )
  req3 = urllib2.Request(url)
  response = urllib2.urlopen(req3)
  link = response.read()
  response.close()
  node = minidom.parseString(link).firstChild
  for stat in node.getElementsByTagName('station'):
    name = unicodedata.normalize('NFKD',stat.attributes["name"].value).encode('ascii','ignore')
    url = "%s?play=%s&tunein=%s" % (sys.argv[0], stat.attributes["id"].value,node.getElementsByTagName('tunein')[0].attributes["base"].value)
    addLink(name,url,stat.attributes["br"].value, stat.attributes["lc"].value)

def search():
  kb = xbmc.Keyboard("", __language__(30092), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    url = "%s?search=%s" % (BASE_URL, quote_plus(kb.getText()),)
    log("SEARCH URL: %s" % url )
    req3 = urllib2.Request(url)
    response = urllib2.urlopen(req3)
    link = response.read()
    response.close()
    node = minidom.parseString(link).firstChild
    for stat in node.getElementsByTagName('station'):
      name = unicodedata.normalize('NFKD',stat.attributes["name"].value).encode('ascii','ignore')
      url = "%s?play=%s&tunein=%s" % (sys.argv[0], stat.attributes["id"].value,node.getElementsByTagName('tunein')[0].attributes["base"].value)
      addLink(name,url,stat.attributes["br"].value, stat.attributes["lc"].value)

def PLAY(st_id, tunein):
  if __XBMC_Revision__.startswith("10.0"):
    url = "shout://yp.shoutcast.com%s?id=%s" %(tunein,st_id,)
  else:
    url = "http://yp.shoutcast.com%s?id=%s" %(tunein,st_id,)
  log("PLAY URL: %s" % url )   
  xbmc.Player().play(url)

def addLink(name,url,size,rating):
  ok=True
  liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage="")
  if __XBMC_Revision__.startswith("10.0"):
    liz.setInfo( type="Music", infoLabels={ "Title": name ,"Size": int(size)} )
  else:
    liz.setInfo( type="Music", infoLabels={ "Title": name ,"Size": int(size), "Listeners": int(rating)} )
  liz.setProperty("IsPlayable","false");
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
  return ok

def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

def addDir(name):
  u = "%s?id=%s" % (sys.argv[0], name,)
  liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

def log(msg):
  xbmc.output("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGDEBUG )
  
params=get_params()
try:
  id = params["id"]
except:
  id = "0";
try:
  initial = params["initial"]
except:
  initial = "0";
try:
  play = params["play"]
except:
  play = "0";
 

iid = len(id)
iplay = len(play)
iinitial = len(initial)

if iid > 1 :
  RESOLVE(id)
  xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X" )
  xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X" )
  try:
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LISTENERS )
  except: pass
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif iinitial > 1:
  if initial == "search":
    search()
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X" )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X" )
    try:
      xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LISTENERS )
    except: pass
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  else:
    INDEX()
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    try:
      xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LISTENERS )
    except: pass
    xbmcplugin.endOfDirectory(int(sys.argv[1]))      
elif iplay > 1:
  PLAY(play,params["tunein"] )
else:
  u = "%s?initial=search" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30091), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  u = "%s?initial=list" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30090), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
