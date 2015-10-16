#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/default.py
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.1.0
#       CREATED:  02.09.2015
#
###########################################################################
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
#     CHANGELOG:  (02.09.2015) TDOe - First Publishing
###########################################################################

import urllib
import urllib2
import re
import os
import xbmcgui
import xbmcaddon
import xbmcplugin

NODEBUG = True

addon               = xbmcaddon.Addon()
addonID             = addon.getAddonInfo('id')
addonFolder         = downloadScript = xbmc.translatePath('special://home/addons/'+addonID).decode('utf-8')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID).decode('utf-8')
translation = addon.getLocalizedString

addonDir   = addon.getAddonInfo("path")
XBMC_SKIN  = xbmc.getSkinDir()
icon       = os.path.join(addonFolder, "icon.png")#.encode('utf-8')
WINDOW     = xbmcgui.Window( 10000 )


SKYAvail   = False
SKYChannel = [ 'Sky Action', 'Sky Cinema', 'Sky Cinema +1', 'Sky Cinema +24', 'Sky Hits',
               'Sky Atlantic HD', 'Sky Comedy', 'Sky Nostalgie', 'Sky Emotion', 'Sky Krimi',
               'Sky 3D', 'MGM', 'Disney Cinemagic', 'Sky Bundesliga', 'Sky Sport HD 1',
               'Sky Sport HD 2', 'Sky Sport Austria', 'Sky Sport News HD', 'SPORT1+', 'Sport1 US',
               'sportdigital', 'Motorvision TV', 'Discovery Channel', 'National Geographic Channel',
               'Nat Geo Wild', 'Planet', 'History HD', 'A und E', 'Spiegel Geschichte',
               'Spiegel TV Wissen', '13TH STREET', 'Syfy', 'FOX', 'Universal Channel', 'TNT Serie',
               'TNT Film', 'Kinowelt TV', 'kabel eins classics', 'Silverline', 'AXN', 'RTL Crime',
               'Sat.1 Emotions', 'Romance TV', 'Passion', 'ProSieben Fun', 'TNT Glitz', 'RTL Living',
               'E! Entertainment', 'Heimatkanal', 'GoldStar TV', 'Beate-Uhse.TV', 'Junior',
               'Disney Junior', 'Disney XD', 'Cartoon Network', 'Boomerang', 'Animax', 'Classica',
               'MTV Live HD', 'MTV HD'
             ]

TVDigitalWatchtypes = ['spielfilm', 'sport', 'serie', 'unterhaltung', 'doku-und-info', 'kinder'] 

mastermode = addon.getSetting('mastermode')
showsky    = addon.getSetting('showsky')
mastertype = addon.getSetting('mastertype')


##########################################################################################################################
##
##########################################################################################################################
def getUnicodePage(url):
    req = urllib2.urlopen(url)
    content = ""
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
        content = unicode(req.read(), encoding)
    else:
        content = unicode(req.read(), "utf-8")
    return content


##########################################################################################################################
##
##########################################################################################################################
def debug(content):
    if (NODEBUG):
        return
    print unicode(content).encode("utf-8")


##########################################################################################################################
##
##########################################################################################################################
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


