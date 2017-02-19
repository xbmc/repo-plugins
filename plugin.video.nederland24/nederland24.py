#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from BeautifulSoup import BeautifulStoneSoup, SoupStrainer

xbmc.log("plugin.video.nederland24:: Starting Addon")

###
addon = xbmcaddon.Addon()
addonId = addon.getAddonInfo('id')

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.nederland24')
xbmcplugin.setContent(pluginhandle, 'episodes')
# xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)  #enable for alphabetic listing
IMG_DIR = os.path.join(settings.getAddonInfo("path"), "resources", "media")

###
API_URL = 'http://ida.omroep.nl/aapi/?stream='
BASE_URL = 'http://livestreams.omroep.nl/live/npo/'
#USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12'
REF_URL = 'http://www.npo.nl'
TOKEN_URL = 'http://ida.omroep.nl/npoplayer/i.js'

CHANNELS = [
  
  ["NPO 1", "npo_1.png", "tvlive/ned1/ned1.isml/ned1.m3u8", "Televisiekijken begint op NPO 1. Van nieuws en actualiteiten tot consumentenprogramma's en kwaliteitsdrama. Programma's die over jou en jouw wereld gaan. Met verhalen die je herkent over mensen die zomaar in je straat kunnen wonen. Ook als er iets belangrijks gebeurt, in Nederland of in de wereld, kijk je NPO 1."],
  ["NPO 2", "npo_2.png", "tvlive/ned2/ned2.isml/ned2.m3u8", "NPO 2 zet je aan het denken. Met programma's die verdiepen en inspireren. Als je wilt weten wat het verhaal achter de actualiteit is. Of als je het eens van een andere kant wilt bekijken. NPO 2 biedt het mooiste van Nederlandse en internationale kunst en cultuur, literatuur, documentaires, art-house films en kwaliteitsdrama."],
  ["NPO 3", "npo_3.png", "tvlive/ned3/ned3.isml/ned3.m3u8", "Op NPO 3 vind je programma's waar jong Nederland zich in herkent en die je uitdagen een eigen mening te vormen. Met veel aandacht voor nieuwe media en experimentele vernieuwing brengt NPO 3 een gevarieerd aanbod van de dagelijkse actualiteit tot muziek, reizen, human interest, talkshows en documentaires."],
  ["NPO 101", "npo_101.png", "thematv/101tv/101tv.isml/101tv.m3u8", "Weg met suffe en saaie tv! Het is tijd voor NPO 101, het 24-uurs jongerenkanaal van BNN en de Publieke Omroep. Met rauwe en brutale programma's, van en voor jongeren. Boordevol hilarische fragmenten, spannende livegames, bizarre experimenten en nieuws over festivals en gratis concertkaartjes. Kijken dus!"],
#  ["NPO Best", "npo_best.png", "thematv/best24/best24.isml/best24.m3u8", "NPO Best brengt hoogtepunten uit ruim zestig jaar Nederlandse televisiehistorie. Het is een feelgoodzender waarop u 24 uur per dag de mooiste programma's uit de schatkamer van de Publieke Omroep kunt zien."],
  ["NPO Cultura", "npo_cultura.png", "thematv/cultura24/cultura24.isml/cultura24.m3u8", "NPO Cultura is het digitale themakanaal van de Publieke Omroep voor verdieping in kunst en cultuur. 24 uur per dag programma's uit genres als klassiek, literatuur, dans, theater, pop, jazz, film, drama en beeldende kunst."],
  ["NPO Zapp Xtra", "npo_zapp.png", "thematv/zappelin24/zappelin24.isml/zappelin24.m3u8", "Zappelin Xtra en Zapp Xtra zendt dagelijks, 24 uur per dag en reclamevrij, de beste kinderprogramma's van de publieke omroep uit. Aansluitend op Nederland 3 zendt het themakanaal programma's uit van Zappelin of Zapp. Is op Nederland 3 iets voor kleuters te zien dan richt het themakanaal zich op oudere kinderen, en andersom."],
#  ["NPO Doc", "npo_doc.png", "thematv/hollanddoc24/hollanddoc24.isml/hollanddoc24.m3u8", "NPO Doc is het documentaireplatform van de NPO en verrast je continu met de beste documentaires uit binnen- en buitenland en exclusieve interviews met regisseurs en topwetenschappers."],
#  ["NPO Humor TV", "npo_humor_tv.png", "thematv/humor24/humor24.isml/humor24.m3u8", "NPO Humor TV is een uitgesproken comedykanaal: een frisse, Nederlandse humorzender met hoogwaardige, grappige, scherpe, jonge, nieuwe, satirische, humoristische programma's."],
  ["NPO Nieuws", "npo_nieuws.png", "thematv/journaal24/journaal24.isml/journaal24.m3u8", "Via het themakanaal 'NPO Nieuws' kunnen de live televisieuitzendingen van het NOS Journaal worden gevolgd. De laatste Journaaluitzending wordt herhaald tot de volgende uitzending van het NOS Journaal."],
  ["NPO Politiek", "npo_politiek.png", "thematv/politiek24/politiek24.isml/politiek24.m3u8", "NPO Politiek is het digitale kanaal over de Nederlandse politiek in de breedste zin van het woord."],
  ["NPO Radio 1", "npo_radio1.png", "visualradio/radio1/radio1.isml/radio1.m3u8", "De onafhankelijke nieuws- en sportzender. Als er iets belangrijks gebeurt, in Nederland of in de wereld, luister je NPO Radio 1. Voor de achtergronden en het nieuws van alle kanten. Ook jouw mening telt. Er is veel ruimte voor opinie en debat waar ook luisteraars steevast aan deelnemen."],
  ["NPO Radio 2", "npo_radio2.png", "visualradio/radio2/radio2.isml/radio2.m3u8", "Informatie, actualiteit en het beste uit vijftig jaar popmuziek. Een toegankelijke zender met veel aandacht voor het Nederlandse lied, kleinkunst en cabaret."],
  ["NPO 3FM", "npo_3fm.png", "visualradio/3fm/3fm.isml/3fm.m3u8", "Op NPO 3FM staat de liefde voor muziek centraal. Samen met de luisteraar vindt NPO 3FM nieuwe muziek, nieuw Nederlands poptalent en jong radiotalent. Je komt onze dj's vaak tegen op festivals en concerten."],
  ["NPO Radio 4", "npo_radio4.png", "visualradio/radio4/radio4.isml/radio4.m3u8", "De klassieke muziekzender voor zowel de ervaren als de nieuwe liefhebber. Naast de mooiste klassieke muziek, brengt NPO Radio 4 jaarlijks ongeveer twaalfhonderd concerten uit 's werelds beroemdste concertzalen. Waaronder drie eigen concertseries."],
  # ["NPO Radio 5", "npo_radio5.png", "tvlive/mcr1/mcr1.isml/mcr1.m3u8", "Overdag is NPO Radio 5 een sfeervolle zender met vooral evergreens uit de jaren ’60 en ’70. In de avond en het weekeinde brengt NPO Radio 5 beschouwende en informatieve programma’s over: godsdienst, levensbeschouwing en specifieke (sub)culturen."],
  # ["NPO Radio 6", "npo_radio6.png", "visualradio/radio6/radio6.isml/radio6.m3u8", "De Soul & Jazz zender, met muziek van Miles Davis tot Caro Emerald. Onze dj’s en muzikanten nemen je mee op een nationale en internationale ontdekkingstocht. Daarnaast doet NPO Radio 6 jaarlijks verslag van festivals als North Sea Jazz."],
  ["NPO FunX", "npo_funx.png", "visualradio/funx/funx.isml/funx.m3u8", "FunX richt zich op alle jongeren tussen 15 en 35 jaar. Muziekstijlen die op FunX te horen zijn zijn urban, latin, reggae en dancehall, oriental, Turkpop, farsipop, banghra, rai, Frans-Afrikaanse hiphop, Mandopop en andere crossoverstijlen."],
]

