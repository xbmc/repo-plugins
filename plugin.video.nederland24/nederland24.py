#import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib
import urllib2
import re

xbmc.log("plugin.video.nederland24:: Starting Addon")

# plugin handle

handle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.nederland24')
xbmcplugin.setContent(handle, 'episodes')
xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_EPISODE)
IMG_DIR = os.path.join(settings.getAddonInfo("path"),"resources", "media")

def addLink(name,url,iconimage,description,channelId):

    retval=True
    

#curl http://nos.nl/nieuws/live/politiek24/#tab-programma

    #if channelId!="0" and channelId!="29":
        #HTML=urllib2.urlopen("http://player.omroep.nl/?zenid=" + channelId).read()
        #xbmc.log(HTML)
        #nowTitle=((re.search(r'<span id="nowTitle">([^*]*?)</span>',HTML)).group(1)).strip()
        #nowPlot=(re.search(r'<p id="nowText">([^*]*?)</p>',HTML)).group(1).strip()
        ##nowTime=(re.search(r'<p id="nowTime">([^*]*?)</p>',HTML)).group(1).strip()
        #nextTitle=((re.search(r'<span id="nextTitle">([^*]*?)</span>',HTML)).group(1)).strip()
        #nextPlot=(re.search(r'<p id="nextText">([^*]*?)</p>',HTML)).group(1).strip()
        #nextTime=(re.search(r'<p id="nextTime">Aanvang:([^*]*?)</p>',HTML)).group(1).strip()
        ##channelEPG =  "Nu: %s\n%s\n\nStraks: %s\n%s\n%s" % (nowTitle, nowPlot, nextTime, nextTitle, nextPlot)
        #channelEPG =  "%s\n%s\n\n%s - %s\n%s" % (nowTitle, nowPlot, nextTime, nextTitle, nextPlot)

    #elif channelId!="0":
        #channelEPG = time
        #nowTitle = time
        #nowPlot = time
    #else:
        #print ""

    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setProperty("IsPlayable","true")
    liz.setInfo( type="Video", infoLabels={ "Title": name,
                                                #"Season":1,
                                                #"Episode":1,,
                                                #"premiered":channelTime,
                                                "Plot":description,
                                                "TVShowTitle":name
                                                })
    retval = xbmcplugin.addDirectoryItem(handle,url=url,listitem=liz)
    return retval
    
#Journaal Additional Channels (lifted from nos addon, with thanks)
if settings.getSetting( "Journaal Additional Channels" )=='true':
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
      addLink(title, video_url, img, meta, 116)
  


####Disabled website has changed
# ## Laatste achtuurjournaal ipad mp4, single link
# if settings.getSetting( "Laatste Achtuurjournaal" )=='true':
#     URL='http://nos.nl/'
#     page=urllib2.urlopen(URL).read()
#     time=re.findall(r'Achtuurjournaal</strong></a><span>([^*]*?)</span>',page)
#     ##URLsingle=((re.findall(r'/uitzending/[^a-z]*?-nos-journaal-2000-uur.html',page))#.group()).strip()
#     URLsingle=((re.search(r'<a href="(.+?)" title="Laatste Journaal">',page)).group()).strip()
#     #URLsingle=re.search(r'<a href="/uitzendingen/(.+?)" title="Laatste Journaal">').findall(page)
#     page=urllib2.urlopen(('http://nos.nl')+(URLsingle)).read()
#     video=re.search(r'http://content.nos.nl/content/playlist/uitzending/fragment/(.*?)mp4',page).group()
#     time=re.search(r'(NOS Journaal [^*]*?)</title>',page).group(1).strip()
#     title='Laatste Achtuurjournaal'
#     addLink(title,video,os.path.join(IMG_DIR, "laatstejournaal.png"), time, "29")
#     #<a href="/uitzendingen/[^a-z]*?" title="Laatste Achtuurjournaal">

####Disabled link no longer available
### Journaal 24 ipad mp4, stream
#if  settings.getSetting ( "Journaal 24 alternative" )=='true':
#    URL='http://player.omroep.nl/?zenid=230'
#    HTML=urllib2.urlopen(URL).read()
#    if re.match(r'<span id="nowTitle">([^*]*?)</span>',HTML):
#        nowTitle=((re.search(r'<span id="nowTitle">([^*]*?)</span>',HTML)).group(1)).strip()
#        nowPlot=(re.search(r'<p id="nowText">([^*]*?)</p>',HTML)).group(1).strip()
#        nowTime=(re.search(r'<p id="nowTime">([^*]*?)</p>',HTML)).group(1).strip()
#        nextTitle=((re.search(r'<span id="nextTitle">([^*]*?)</span>',HTML)).group(1)).strip()
#        nextPlot=(re.search(r'<p id="nextText">([^*]*?)</p>',HTML)).group(1).strip()
#        nextTime=(re.search(r'<p id="nextTime">Aanvang:([^*]*?)</p>',HTML)).group(1).strip()
#        time=  "%s\n%s\n\n%s - %s\n%s" % (nowTitle, nowPlot, nextTime, nextTitle, nextPlot)
#        video='http://download.omroep.nl/nos/iphone-live-streaming/j24/j24_ipad.m3u8'
#        title='Journaal 24 alternative'
#        addLink(title,video,os.path.join(IMG_DIR, "journaal24.png"), time, "29")