##########################################################################################################################
## clear Properties (mastermode)
##########################################################################################################################
def clear_tvdigital_mastermode_highlights():
    for i in range(1, 14, 1):
        WINDOW.clearProperty( "TVHighlightsToday.%s.Title" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Thumb" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Time" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Date" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Channel" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Icon" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Logo" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Genre" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Comment" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Year" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Duration" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Extrainfos" %(i) )


##########################################################################################################################
## retrieve tvhighlights (mastermode)
##########################################################################################################################
def get_tvdigital_mastermode_highlights(mastertype):
    url="http://www.tvdigital.de/tv-tipps/heute/"+mastertype+"/"
    content = getUnicodePage(url)
    content = content.replace("\\","")
    spl = content.split('class="highlight-container"')
    max = 10
    thumbNr = 1
    for i in range(1, len(spl), 1):
        if thumbNr > max:
            break
        entry = spl[i]
        channel = re.compile('/programm/" title="(.+?) Programm"', re.DOTALL).findall(entry)[0]
        if showsky != "true":
            debug("Sky not selected, throw away paytv channel")
            if channel in SKYChannel:
                debug("Throw away channel %s. Its PayTV" %(channel))
                continue
        else:
            debug("Sky is selected. No filtering")

        thumbs = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumbUrl=thumbs[0]
        logoUrl=thumbs[1]
        if len(re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry))>0:
            title = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)[0]
        else:
            title = re.compile('<h2 class="highlight-title">(.+?)</h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('<a class="highlight-title(.+?)<h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('href="(.+?)"', re.DOTALL).findall(detailurl)[0]
        date = re.compile('highlight-date">(.+?) | </div>', re.DOTALL).findall(entry)[0]
        time = re.compile('highlight-time">(.+?)</div>', re.DOTALL).findall(entry)[0]
        descs = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
        extrainfos = descs[0]
        if len(descs) == 2:
            comment = descs[1]
        else:
            comment = ""
        genre = re.compile('(.+?) | ', re.DOTALL).findall(extrainfos)
    
        extrainfos2 = extrainfos.split('|')
        genre = extrainfos2[0]
    
        WINDOW.setProperty( "TVHighlightsToday.%s.Title" %(thumbNr), title )
        WINDOW.setProperty( "TVHighlightsToday.%s.Thumb" %(thumbNr), thumbUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Time" %(thumbNr), time )
        WINDOW.setProperty( "TVHighlightsToday.%s.Date" %(thumbNr), date )
        WINDOW.setProperty( "TVHighlightsToday.%s.Channel" %(thumbNr), channel )
        WINDOW.setProperty( "TVHighlightsToday.%s.Icon" %(thumbNr), thumbUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Logo" %(thumbNr), logoUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Genre" %(thumbNr), genre )
        WINDOW.setProperty( "TVHighlightsToday.%s.Comment" %(thumbNr), comment )
        WINDOW.setProperty( "TVHighlightsToday.%s.Extrainfos" %(thumbNr), extrainfos )
        WINDOW.setProperty( "TVHighlightsToday.%s.Popup" %(thumbNr),detailurl)

        debug("===========TIP START=============")
        debug("Title "+title)
        debug("Thumb "+thumbUrl)
        debug("Time "+time)
        debug("Date "+date)
        debug("Channel "+channel)
        debug("Icon "+thumbUrl)
        debug("Logo "+logoUrl)
        debug("Genre "+genre)
        debug("Comment "+comment)
        debug("Extrainfos "+extrainfos)
        debug("Detailurl "+detailurl)
        debug("===========TIP END=============")
        thumbNr = thumbNr + 1
    
##########################################################################################################################
## Clear possible existing property values. watchtype is one of spielfilm,sport,serie,unterhaltung,doku-und-info,kinder    
##########################################################################################################################
def clear_tvdigital_watchtype_highlights(watchtype):
    debug("Clear Props for "+watchtype)
    for i in range(1, 14, 1):
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Year" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Duration" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,i) )



##########################################################################################################################
## Retrieve tvhighlights for a choosen watchtype. Set Home properties. 
## Possible watchtype types are spielfilm,sport,serie,unterhaltung,doku-und-info,kinder
##########################################################################################################################
def get_tvdigital_watchtype_highlights(watchtype):
    debug("Start retrive watchtype "+watchtype)
    url="http://www.tvdigital.de/tv-tipps/heute/"+watchtype+"/"
    content = getUnicodePage(url)
    content = content.replace("\\","")
    spl = content.split('class="highlight-container"')
    max = 10
    thumbNr = 1
    for i in range(1, len(spl), 1):
        if thumbNr > max:
            break
        entry = spl[i]
        channel = re.compile('/programm/" title="(.+?) Programm"', re.DOTALL).findall(entry)[0]
        if showsky != "true":
            debug("Sky not selected, throw away paytv channel")
            if channel in SKYChannel:
                debug("Throw away channel %s. Its PayTV" %(channel))
                continue
        else:
            debug("Sky is selected. No filtering")

        thumbs = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumbUrl=thumbs[0]
        logoUrl=thumbs[1]
        if len(re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry))>0:
            title = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)[0]
        else:
            title = re.compile('<h2 class="highlight-title">(.+?)</h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('<a class="highlight-title(.+?)<h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('href="(.+?)"', re.DOTALL).findall(detailurl)[0]
        #debug(detailurl)
        date = re.compile('highlight-date">(.+?) | </div>', re.DOTALL).findall(entry)[0]
        time = re.compile('highlight-time">(.+?)</div>', re.DOTALL).findall(entry)[0]
        descs = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
        extrainfos = descs[0]
        if len(descs) == 2:
            comment = descs[1]
        else:
            comment = ""
        genre = re.compile('(.+?) | ', re.DOTALL).findall(extrainfos)
    
        extrainfos2 = extrainfos.split('|')
        genre = extrainfos2[0]
   
        watchtype.translate(None, '-')
 
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,thumbNr), title )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,thumbNr), time )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,thumbNr), date )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,thumbNr), channel )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,thumbNr), logoUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,thumbNr), genre )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,thumbNr), comment )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,thumbNr), extrainfos )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Popup" %(watchtype,thumbNr),detailurl)
        debug("===========TIP "+watchtype+" START=============")
        debug("Title "+title)
        debug("Thumb "+thumbUrl)
        debug("Time "+time)
        debug("Date "+date)
        debug("Channel "+channel)
        debug("Icon "+thumbUrl)
        debug("Logo "+logoUrl)
        debug("Genre "+genre)
        debug("Comment "+comment)
        debug("Extrainfos "+extrainfos)
        debug("Detailurl "+detailurl)
        debug("===========TIP "+watchtype+" END=============")
        thumbNr = thumbNr + 1
 



