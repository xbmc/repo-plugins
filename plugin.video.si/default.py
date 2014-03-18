# -*- coding: utf-8 -*-
# Sports Illustrated

import sys
import httplib

import urllib, urllib2, cookielib, datetime, time, re, os
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import cgi, gzip
from StringIO import StringIO

import pyamf
from pyamf import remoting

CONST = '84c401e577ddd24ca827eab0184302b8281e8b51'

USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_2 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8H7 Safari/6533.18.5'
GENRE_SPORTS  = "Sports"
UTF8          = 'utf-8'

addon         = xbmcaddon.Addon('plugin.video.si')
__addonname__ = addon.getAddonInfo('name')
__language__  = addon.getLocalizedString

home          = addon.getAddonInfo('path').decode(UTF8)
icon          = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart        = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))


def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def _parse_argv():

        global url,name,iconimage, mode, playlist,fchan,fres,fhost,fname,fepg,fanArt

        params = {}
        try:
            params = dict( arg.split( "=" ) for arg in ((sys.argv[2][1:]).split( "&" )) )
        except:
            params = {}

        url =       demunge(params.get("url",None))
        name =      demunge(params.get("name",""))
        iconimage = demunge(params.get("iconimage",""))
        fanArt =    demunge(params.get("fanart",""))
        playlist =  demunge(params.get("playlist",""))
        fchan =     demunge(params.get("fchan",""))
        fres =      demunge(params.get("fres",""))
        fhost =     demunge(params.get("fhost",""))
        fname =     demunge(params.get("fname",""))
        fepg =      demunge(params.get("fepg",None))

        try:
            playlist=eval(playlist.replace('|',','))
        except:
            pass

        try:
            mode = int(params.get( "mode", None ))
        except:
            mode = None

def demunge(munge):
        try:
            munge = urllib.unquote_plus(munge).decode(UTF8)
        except:
            pass
        return munge


def getRequest(url):
              log("getRequest URL:"+str(url))
              headers = {'User-Agent':USER_AGENT, 'Accept':"text/html", 'Accept-Encoding':'gzip,deflate,sdch', 'Accept-Language':'en-US,en;q=0.8', 'Cookie':'hide_ce=true'} 
              req = urllib2.Request(url.encode(UTF8), None, headers)

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

              Choices = [
                         ["Most Recent","","SI"],
                         ["NFL","nfl",""],
                         ["College Football","ncaaf_video",""],
                         ["MLB","mlb",""],
                         ["NBA","nba",""],
                         ["College Basketball","ncaab_video",""],
                         ["Golf","golf",""],
                         ["NHL","nhl",""],
                         ["NASCAR","nascar",""],
                         ["Soccer","soccer",""],
                         ["MMA & Boxing","boxing",""],
                         ["Tennis","tennis",""],
                         ["More Sports","si_video",""],
                         ["Swim Daily","swimdaily",""],
                         ["Game Room","gameroom",""],
                         ["Fantasy","fantasy",""],
                         ["High School","highschool",""],
                         [" SI Now","si_now_fullshow","SI"],
                         [" Pro Football Now","profootballnow_fullshow","SI"]
                        ]

              for pname, pcode, pchoice in Choices:
                 addDir(pname,pchoice+'#'+pcode,21,icon,fanart,pname,GENRE_SPORTS,"",False)



'''
                         [" Moments of Glory","moments_of_glory","SI"],
                         [" Fresh Takes","ncaab.video_all_fresh_takes","SI"],
                         [" The Press","this_week_in_sports","SI"]]

'''

