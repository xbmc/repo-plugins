# -*- coding: utf-8 -*-
# Mediacorp Broadcove


import urllib
import urllib2
import cookielib
import datetime
import time
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import cgi
from operator import itemgetter
import httplib, sys

import pyamf
from pyamf import remoting
CONST = '84c401e577ddd24ca827eab0184302b8281e8b51'



USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'
GENRE_TV  = "TV"
UTF8          = 'utf-8'
MAX_PER_PAGE  = 25

addon         = xbmcaddon.Addon('plugin.video.mediacorp')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode('utf-8')
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
addonfanart   = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))




def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

def cleanfilename(name):    
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in name if c in valid_chars)

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge

def getRequest(url, user_data=None, headers = {'User-Agent':USER_AGENT}):
              log("getRequest URL:"+str(url))
              req = urllib2.Request(url.encode(UTF8), user_data, headers)

              try:
                 response = urllib2.urlopen(req)
                 if response.info().getheader('Content-Encoding') == 'gzip':
                    log("Content Encoding == gzip")
                    buf = StringIO( response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    link1 = f.read()
                 else:
                    link1=response.read()
              except:
                 link1 = ""

              link1 = str(link1).replace('\n','')
              return(link1)


def getSources():

              addDir(__language__(30002),"channel5",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-5_nl.png",addonfanart,__language__(30002),"TV",False)
              addDir(__language__(30003),"channel8",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-8_nl.png",addonfanart,__language__(30003),"TV",False)
              addDir(__language__(30004),"channelu",'GC',"http://img.video.msn.com/video/i/network/ensg_channel-u_nl.png",addonfanart,__language__(30004),"TV",False)
              addDir(__language__(30007),"okto",'GC',"",addonfanart,__language__(30007),"TV",False)
              addDir(__language__(30008),"suria",'GC',"",addonfanart,__language__(30008),"TV",False)
              addDir(__language__(30009),"vasantham",'GC',"",addonfanart,__language__(30009),"TV",False)


def getChannel(url):
     html  = getRequest('http://xin.msn.com/en-sg/video/catchup/')
     blob  = re.compile('class="section tabsection horizontal".+?data-section-id="%s"(.+?)</ul>' % (url)).search(html).group(1)
     blobs = re.compile('<li tabindex="0" data-tabid="(.+?)".+?>(.+?)</li>').findall(blob)
     for caturl, cattext in blobs:
         caturl = '%s#%s' % (url, caturl)
         cattext = cattext.replace('&#39;',"'").replace('&amp;','&')
         cattext = cattext.strip()
         addDir(cattext,caturl.encode('utf-8'),'GS',icon,addonfanart,cattext,"TV","",False)


def getShows(url):
 try:
  url, caturl = url.split('#')
  html = getRequest('http://xin.msn.com/en-sg/video/catchup/')
  blob  = re.compile('class="section tabsection horizontal".+?data-section-id="%s".+?<div data-tabkey="%s"(.+?)</ul>' % (url, caturl)).search(html).group(1)
  blobs = re.compile('<li.+?href="(.+?)".+?:&quot;(.+?)&quot.+?<h4>(.+?)</h4>.+?"duration">(.+?)<.+?</li>').findall(blob)
  for caturl, caticon, cattitle, cattime in blobs:
     caturl = 'http://xin.msn.com'+caturl
     cattime = cattime.strip()
     cattitle = cattitle.replace('&#39;',"'").replace('&amp;','&')
     cattitle= cattitle.strip()
     caticon = 'http:'+caticon.replace('&amp;','&')
     caturl = "plugin://plugin.video.mediacorp/?url="+urllib.quote_plus(caturl)+"&name="+urllib.quote_plus(cattitle)+"&iconimage="+urllib.quote_plus(caticon)+"&mode=GV"
     addLink(caturl, cattitle, caticon, addonfanart, cattime+"\n"+cattitle, "TV", "")
 except:
     return



def getVideo(url):
    html = getRequest(url)  
    html=html.replace('\r','').replace("&#39;","'").replace('&quot;','"')
    try:
      if '{"formatCode":"103","url":"' in html:
            vidurl = re.compile('"formatCode":"103","url":"(.+?)"').search(html).group(1)
      elif '"formatCode":"101","url"' in html:
            vidurl = re.compile('"formatCode":"101","url":"(.+?)"').search(html).group(1)

      elif '<div class="wcvideoplayer" data-adpagegroups="' in html:
#            print "got here"
            blob = re.compile('<div class="wcvideoplayer" data-adpagegroups=(.+?)</div>').search(html).group(1)
#            print "blob="+str(blob)
            videoId = re.compile('"providerId":"(.+?)"').search(blob).group(1)
#            print "videoId = "+str(videoId)
            vidurl = getBrightCoveUrl(videoId)
#            print "vidurl = "+str(vidurl)

    except:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), '',__language__(30001))
        return

    vidurl = vidurl.encode(UTF8)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=vidurl))


def getBrightCoveUrl(video_content_id):
	video_player_key = "AQ~~%2CAAABhuSnh_E~%2CMYK8rOjehP4S5O2-9HT51QOan9pItjG3"
	page_url = "http://xin.msn.com/en-sg/video/catchup/hawaii-five-o-4-episode-6/Fvi-BBamdrC"
	video_player_id = "3605549263001"
	publisher_id = "1678873430001"

	swf_url = get_swf_url("myExperience",video_player_id,publisher_id,str(video_content_id))
#	print "swf_url = "+str(swf_url)
	renditions = get_episode_info(video_player_key,str(video_content_id),page_url,video_player_id)
#	print "renditions = "+str(renditions)
	finalurl = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