##########################################################################################################################
## Get movie details
##########################################################################################################################
def get_movie_details(url):
    url.rstrip()
    debug("In Function get_movie_details with parameter: "+url)
    #### Start capture ####
    content = getUnicodePage(url)
    content = content.replace("\\","")
    spl = content.split('id="broadcast-content-box"')

    ### movie picture
    picture = re.compile('<img id="galpic" itemprop="image" src="(.+?)"', re.DOTALL).findall(content)[0]
    ### movie title
    titel = re.compile('<li id="broadcast-title" itemprop="name">(.+?)</li>', re.DOTALL).findall(content)[0]
    debug(titel)
    ### movie subtitle
    subtitel = re.compile('<li id="broadcast-subtitle"><h2>(.+?)</h2>', re.DOTALL).findall(content)
    if len(subtitel) == 0:
        subtitel = ""
    else:
        subtitel = subtitel[0]
    debug(len(subtitel))
    ### movie broadcast details
    playson = re.compile('<li id="broadcast-title" itemprop="name">(.+?)<li id="broadcast-genre', re.DOTALL).findall(content)  # class="broadcast-info-icons
    debug(playson)
    playson = re.compile('<li>(.+?)</li>', re.DOTALL).findall(playson[0])
    if len(playson) == 0:
        playson = "-"
    else:
        playson = playson[0]
        playson = re.sub('<[^<]+?>','', str(playson))

    ############# rating values start
    ratingValue = re.compile('<span itemprop="ratingValue">(.+?)</span>', re.DOTALL).findall(content)
    if len(ratingValue) == 0:
        ratingValue = "-"
    else:
        ratingValue = ratingValue[0]
    reviewCount = re.compile('<span itemprop="reviewCount">(.+?)</span>', re.DOTALL).findall(content)
    if len(reviewCount) == 0:
        reviewCount = "-"
    else:
        reviewCount = reviewCount[0]
    bestRating = re.compile('<span itemprop="bestRating">(.+?)</span>', re.DOTALL).findall(content)
    if len(bestRating) == 0:
        bestRating = "-"
    else:
        bestRating = bestRating[0]
    ############# rating values end

    ### movie description start
    description = re.compile('<span itemprop="description">(.+?)</span>', re.DOTALL).findall(content)
    if len(description) == 0:
        description = "-"
    else:
        description = description[0]
    ### movie description end


##    ### actors
    actors = re.compile('class="person-list-actor">(.+?)class="person-list-crew', re.DOTALL).findall(content)
    debug(len(actors))
    if len(actors) > 0:
        actors = actors[0].split('<tr class=')
        actors.pop(0)
        actorsdata = []
        for i in actors:
            rolle = re.compile('<td>(.+?)</td>', re.DOTALL).findall(i)[0]
            if len(rolle) > 50:
                rolle = ""
            actor = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(i)[0]
            actordict={'rolle':rolle, 'actor':actor}
            actorsdata.append(actordict)
    else:
        actorsdata = ""
