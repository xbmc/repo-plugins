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

import urllib2,string,xbmcgui,xbmcplugin,xbmcaddon
from xml.dom import minidom
from urllib import quote_plus
import unicodedata
import re
from datetime import date

BASE_URL = 'http://tvnz.co.nz'
MIN_BITRATE = 400000
__addon__ = xbmcaddon.Addon(id='plugin.video.tvnz.ondemand')

def INDEX():
  url = "%s/content/ps3_navigation/ps3_xml_skin.xml" % (BASE_URL,)
  req = urllib2.Request(url)
  response = urllib2.urlopen(req)
  link=response.read()
  response.close()
  for stat in minidom.parseString(link).documentElement.getElementsByTagName('MenuItem'):
    type=stat.attributes["type"].value
    if type in ('shows','alphabetical'): # TODO: distributor ,'distributor'):
      name=stat.attributes["title"].value
      m=re.search('/([0-9]+)/',stat.attributes["href"].value)
      if m:
      	id=m.group(1)
      	addDir(name,type,id)

def SHOW_LIST(id):
  url = "%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id,)
  req3 = urllib2.Request(url)
  response = urllib2.urlopen(req3)
  link = response.read()
  response.close()
  node = minidom.parseString(link).documentElement
  print node.toxml().encode('latin1')
  urls = list()
  for show in node.getElementsByTagName('Show'):
    url,liz = getShow(show)
    if not urls.count(url):
      xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=True )
      urls.append(url)

def SHOW_EPISODES(id):
  try:
    getEpisodes(id,"%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id,))
  except:
    pass
  try:
    url = "%s/content/%s_extras_group/ps3_xml_skin.xml" % (BASE_URL, id[:-15],)
    req3 = urllib2.Request(url)
    response = urllib2.urlopen(req3)
    link = response.read()
    response.close()
    node = minidom.parseString(link).documentElement
    if node:
      url = "%s?type=shows&id=%s_extras_group" % (sys.argv[0],id[:-15],)
      liz=xbmcgui.ListItem('Extras', iconImage='DefaultFolder.png', thumbnailImage='')
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)
  except:
    return

def getEpisodes(id,url):
  req3 = urllib2.Request(url)
  response = urllib2.urlopen(req3)
  link = response.read()
  response.close()
  node = minidom.parseString(link).documentElement
  for ep in node.getElementsByTagName('Episode'):
    addEpisode(ep)
  for ep in node.getElementsByTagName('Extra'):
    addEpisode(ep)

def EPISODE_LIST(id):
  getEpisodes(id, "%s/content/%s/ps3_xml_skin.xml" % (BASE_URL, id,))

def getDuration(dur):
  # Durations are formatted like 0:43:15
  minutes = 0
  parts = dur.split(":")
  if len(parts) == 3:
    minutes = int(parts[0]) * 60 + int(parts[1])
  return str(minutes)

def getDate(str):
  # Dates are formatted like 23 Jan 2010.
  # Can't use datetime.strptime as that wasn't introduced until Python 2.6
  months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  str = str.encode('ascii', 'replace') # Part of the dates include the NO BREAK character \xA0 instead of a space
  str = str.replace("?", " ")
  parts = str.split(" ")
  if len(parts) == 3:
    d = date(int(parts[2]), months.index(parts[1]) + 1, int(parts[0]))
    return d.strftime("%d.%m.%Y")
  return ""

def getShow(show):
  se = re.search('/content/(.*)_(episodes|extras)_group/ps3_xml_skin.xml', show.attributes["href"].value)
  if se:
    show_id = se.group(1)
    title = show.attributes["title"].value
    if "videos" in show.attributes.keys():
      videos = int(show.attributes["videos"].value)
    else:
      videos = 0
    #channel = show.attributes["channel"].value
    url = "%s?type=singleshow&id=%s_episodes_group" % (sys.argv[0],show_id)
    liz=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage="")
    liz.setInfo( type='Video', infoLabels={ 'episode': videos, 'tvshowtitle': title, 'title': title } )
    return(url,liz)

