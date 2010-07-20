#/*
# *      Copyright (C) 2010 Mart
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

import urllib,urllib2,re,xbmcplugin,xbmcgui,httplib

#http://3voor12.vpro.nl/feeds/luisterpaal
#http://download.omroep.nl/vpro/luisterpaal/albums/43708792/data01.swf
#http://images.vpro.nl/images/43698537+s(200)

TRACK_SEPERATOR="~"

def INDEX():
	url = 'http://3voor12.vpro.nl/feeds/luisterpaal'
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	matchAlbums=re.compile('<item>\s*?<title>(.*?)</title>\s*?<link>http://3voor12.vpro.nl/speler/luisterpaal/(\d*?)</link>\s*?<description>([\s\S]*?)</description>\s*?<enclosure length="\d*?" type="image/jpeg" url="http://images\.vpro\.nl/images/(\d*).*?"/>').findall(link)
	for title,albumId,description,coverId in matchAlbums:
		matchTracks=re.compile(r"\[(\d*)\] (.*?)&lt;br /&gt;").findall(description)
		trackList = ""
		for number,name in matchTracks:
			trackList = trackList+TRACK_SEPERATOR+name
		trackList = trackList.strip(TRACK_SEPERATOR)
		addDir(title,albumId,coverId,trackList)

def VIDEOLINKS(name,albumId,coverId,tracks):
	
	tracklist = tracks.split(TRACK_SEPERATOR)
	nr = 0
	for track in tracklist:
		nr = nr + 1
		if nr < 10:
			nrstr = "0" + str(nr)
		else:
			nrstr = str(nr)
		
		url = 'http://download.omroep.nl/vpro/luisterpaal/albums/'+albumId+'/data'+nrstr+'.swf'
		addLink(nrstr + '. ' + track,coverId,url)

def addDir(name,albumId,coverId,tracks):
		u=sys.argv[0]+"?name="+urllib.quote_plus(name)+"&albumid="+albumId+"&coverid="+coverId+"&tracks="+urllib.quote_plus(tracks)
		ok=True
		cover="http://images.vpro.nl/images/"+coverId+"+s(200).jpg"
		liz=xbmcgui.ListItem(name, iconImage=cover, thumbnailImage=cover)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		return ok

def addLink(name,coverId,url):
		ok=True
		cover="http://images.vpro.nl/images/"+coverId+"+s(200).jpg"
		liz=xbmcgui.ListItem(name, iconImage=cover, thumbnailImage=cover)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
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

params=get_params()
name=None
par=None

try:
		name=urllib.unquote_plus(params["name"])
except:
		pass
try:
		albumid=urllib.unquote_plus(params["albumid"])
except:
		pass
try:
		coverid=urllib.unquote_plus(params["coverid"])
except:
		pass

try:
		tracks=urllib.unquote_plus(params["tracks"])
except:
		pass

if name==None or len(name)<1:
		INDEX()
       
else:
		VIDEOLINKS(name,albumid,coverid,tracks)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