##
##    ### crew
##    crew = re.compile('<div class="person-list-crew">(.+?)</table>', re.DOTALL).findall(content)
##    crew = crew[0].split('<tr class=')
##    crew.pop(0)
##    crewdata = []
##    for i in crew:
##        doing = re.compile('<td>(.+?)</td>', re.DOTALL).findall(i)[0]
##        if len(doing) > 50:
##            doing = ""
##        person = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(i)[0]
##        crewdict={'doing':doing, 'person':person}
##        crewdata.append(crewdict)
##
    crewdata = ""
##    actorsdata = ""
    
    ### genre
    genre = re.compile('<ul class="genre"(.+?)class="desc-block">', re.DOTALL).findall(content)
    if len(genre) == 0:
        genre = ['nA']
    else:
        genre2 = re.compile('<span itemprop="genre">(.+?)</span>', re.DOTALL).findall(genre[0])
        debug(genre2)
        if len(genre2) == 0:
            genre2 = re.compile('<span >(.+?)</span>', re.DOTALL).findall(genre[0])
    genre = genre2





#    genre = re.compile('<ul class="genre"(.+?)class="desc-block">', re.DOTALL).findall(content)
#    if len(genre) == 0:
#        genre = ['nA']
#    else:
#        genre = re.compile('<span itemprop="genre">(.+?)</span>', re.DOTALL).findall(genre[0])
#        if len(genre) == 0:
#            genre = re.compile('<span>(.+?)</span>', re.DOTALL).findall(genre[0])

##    ### rating details
    rating = re.compile('<ul class="rating-box"(.+?)</ul>', re.DOTALL).findall(content)
    ratingdata = []
    if len(rating) > 0:
        rating = rating[0].split('<li>')
        rating.pop(0)
        for i in rating:
           ratingtype = i.split('<span')[0]
           ratingclass = re.compile('class="rating-(.+?)">', re.DOTALL).findall(i)
           ratingdict = {'ratingtype':ratingtype, 'rating': ratingclass}
           ratingdata.append(ratingdict)
    else:
        ratingdata = [ {'ratingtype':'Spannung', 'rating':'-'}, {'ratingtype':'Action', 'rating':'-'}, {'ratingtype':'Humor', 'rating':'-'}, {'ratingtype':'Romantik', 'rating':'-'}, {'ratingtype':'Sex', 'rating':'-'} ]
##
    ### broadcastinfo
    broadcastinfo = re.compile('class="broadcast-info-icons tvd-tooltip">(.+?)</ul>', re.DOTALL).findall(content)
    if len(broadcastinfo) > 0:
        broadcastinfo = re.compile('class="(.+?)"', re.DOTALL).findall(broadcastinfo[0])
    else:
        broadcastinfo = ""

    resultdict = {'titel':titel,'subtitel':subtitel,'picture':picture,'ratingValue':ratingValue,
                  'reviewCount':reviewCount,'bestRating':bestRating,'description':description,
                  'ratingdata':ratingdata,'genre':genre,'broadcastdetails':playson,'actorsdata':actorsdata,
                  'crewdata':crewdata,'broadcastinfo':broadcastinfo}
    return resultdict



