# This file is part of plugin.video.nederland24 ("Nederland24")

# Nederland24 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Nederland24 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Nederland24.  If not, see <http://www.gnu.org/licenses/>.


import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib
import urllib2
import re
import urlparse
import httplib

xbmc.log("plugin.video.nederland24:: Starting Addon")

###
addon = xbmcaddon.Addon()
addonId = addon.getAddonInfo('id')

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.nederland24')
xbmcplugin.setContent(pluginhandle, 'episodes')
#xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)  #enable for alphabetic listing
IMG_DIR = os.path.join(settings.getAddonInfo("path"),"resources", "media")

###
API_URL = 'http://ida.omroep.nl/aapi/?stream='
BASE_URL = 'http://livestreams.omroep.nl/live/npo/'
USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B176 Safari/7534.48.3'

CHANNELS = [
  
  ["101 TV", "101tv.png", "thematv/101tv/101tv.isml/101tv.m3u8", "Weg met suffe en saaie tv! Het is tijd voor 101 TV, het 24-uurs jongerenkanaal van BNN en de Publieke Omroep. Met rauwe en brutale programma's, van en voor jongeren. Boordevol hilarische fragmenten, spannende livegames, bizarre experimenten en nieuws over festivals en gratis concertkaartjes. Kijken dus!"],
  ["Best 24", "best24.png", "thematv/best24/best24.isml/best24.m3u8", "Best 24 brengt hoogtepunten uit zestig jaar televisiehistorie. Het is een feelgoodkanaal met 24 uur per dag de leukste, grappigste en meest spraakmakende programma's uit de Hilversumse schatkamer. Best 24: de schatkamer van de publieke omroep."],
  ["Cultura 24", "cultura24.png", "thematv/cultura24/cultura24.isml/cultura24.m3u8", "Dit is het 'cultuurkanaal van de Publieke Omroep' met de beste recente en oudere 'kunst en expressie' over verschillende onderwerpen. Klassieke muziek, dans, literatuur, theater, beeldende kunst, film 'Waar cultuur is, is Cultura 24'."],
  ["Z@ppelin/ Zapp", "familie24.png", "thematv/zappelin24/zappelin24.isml/zappelin24.m3u8", "Z@ppelin24 zendt dagelijks uit van half drie 's nachts tot half negen 's avonds. Familie24 is er op de tussenliggende tijd. Z@ppelin 24 biedt ruimte aan (oude) bekende peuterprogramma's en je kunt er kijken naar nieuwe kleuterseries. Op Familie24 zijn bekende programma's te zien en nieuwe programma's en documentaires die speciaal voor Familie24 zijn gemaakt of aangekocht."],
  ["Holland Doc 24", "hollanddoc24.png", "thematv/hollanddoc24/hollanddoc24.isml/hollanddoc24.m3u8", "Holland Doc 24 brengt op verschillende manieren en niveaus documentaires en reportages onder de aandacht. De programmering op Holland Doc 24 is gecentreerd rond wekelijkse thema's, die gerelateerd zijn aan de actualiteit, de programmering van documentairerubrieken, van culturele instellingen en festivals."],
  ["Humor TV 24", "humortv24.png", "thematv/humor24/humor24.isml/humor24.m3u8", "Humor TV 24 is een uitgesproken comedykanaal: een frisse, Nederlandse humorzender met hoogwaardige, grappige, scherpe, jonge, nieuwe, satirische, humoristische programma's."],
  ["Journaal 24", "journaal24.png", "thematv/journaal24/journaal24.isml/journaal24.m3u8", "Via het themakanaal 'Journaal 24' kunnen de live televisieuitzendingen van het NOS Journaal worden gevolgd. De laatste Journaaluitzending wordt herhaald tot de volgende uitzending van het NOS Journaal."],
  ["Politiek 24", "politiek24.png", "thematv/politiek24/politiek24.isml/politiek24.m3u8", "Politiek 24 is het digitale kanaal over de Nederlandse politiek in de breedste zin van het woord."],
  ["Nederland 1", "nederland1.png", "tvlive/ned1/ned1.isml/ned1.m3u8", "Nederland 1 Live"],
  ["Nederland 2", "nederland2.png", "tvlive/ned2/ned2.isml/ned2.m3u8", "Nederland 2 Live"],
  ["Nederland 3", "nederland3.png", "tvlive/ned3/ned3.isml/ned3.m3u8", "Nederland 3 Live"],
  ["3FM", "3fm.png", "visualradio/3fm/3fm.isml/3fm.m3u8", "3FM Live Radio"],
]