#	print "finalurl = "+str(finalurl)

# use 'IOSRenditions' in place of 'renditions' in below for .m3u8 list, note case of 'r' in renditions, using 'renditions' gives you rtmp links

	if (addon.getSetting('vid_res') == "1"):
	  stored_size=stored_height = 0
	  for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['renditions'], key = lambda item:item['frameHeight'], reverse = False):
		stream_size = item['size']
		stream_height = item['frameHeight']
		if (int(stream_size) > stored_size) and (int(item['encodingRate']) < 4000000):
			finalurl = item['defaultURL']
			stored_size = stream_size
			stored_height = stream_height

	(server,ppath)= finalurl.split('&',1)
	finalurl = "%s playpath=%s swfUrl=%s  swfvfy=1 timeout=45 pageurl=http://xin.msn.com/en-sg/video/catchup/" % (server, ppath, swf_url)
	log("final rtmp: url =%s" % (finalurl,))
	return finalurl


def get_episode_info(video_player_key, video_content_id, video_url, video_player_id):

	envelope = build_amf_request(video_player_key, video_content_id, video_url, video_player_id)
	connection_url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + video_player_key
	values = bytes(remoting.encode(envelope).read())
	header = {'Content-Type' : 'application/x-amf'}
	response = remoting.decode(getURL(connection_url, values, header, amf = True)).bodies[0][1].body
	log("Episode Info response: %s" % (response,))
	return response

def getURL(url, values = None, header = {}, amf = False, cookieinfo = False):
	try:
		if values is None:
			req = urllib2.Request(bytes(url))
		else:
			if amf == False:
				data = urllib.urlencode(values)
			elif amf == True:
				data = values
			req = urllib2.Request(bytes(url), data)
		header.update({'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0'})
		for key, value in header.iteritems():
			req.add_header(key, value)
		response = urllib2.urlopen(req)
		link = response.read()
		cookie = response.info()
		response.close()
	except urllib2.HTTPError, error:
		log("HTTP Error reason: %s" % (error,))
		return error.read()
	else:
		if cookieinfo is True:
			return link, cookie
		else:
			return link



class ViewerExperienceRequest(object):
	def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken = ''):
		self.TTLToken = TTLToken
		self.URL = URL
		self.deliveryType = float(0)
		self.contentOverrides = contentOverrides
		self.experienceId = experienceId
		self.playerKey = playerKey

class ContentOverride(object):
	def __init__(self, contentId, contentType = 0, target = 'videoPlayer'):
		self.contentType = contentType
		self.contentId = contentId
		self.target = target
		self.contentIds = None
		self.contentRefId = None
		self.contentRefIds = None
		self.contentType = 0
		self.featureId = float(0)
		self.featuredRefId = None

def build_amf_request(video_player_key, video_content_id, video_url, video_player_id):
	pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
	pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
	content_override = ContentOverride(int(video_content_id))
	viewer_exp_req = ViewerExperienceRequest(video_url, [content_override], int(video_player_id), video_player_key)
	env = remoting.Envelope(amfVersion=3)
	env.bodies.append(
	(
		"/1",
		remoting.Request(
			target = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience",
			body = [CONST, viewer_exp_req],
			envelope = env
		)
	)
	)
	return env
 
def get_swf_url(flash_experience_id, player_id, publisher_id, video_id):
        conn = httplib.HTTPConnection('c.brightcove.com')
        qsdata = dict(width=640, height=480, flashID=flash_experience_id, 
                      bgcolor="#000000", playerID=player_id, publisherID=publisher_id,
                      isSlim='true', wmode='opaque', optimizedContentLoad='true', autoStart='', debuggerID='')
        qsdata['@videoPlayer'] = video_id
        log("SWFURL: %s" % (urllib.urlencode(qsdata),))
        conn.request("GET", "/services/viewer/federated_f9?&" + urllib.urlencode(qsdata))
        resp = conn.getresponse()
        location = resp.getheader('location')
        base = location.split("?",1)[0]
        location = base.replace("BrightcoveBootloader.swf", "federatedVideo/BrightcovePlayer.swf")
        return location





def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,showcontext=True,playlist=None,autoplay=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode
        dir_playable = False
        cm = []

        if mode != 'SR':
            u += "&name="+urllib.quote_plus(name)
            if (fanart is None) or fanart == '': fanart = addonfanart
            u += "&fanart="+urllib.quote_plus(fanart)
            dir_image = "DefaultFolder.png"
            dir_folder = True
        else:
            dir_image = "DefaultVideo.png"
            dir_folder = False
            dir_playable = True

        ok=True
        liz=xbmcgui.ListItem(name, iconImage=dir_image, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Year": date } )
        liz.setProperty( "Fanart_Image", fanart )

        if dir_playable == True:
         liz.setProperty('IsPlayable', 'true')
        if not playlist is None:
            playlist_name = name.split(') ')[1]
            cm.append(('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=PP&name=%s&playlist=%s)' %(sys.argv[0], playlist_name, urllib.quote_plus(str(playlist).replace(',','|')))))
        liz.addContextMenuItems(cm)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,'SR',iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)


# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

parms = {}
try:
    parms = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
    for key in parms:
       parms[key] = demunge(parms[key])
except:
    parms = {}

p = parms.get

mode = p('mode', None)

if mode==  None:  getSources()
elif mode=='SR':  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=p('url')))
elif mode=='PP':  play_playlist(p('name'), p('playlist'))
elif mode=='GV':  getVideo(p('url'))
elif mode=='GS':  getShows(p('url'))
elif mode=='GC':  getChannel(p('url'))

xbmcplugin.endOfDirectory(int(sys.argv[1]))