##########################################################################################################################
## Show movie details window
##########################################################################################################################
def show_detail_window(detailurl):
    debug('Open detail window')
    DETAILS = get_movie_details(detailurl)

    PopupWindow = xbmcgui.WindowDialog()

    ### Set Background Window to skin default
    BGImage = xbmc.translatePath("special://skin/backgrounds/").decode('utf-8')
    BGImage = BGImage+"SKINDEFAULT.jpg"
    BGImage = xbmcgui.ControlImage(0,0,1280,720,BGImage)
    PopupWindow.addControl(BGImage)

    ### Set Background Panel
    ContentPanelIMG = xbmc.translatePath("special://skin/").decode('utf-8')
    ContentPanelIMG = ContentPanelIMG+"media/ContentPanel.png"
    BGPanel = xbmcgui.ControlImage(240,20,800,680,ContentPanelIMG)
    PopupWindow.addControl(BGPanel)

    ### Set Title Cover Image
    TitleCover = xbmcgui.ControlImage(650,170,320,240,DETAILS['picture'].decode('utf-8'))
    PopupWindow.addControl(TitleCover)

    ### Movie Title
    TitleLabel = xbmcgui.ControlFadeLabel(300, 80, 680, 15, font='font14',textColor='FF2E9AFE',_alignment=6)
    PopupWindow.addControl(TitleLabel)
    TitleLabel.addLabel(DETAILS['titel'])

    ### Movie SubTitle
    SubTitelLabel = xbmcgui.ControlLabel(300, 115, 680, 11, DETAILS['subtitel'],font='font11',alignment=6)
    PopupWindow.addControl(SubTitelLabel)
    #SubTitelLabel.setLabel(DETAILS['titel'])
    #xbmcgui.ControlLabel(300, 140, 300, 11, DETAILS['subtitel'],font='font11',textColor='FFFF3300'))

    ### Description Text
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 440,300,10, 'Beschreibung:', font='font14',textColor='FF2E9AFE'))
    DescText = xbmcgui.ControlTextBox(300, 480, 670, 140) 
    PopupWindow.addControl(DescText)
    DescText.setText(DETAILS['description'])
    DescText.autoScroll(3000, 2500, 10000)
    ###

    ### Begin Broadcast Infos
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 160,300,10, 'Rating:', font='font14',textColor='FF2E9AFE'))
    BCastInfo = xbmcgui.ControlFadeLabel(650, 420,320,10,_alignment=6)
    PopupWindow.addControl(BCastInfo)
    BCastInfo.addLabel(DETAILS['broadcastdetails'])
    ### End Broadcast Infos

    ### Begin Genre
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 360,300,10, 'Genre:', font='font14',textColor='FF2E9AFE'))
    debug(DETAILS['genre'])
    genreSTR = ""
    for g in DETAILS['genre']:
        if len(genreSTR) > 0:
            genreSTR = genreSTR+", "+g
        else:
            genreSTR = g
    GenreLabel = xbmcgui.ControlFadeLabel(300, 400,310,10)
    PopupWindow.addControl(GenreLabel) 
    GenreLabel.addLabel(genreSTR)
    ### End Genre

    ### Begin Rating-Kategorie
    ratingy=200
    for r in DETAILS['ratingdata']:
        debug(r)
        PopupWindow.addControl(xbmcgui.ControlLabel(300, int(ratingy),300,10,r['ratingtype']))
        PopupWindow.addControl(xbmcgui.ControlLabel(500, int(ratingy),300,10,r['rating'][0]))
        ratingy = int(ratingy) + 30
    ### End Rating-Kategorie
    
    PopupWindow.doModal()