def getEpisode(ep):
  info = dict()
  info["tvshowtitle"] = ep.attributes["title"].value
  info["title"] = ep.attributes["sub-title"].value
  extra = string.split(ep.attributes["episode"].value,' | ')
  if len(extra) == 3:
    se = re.search('Series ([0-9]+), Episode ([0-9]+)', extra[0])
    if se:
      info["season"] = int(se.group(1))
      info["episode"] = int(se.group(2))
    else:
      info["season"] = 0
      info["episode"] = 1
    info["date"] = getDate(extra[1])
    info["aired"] = extra[1]
    info["duration"] = getDuration(extra[2])
  elif len(extra) == 2:
    info["duration"] = getDuration(extra[1])
  elif len(extra) == 1:
    info["duration"] = getDuration(extra[0])

  #channel = ep.attributes["channel"].value
  thumb = ep.attributes["src"].value
  se = re.search('/([0-9]+)/', ep.attributes["href"].value)
  if se:
    link = se.group(1)
    if len(info["title"]):
      label = "%s - \"%s\"" % (info["tvshowtitle"],info["title"],)
    else:
      label = info["tvshowtitle"]
    info["title"] = label
    if ep.firstChild:
      info["plot"]=ep.firstChild.data
    url = "%s?type=video&id=%s" % (sys.argv[0],link)
    liz = xbmcgui.ListItem(label, iconImage="DefaultVideo.png", thumbnailImage=thumb)
    liz.setInfo( type="Video", infoLabels=info )
    liz.setProperty("IsPlayable", "true")
    return(url,liz)

def addEpisode(ep):
  url,liz = getEpisode(ep)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)

def getAdvert(chapter):
  advert = chapter.getElementsByTagName('ref')
  if len(advert):
    # fetch the link - it'll return a .asf file
    req = urllib2.Request(advert[0].attributes['src'].value)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    node = minidom.parseString(link).documentElement
    # grab out the URL to the actual flash ad
    for flv in node.getElementsByTagName('FLV'):
      if flv.firstChild and len(flv.firstChild.wholeText):
        return(flv.firstChild.wholeText)

def RESOLVE(id):
  url = "%s/content/%s/ta_ent_smil_skin.smil?platform=PS3" % (BASE_URL,id,)
  req3 = urllib2.Request(url)
  response = urllib2.urlopen(req3)
  link = response.read()
  response.close()
  node = minidom.parseString(link).documentElement
  urls=list()
  for chapter in node.getElementsByTagName('seq'):
    # grab out the advert link
    if __addon__.getSetting('showads') == 'true':
      ad = getAdvert(chapter)
      if len(ad) > 0:
        urls.append(ad)
    for video in chapter.getElementsByTagName('video'):
      url = video.attributes["src"].value
      bitrate = int(video.attributes["systemBitrate"].value)
      if bitrate > MIN_BITRATE:
        if url[:7] == 'http://':
          # easy case - we have an http URL
          urls.append(url)
        elif url[:5] == 'rtmp:':
          # rtmp case
          rtmp_url = "rtmpe://fms-streaming.tvnz.co.nz/tvnz.co.nz"
          playpath = " playpath=" + url[5:]
          flashversion = " flashVer=MAC%2010,0,32,18"
          swfverify = " swfurl=http://tvnz.co.nz/stylesheets/tvnz/entertainment/flash/ondemand/player.swf swfvfy=true"
          conn = " conn=S:-720"
          urls.append(rtmp_url + playpath + flashversion + swfverify + conn)
  if len(urls) > 1:
    uri = constructStackURL(urls)
  elif len(urls) == 1:
    uri = urls[0]
  liz=xbmcgui.ListItem(path=uri)
  return(xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz))

def constructStackURL(urls):
  uri = ""
  for url in urls:
    url.replace(',',',,')
    if len(uri)>0:
      uri = uri + " , " + url
    else:
      uri = "stack://" + url
  return(uri)

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

def addDir(name,type,id):
  u = "%s?type=%s&id=%s" % (sys.argv[0],type,id,)
  liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

params=get_params()
try:
  id = params["id"]
except:
  id = "";
  pass
try:
  type = params["type"]
except:
  type = "";
  pass

if len(id) > 1:
  if type=="shows":
    EPISODE_LIST(id)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(handle=int( sys.argv[ 1 ] ), content="episodes")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  elif type=="singleshow":
    SHOW_EPISODES(id)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.setContent(handle=int( sys.argv[ 1 ] ), content="episodes")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  elif type=="alphabetical":
    SHOW_LIST(id)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(handle=int( sys.argv[ 1 ] ), content="tvshows")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  elif type=="distributor":
    # TODO: distributor
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(handle=int( sys.argv[ 1 ] ), content="tvshows")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  elif type=="video":
    RESOLVE(id)
else:  
  INDEX()
  xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