###
def index():
    for channel in CHANNELS:
        if settings.getSetting( channel[0] )=='true' and settings.getSetting( "GEOIP" )=='false':
            addLink(channel[0],channel[2], "playVideo", os.path.join(IMG_DIR, channel[1]), channel[3])
        else:
            print ""
            #xbmc.log("plugin.video.nederland24:: %s not selected" % str(channel[0]))
    if settings.getSetting( "Additional Journaal Channels" )=='true':
        additionalChannels()
    else:
        print ""
        #xbmc.log("plugin.video.nederland24:: Additional channels not selected"
    xbmcplugin.endOfDirectory(pluginhandle)

def resolve_http_redirect(url, depth=0):
    if depth > 10:
        raise Exception("Redirected "+depth+" times, giving up.")
    o = urlparse.urlparse(url,allow_fragments=True)
    conn = httplib.HTTPConnection(o.netloc)
    path = o.path
    if o.query:
        path +='?'+o.query
    conn.request("HEAD", path)
    res = conn.getresponse()
    headers = dict(res.getheaders())
    if headers.has_key('location') and headers['location'] != url:
        return resolve_http_redirect(headers['location'], depth+1)
    else:
        return url

def extract_url(chan):
    URL=API_URL+BASE_URL+(chan)
    req = urllib2.Request(URL)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    page = response.read()
    response.close()
    videopre=re.search(r'http:(.*?)url',page).group()
    prostream= (videopre.replace('\/', '/'))
    video = resolve_http_redirect(prostream, 3)
    return video

def addLink(name, url, mode, iconimage, description):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name,
    	                                  "Plot":description,
    	                                  "TVShowTitle":name
    	                                  })
    
    liz.setProperty("fanart_image", os.path.join(IMG_DIR, "fanart.png"))
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

def additionalChannels():
    link_re = re.compile(r'<a.*?</a>', re.S)
    video_re = re.compile(r'http://.*\.mp4')
    title_re = re.compile(r'<h3>(.*?)</h3>')
    meta_re = re.compile(r'<p class="video-meta">(.*?)</p>')
    img_re = re.compile(r'<img src="(.*?)"')
    
    URL='http://tv.nos.nl'
    html=urllib2.urlopen(URL).read()
    for (a, video_url) in zip(link_re.findall(html), video_re.findall(html)):
      a = a.replace('\n', '')
      title = title_re.search(a).group(1).strip()
      meta = ', '.join([meta_part.strip() for meta_part in re.sub(r'\s+', ' ', meta_re.search(a).group(1)).split('<br />')])
      #img = URL + '/browser/' + img_re.search(a).group(1).strip()
      img = os.path.join(IMG_DIR, "placeholder24.png")
      #title = title + ' - ' + meta
      addLink(title, video_url, "playVideo", img, meta)

def playVideo(url):
    media = url
    finalUrl=""
    if media and media.startswith("http://"):
        finalUrl=media
    else:
        URL=API_URL+BASE_URL+media
        req = urllib2.Request(URL)
        req.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(req)
        page = response.read()
        response.close()
        videopre=re.search(r'http:(.*?)url',page).group()
        prostream= (videopre.replace('\/', '/'))
        finalUrl = resolve_http_redirect(prostream)
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))


if mode == "playVideo":
    playVideo(url)
else:
    index()