####Disabled link no longer available
## Politiek ipad mp4, stream
#if  settings.getSetting ( "Politiek 24 alternative" )=='true':
#    URL='http://nos.nl/nieuws/live/politiek24/'
#    page=urllib2.urlopen(URL).read()
#    video='http://download.omroep.nl/nos/iphone-live-streaming/p24/p24_ipad.m3u8'
#    ##check for current debate seems to work, there must be a better way to do this however.
#    tmpitem=re.search(r'(Politiek 24</a>(.+?)</li> </ul>)',page)
#    if tmpitem:
#        time=re.search(r'(Politiek 24</a>(.+?)</li> </ul>)',page).group(2).strip()
#    else:
#        time='Politiek 24 alternative'
#    title='Politiek 24 alternative'
#    addLink(title,video,os.path.join(IMG_DIR, "politiek24.png"), time, "29")
#
#else:
#    print ""


BASE_URL = 'http://livestreams.omroep.nl'

if settings.getSetting( "smallband" )=='true':
    REZ = 'sb'
else:
    REZ = 'bb'


CHANNELS = [
  ["Journaal 24", "journaal24.png", "/nos/journaal24-", "Via het themakanaal 'Journaal 24' kunnen de live televisieuitzendingen van het NOS Journaal worden gevolgd. De laatste Journaaluitzending wordt herhaald tot de volgende uitzending van het NOS Journaal.", "230"],
  ["Politiek 24", "politiek24.png", "/nos/politiek24-", "Politiek 24 is het digitale kanaal over de Nederlandse politiek in de breedste zin van het woord.", "247"],
  ["101 TV", "101tv.png", "/npo/101tv-", "Weg met suffe en saaie tv! Het is tijd voor 101 TV, het 24-uurs jongerenkanaal van BNN en de Publieke Omroep. Met rauwe en brutale programma's, van en voor jongeren. Boordevol hilarische fragmenten, spannende livegames, bizarre experimenten en nieuws over festivals en gratis concertkaartjes. Kijken dus!", "246"],
  ["Best 24", "best24.png", "/npo/best24-", "Best 24 brengt hoogtepunten uit zestig jaar televisiehistorie. Het is een feelgoodkanaal met 24 uur per dag de leukste, grappigste en meest spraakmakende programma's uit de Hilversumse schatkamer. Best 24: de schatkamer van de publieke omroep.", "252"],
  ["Cultura 24", "cultura24.png", "/npo/cultura24-", "Dit is het 'cultuurkanaal van de Publieke Omroep' met de beste recente en oudere 'kunst en expressie' over verschillende onderwerpen. Klassieke muziek, dans, literatuur, theater, beeldende kunst, film 'Waar cultuur is, is Cultura 24'.", "239"],
  ["Familie 24 / Z@ppelin", "familie24.png", "/npo/familie24-", "Z@ppelin24 zendt dagelijks uit van half drie 's nachts tot half negen 's avonds. Familie24 is er op de tussenliggende tijd. Z@ppelin 24 biedt ruimte aan (oude) bekende peuterprogramma's en je kunt er kijken naar nieuwe kleuterseries. Op Familie24 zijn bekende programma's te zien en nieuwe programma's en documentaires die speciaal voor Familie24 zijn gemaakt of aangekocht.", "261"],
  ["Holland Doc 24", "hollanddoc24.png", "/npo/hollanddoc24-", "Holland Doc 24 brengt op verschillende manieren en niveaus documentaires en reportages onder de aandacht. De programmering op Holland Doc 24 is gecentreerd rond wekelijkse thema's, die gerelateerd zijn aan de actualiteit, de programmering van documentairerubrieken, van culturele instellingen en festivals.", "227"],
  ["Humor TV 24", "humortv24.png", "/npo/humortv24-", "Humor TV 24 is een uitgesproken comedykanaal: een frisse, Nederlandse humorzender met hoogwaardige, grappige, scherpe, jonge, nieuwe, satirische, humoristische programma's.", "241"]
]

for channel in CHANNELS:
    if settings.getSetting( channel[0] )=='true' and settings.getSetting( "GEOIP" )=='false':
        addLink(channel[0],(BASE_URL+channel[2]+REZ), os.path.join(IMG_DIR, channel[1]), channel[3], channel[4])
    elif settings.getSetting( channel[0] )=='false':
        print ""
    else:
        print ""

xbmcplugin.endOfDirectory(handle)