##########################################################################################################################
## Clear possible existing property values from detail info     
##########################################################################################################################
def clear_details_of_home():
    debug("Clear Details from Home")
    WINDOW.clearProperty( "TVHighlightsToday.Info.Title" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Picture" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Subtitle" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Description" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Broadcastdetails" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Genre" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.1" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.1" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.2" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.2" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.3" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.3" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.4" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.4" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.5" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.5" )





##########################################################################################################################
## Set details to Window (INFO Labels)
##########################################################################################################################
def set_details_to_window(detailurl):
    debug('Set details to info screen')
    clear_details_of_home()
    DETAILWIN = xbmcgui.WindowXMLDialog('script-TVHighlights-DialogWindow.xml', addonDir, 'Default', '720p')
    #DETAILWIN = xbmcgui.Window( 3099 )
    DETAILS   = get_movie_details(detailurl)
    debug(DETAILS)
    debug(xbmcgui.getCurrentWindowId())
    WINDOW.setProperty( "TVHighlightsToday.Info.Title", DETAILS['titel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Picture", DETAILS['picture'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Subtitle", DETAILS['subtitel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Description", DETAILS['description'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Broadcastdetails", DETAILS['broadcastdetails'] )

    ### Begin Genre
    genreSTR = ""
    for g in DETAILS['genre']:
        if len(genreSTR) > 0:
            genreSTR = genreSTR+", "+g
        else:
            genreSTR = g
    WINDOW.setProperty( "TVHighlightsToday.Info.Genre", genreSTR )
    ### End Genre

    ### Begin Rating-Kategorie
    ratingy=200
    i=1
    for r in DETAILS['ratingdata']:
        WINDOW.setProperty( "TVHighlightsToday.Info.RatingType.%s" %(i), r['ratingtype'] )
        WINDOW.setProperty( "TVHighlightsToday.Info.Rating.%s" %(i), r['rating'][0] )
        ratingy = int(ratingy) + 30
        i += 1
    ### End Rating-Kategorie
    DETAILWIN.doModal() 



##########################################################################################################################
##########################################################################################################################
##
##                                                       M  A  I  N
##
##########################################################################################################################
##########################################################################################################################




##########################################################################################################################
## Get starting methode
##########################################################################################################################
debug("TVHighlights sysargv: "+str(sys.argv))
debug("TVHighlights mastermode: "+mastermode)
if len(sys.argv)>1:
    params = parameters_string_to_dict(sys.argv[1])
    methode = urllib.unquote_plus(params.get('methode', ''))
    watchtype = urllib.unquote_plus(params.get('watchtype', ''))
    detailurl = urllib.unquote_plus(params.get('detailurl', ''))
else:
    methode = None
    watchtype = None
    detailurl= "-"

debug("Methode in Script:")
debug(methode)

if methode=='mastermode':
        debug("Methode: Mastermode Retrieve")
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights(watchtype)
 
elif methode=='getall_tvdigital':
        debug("Methode: Get All Highlights")
        for singlewatchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(singlewatchtype)
            get_tvdigital_watchtype_highlights(singlewatchtype)

elif methode=='get_single_tvdigital':
        debug("Methode: Single Methode Retrieve for "+watchtype)
        if watchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(watchtype)
            get_tvdigital_watchtype_highlights(watchtype)

elif methode=='infopopup':
        debug('Methode: set Detail INFOs to Window')
        set_details_to_window(detailurl)

elif methode=='get_tvdigital_movie_details':
        debug('Methode: should get moviedetails')
        show_detail_window(detailurl)

elif methode=='show_select_dialog':
    debug('Methode: show select dialog')
    dialog = xbmcgui.Dialog()
    ret = dialog.select(str(translation(30011)), [str(translation(30120)), str(translation(30121)), str(translation(30122)), str(translation(30123)), str(translation(30124)), str(translation(30125))])
    debug(ret)
    if ret==0:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('spielfilm')
    elif ret==1:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('sport')
    elif ret==2:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('serie')
    elif ret==3:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('unterhaltung')
    elif ret==4:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('doku-und-info')
    elif ret==5:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('kinder')
    else:
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights('spielfilm')

elif methode=='settings' or methode==None or not (watchtype in TVDigitalWatchtypes):
        debug("Settings Methode Retrieve")
        if mastermode=='true':
            clear_tvdigital_mastermode_highlights()
            get_tvdigital_mastermode_highlights(mastertype)
        else:
            setting_spielfilm     = addon.getSetting('setting_spielfilm')
            setting_sport         = addon.getSetting('setting_sport')
            setting_unterhaltung  = addon.getSetting('setting_unterhaltung')
            setting_serie         = addon.getSetting('setting_serie')
            setting_kinder        = addon.getSetting('setting_kinder')
            setting_doku          = addon.getSetting('setting_doku')

            debug("setting_spielfilm"+setting_spielfilm)
            debug("setting_sport"+setting_sport)
            debug("setting_unterhaltung"+setting_unterhaltung)
            debug("setting_serie"+setting_serie)
            debug("setting_kinder"+setting_kinder)
            debug("setting_doku"+setting_doku)

            if setting_spielfilm=='true':
                clear_tvdigital_watchtype_highlights('spielfilm')
                get_tvdigital_watchtype_highlights('spielfilm')
            if setting_serie=='true':
                clear_tvdigital_watchtype_highlights('serie')
                get_tvdigital_watchtype_highlights('serie')
            if setting_doku=='true':
                clear_tvdigital_watchtype_highlights('doku-und-info')
                get_tvdigital_watchtype_highlights('doku-und-info')
            if setting_unterhaltung=='true':
                clear_tvdigital_watchtype_highlights('unterhaltung')
                get_tvdigital_watchtype_highlights('unterhaltung')
            if setting_kinder=='true':
                clear_tvdigital_watchtype_highlights('kinder')
                get_tvdigital_watchtype_highlights('kinder')
            if setting_sport=='true':
                clear_tvdigital_watchtype_highlights('sport')
                get_tvdigital_watchtype_highlights('sport')
    
    