EVENTCHANNELS = [

  ["NPO Event 1", "npo_placeholder.png", "tvlive/mcr1/mcr1.isml/mcr1.m3u8", "NPO Evenementkanaal 1."], 
  ["NPO Event 2", "npo_placeholder.png", "tvlive/mcr2/mcr2.isml/mcr2.m3u8", "NPO Evenementkanaal 2."],
  ["NPO Event 3", "npo_placeholder.png", "tvlive/mcr3/mcr3.isml/mcr3.m3u8", "NPO Evenementkanaal 3."],
]

def index():
    for channel in CHANNELS:
        if settings.getSetting(channel[0]) == 'true':
            addLink(channel[0], channel[2], "playVideo", os.path.join(IMG_DIR, channel[1]), channel[3])
        else:
            xbmc.log("plugin.video.nederland24:: %s not set" % str(channel[0]))
    if int(settings.getSetting("Depth_Acht")) != 0:
        url = 'http://feeds.nos.nl/journaal20uur'
        depth = int(settings.getSetting("Depth_Acht"))
        additionalChannels(url, depth)
    if int(settings.getSetting("Depth_Jeugd")) != 0:
        url = 'http://feeds.nos.nl/vodcast_jeugdjournaal'
        depth = int(settings.getSetting("Depth_Jeugd"))
        additionalChannels(url, depth)
    if settings.getSetting("EVENT") == 'true':
        for channel in EVENTCHANNELS:
            # if settings.getSetting(channel[0]) == 'true':
                addLink(channel[0], channel[2], "playVideo", os.path.join(IMG_DIR, channel[1]), channel[3])
            # else:
                # xbmc.log("plugin.video.nederland24:: %s not set" % str(channel[0]))
    else:
        xbmc.log("plugin.video.nederland24:: No additional channels set")
    xbmcplugin.endOfDirectory(pluginhandle)