def getCategory(Category_url):

          log("main page")
          pchoice, pcode = Category_url.split('#')
          if pchoice == "SI":
              Category_url = "http://sportsillustrated.cnn.com/.element/auto/4.1/video/page/si_"+pcode+"_video_page.json?format=jsonp&callback=siVideoPage.load&_="+str(int(round(time.time() * 1000)))
              link = getRequest(Category_url)
              match = re.compile('\{.+?"brightcoveId":"(.+?)".+?"createdDate":"(.+?)".+?"slug":"(.+?)".+?"headline":"(.+?)".+?"description":"(.+?)".+?"images":\["(.+?)".+?\}').findall(link)
              for pid, pdate, pslug, pname, pdesc, pimage in match:
                 if (not ('-clip' in pslug)):
                     ts = int(pdate)
                     pdesc  = datetime.datetime.fromtimestamp(ts).strftime('%a %b %d, %Y %H:%M')+'\n'+pdesc
                     caturl = "plugin://plugin.video.si/?url=#"+str(pid)+"&mode=20"
                     try:
                        addLink(caturl.encode(UTF8),pname,pimage,fanart,pdesc,GENRE_SPORTS,"")
                     except:
                        log("Problem adding directory")
          else:
              Category_url = "http://api.brightcove.com/services/library?callback=jQuery17209430150024127215_"+str(int(round(time.time() * 1000)))+"&command=search_videos&any=primarycategory%3A"+pcode+"&page_size=100&video_fields=id%2CshortDescription%2CcreationDate%2CthumbnailURL%2Clength%2Cname&custom_fields=primarycategory%2Csubcategory&sort_by=PUBLISH_DATE%3ADESC&get_item_count=true&token=HYk6klcc_dX8GkFqbW1C2tZHLqgLDxGWBMlica9EroqvNv-skogPlw..&format=json"
              link = getRequest(Category_url)
              match = re.compile('\{"id":(.+?),"name":"(.+?)".+?"shortDescription":"(.+?)".+?"creationDate":"(.+?)".+?"thumbnailURL":"(.+?)"').findall(link)
              for pid, pname, pdesc, pdate, pimage in match:

                     ts = int(int(str(int(pdate)))/1000)
                     pdesc  = datetime.datetime.fromtimestamp(ts).strftime('%a %b %d, %Y %H:%M')+'\n'+pdesc
                     pimage = pimage.replace('\\','')
                     caturl = "plugin://plugin.video.si/?url=#"+str(pid)+"&mode=20"
                     try:
                        addLink(caturl.encode(UTF8),pname,pimage,fanart,pdesc,GENRE_SPORTS,"")
                     except:
                        log("Problem adding directory")


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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        dir_playable = False

        if mode != 12:
            u += "&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
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
            contextMenu_ = [('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=13&name=%s&playlist=%s)' %(sys.argv[0], urllib.quote_plus(playlist_name), urllib.quote_plus(str(playlist).replace(',','|'))))]
            liz.addContextMenuItems(contextMenu_)

        if autoplay == True:
            xbmc.PlayList(1).add(u, liz)
        else:    
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=dir_folder)
        return ok

def addLink(url,name,iconimage,fanart,description,genre,date,showcontext=True,playlist=None, autoplay=False):
        return addDir(name,url,12,iconimage,fanart,description,genre,date,showcontext,playlist,autoplay)

def play_video(video_url):
	video_player_key = "AQ~~,AAAB9mw57HE~,xU4DCdZtHhuasNZF5WPK5LWKKRK4p1HG"
	page_url = "http://sportsillustrated.cnn.com/video/"
	video_player_id = "2546892348001"
	publisher_id = "2157889318001"

	video_url, video_content_id = video_url.split('#')
	swf_url = get_swf_url("myExperience",video_player_id,publisher_id,str(video_content_id))
	renditions = get_episode_info(video_player_key,str(video_content_id),page_url,video_player_id)
	finalurl = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']

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

	if 'llnwd.net' not in finalurl: # using edgefcs then
		(server,ppath)= finalurl.split('/&',1)
		app = ppath.split('?',1)[1]
		finalurl = server+'?'+app+' playpath='+ppath+' swfUrl='+swf_url+' timeout=30 pageUrl='+page_url
	else:
##	finalurl = finalurl.replace('.mp4?','.mp4&') # this needs work where the app, playpath, wierdqs split doesn't work right below
		app, playpath, wierdqs = finalurl.split("&", 2)
		qs = "?videoId=%s&lineUpId=&pubId=%s&playerId=%s&affiliateId=" % (video_content_id, publisher_id, video_player_id)
		scheme,netloc = app.split("://")
		netloc, app = netloc.split("/",1)
		app = app.rstrip("/") + qs
		log("APP:%s" %(app,))
		tcurl = "%s://%s:1935/%s" % (scheme, netloc, app)
		log("TCURL:%s" % (tcurl,))
		finalurl = "%s tcUrl=%s app=%s playpath=%s%s swfUrl=%s conn=B:0 conn=S:%s&%s" % (tcurl,tcurl, app, playpath, qs, swf_url, playpath, wierdqs)
	log("final rtmp: url =%s" % (finalurl,))
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = finalurl))


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

# MAIN EVENT PROCESSING STARTS HERE

xbmcplugin.setContent(int(sys.argv[1]), 'movies')
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
except:
    pass


url=name=iconimage=mode=playlist=fchan=fres=fhost=fname=fepg=None

_parse_argv()


log("Mode: "+str(mode))
if not url is None:
    try:
      log("URL: "+str(url.encode(UTF8)))
    except:
      pass

try:
 log("Name: "+str(name))
except:
 pass

auto_play = False

if mode==None:
    log("getSources")
    getSources()

elif mode==12:
    log("setResolvedUrl")
    item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    log("play_playlist")
    play_playlist(name, playlist)

elif mode==20:
              play_video(url)

elif mode==21:
              getCategory(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

sys.modules.clear()