def prefer_clca():
    if settings.getSetting("CLCA") == 'true':
        for channel in CHANNELS:
            if channel[0] == "NPO 1":
                channel[2] = "tvlive/npo1cc/npo1cc.isml/npo1cc.m3u8"
            elif channel[0] == "NPO 2":
                channel[2] = "tvlive/npo2cc/npo2cc.isml/npo2cc.m3u8"
            elif channel[0] == "NPO 3":
                channel[2] = "tvlive/npo3cc/npo3cc.isml/npo3cc.m3u8"


def resolve_http_redirect(url, depth=0):
    if depth > 10:
        raise Exception("Redirected "+depth+" times, giving up.")
    o = urlparse.urlparse(url, allow_fragments=True)
    conn = httplib.HTTPConnection(o.netloc)
    path = o.path
    if o.query:
        path += '?'+o.query
    conn.request("HEAD", path)
    res = conn.getresponse()
    headers = dict(res.getheaders())
    if headers.has_key('location') and headers['location'] != url:
        return resolve_http_redirect(headers['location'], depth+1)
    else:
        return url


def extract_url(chan):
    URL = API_URL+BASE_URL+(chan)
    req = urllib2.Request(URL)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    page = response.read()
    response.close()
    videopre = re.search(r'http:(.*?)url', page).group()
    prostream = (videopre.replace('\/', '/'))
    video = resolve_http_redirect(prostream, 3)
    return video


def collect_token():
    req = urllib2.Request(TOKEN_URL)
    req.add_header('User-Agent', USER_AGENT)
    response = urllib2.urlopen(req)
    page = response.read()
    response.close()
    token = re.search(r'npoplayer.token = "(.*?)"', page).group(1)
    # xbmc.log("plugin.video.nederland24:: oldtoken: %s" % token)
    # site change, token invalid, needs to be reordered. Thanks to rieter for figuring this out very quickly.
    first = -1
    last = -1
    for i in range(5, len(token) - 5, 1):
        # xbmc.log("plugin.video.nederland24:: %s" % token[i])
        if token[i].isdigit():
            if first < 0:
                first = i
                # xbmc.log("plugin.video.nederland24:: %s" % token[i])
            elif last < 0:
                last = i
                # xbmc.log("plugin.video.nederland24:: %s" % token[i])
                break

    newtoken = list(token)
    if first < 0 or last < 0:
        first = 12
        last = 13
    newtoken[first] = token[last]
    newtoken[last] = token[first]
    newtoken = ''.join(newtoken)
    # xbmc.log("plugin.video.nederland24:: newtoken: %s" % newtoken)
    return newtoken


def addLink(name, url, mode, iconimage, description):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name,
    	                                  "Plot":description,
    	                                  "TVShowTitle":name,
    	                                  "Playcount": 0,
    	                                  })
    
    liz.setProperty("fanart_image", os.path.join(IMG_DIR, "fanart.png"))
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def additionalChannels(url, depth):
    i = 0
    URL = url
    # URL = 'http://feeds.nos.nl/journaal'
    items = SoupStrainer('item')
    for tag in BeautifulStoneSoup(urllib2.urlopen(URL).read(), parseOnlyThese=items):
        title = tag.title.contents[0]
        url = tag.guid.contents[0]
        img = os.path.join(IMG_DIR, "npo_placeholder.png")
        addLink(title, url, "playVideo", img, '')
        i += 1
        if i == int(depth):
            break


def playVideo(url):
    media = url
    finalUrl = ""
    if media and media.startswith("http://") or media.startswith("https://"):
        finalUrl = media
    else:
        URL = API_URL+BASE_URL+media+"&token=%s" % collect_token()
        xbmc.log("plugin.video.nederland24:: URL and token %s" % str(URL))
        req = urllib2.Request(URL)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Referer', REF_URL)
        response = urllib2.urlopen(req)
        page = response.read()
        response.close()
        videopre = re.search(r'http:(.*?)url', page).group()
        prostream = (videopre.replace('\/', '/'))
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
prefer_clca()


if mode == "playVideo":
    playVideo(url)
else:
    index()
