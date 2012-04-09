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
# *  You should have received a copy of the GNU General Public License.
# *  If not, write to the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  2011/05/30
# *
# *  Thanks and credit to:
# *
# *  mlbviewer  http://sourceforge.net/projects/mlbviewer/  Most of the mlb.tv code was from this project.
# *
# *  Everyone from the fourm - http://fourm.xbmc.org
# *    giftie - for the colored text code :) thanks.
# *    theophile and the others from - http://forum.xbmc.org/showthread.php?t=97251


import urllib
import urllib2
import re
import os
import cookielib
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon
try:
    import json
except:
    import simplejson as json
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup


__settings__ = xbmcaddon.Addon(id='plugin.video.mlbmc')
__language__ = __settings__.getLocalizedString
addon = xbmcaddon.Addon('plugin.video.mlbmc')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )
fanart1 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart1.jpg'
fanart2 = 'http://mlbmc-xbmc.googlecode.com/svn/icons/fanart2.jpg'
debug = __settings__.getSetting('debug')
cj = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)

# reset old playback setting
if 'FLASH' in __settings__.getSetting('scenario'):
    reset = __settings__.setSetting('scenario', "2400K")

SOAPCODES = {
    "1"    : "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
    }
TeamCodes = {
    '108': ('Los Angeles Angels', 'ana'),
    '109': ('Arizona Diamondbacks', 'ari'),
    '144': ('Atlanta Braves', 'atl'),
    '110': ('Baltimore Orioles', 'bal'),
    '111': ('Boston Red Sox', 'bos'),
    '112': ('Chicago Cubs', 'chc'),
    '113': ('Cincinnati Reds', 'cin'),
    '114': ('Cleveland Indians', 'cle'),
    '115': ('Colorado Rockies', 'col'),
    '145': ('Chicago White Sox', 'cws'),
    '116': ('Detroit Tigers', 'det'),
    '146': ('Florida Marlins', 'fla'),
    '117': ('Houston Astros', 'hou'),
    '118': ('Kansas City Royals', 'kc'),
    '119': ('Los Angeles Dodgers', 'la'),
    '158': ('Milwaukee Brewers', 'mil'),
    '142': ('Minnesota Twins', 'min'),
    '121': ('New York Mets', 'nym'),
    '147': ('New York Yankees', 'nyy'),
    '133': ('Oakland Athletics', 'oak'),
    '143': ('Philadelphia Phillies', 'phi'),
    '134': ('Pittsburgh Pirates', 'pit'),
    '135': ('San Diego Padres', 'sd'),
    '136': ('Seattle Mariners', 'sea'),
    '137': ('San Francisco Giants', 'sf'),
    '138': ('St Louis Cardinals', 'stl'),
    '139': ('Tampa Bay Rays', 'tb'),
    '140': ('Texas Rangers', 'tex'),
    '141': ('Toronto Blue Jays', 'tor'),
    '120': ('Washington Nationals', 'was')
    }


def addon_log(string):
    xbmc.log( "[addon.mlbmc.1.0.6]: %s" %string )


def categories():
        thumb_path = 'http://mlbmc-xbmc.googlecode.com/svn/icons/'
        addDir(__language__(30000),'',3,thumb_path+'mlb.tv.png')
        addDir(__language__(30029),'',14,thumb_path+'condensed.png')
        addPlaylist(__language__(30001),'http://mlb.mlb.com/video/play.jsp?tcid=mm_mlb_vid',12,thumb_path+'latestvid.png')
        addDir(__language__(30002),'',4,thumb_path+'tvideo.png')
        addDir(__language__(30003),'9674738',1,thumb_path+'fc.png')
        addDir(__language__(30004),'11493214',1,thumb_path+'mc.png')
        addDir(__language__(30031),'17392054',1,thumb_path+'dailydash.png')
        addDir(__language__(30005),'8879974',1,thumb_path+'gamere.png')
        addDir(__language__(30032),'',17,thumb_path+'highlights.png')
        addDir(__language__(30006),'',18,thumb_path+'mlbnet.png')
        addDir(__language__(30007),'16820808',1,thumb_path+'pranking.png')
        addDir(__language__(30033),'4709980',1,thumb_path+'fantasy.png')
        addDir(__language__(30009),'7759164',1,thumb_path+'bball.png')
        addDir(__language__(30090),'',22,thumb_path+'podcast.png')
        addDir(__language__(30008),'http://gdx.mlb.com/components/game/mlb/'+dateStr.day[0]+'/media/highlights.xml',8,thumb_path+'realtime.png')
        addDir(__language__(30034),'',16,thumb_path+'search.png')
        addDir(__language__(30035),'',20,thumb_path+'more.png')


def mlbTV():
        if __settings__.getSetting('email') != "":
            base = 'http://mlb.mlb.com/gdcross/components/game/mlb/'
            thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/mlb.tv.png'
            addGameDir(__language__(30010),base+dateStr.day[0]+'/master_scoreboard.json',6,thumb)
            addGameDir(__language__(30011),base+dateStr.day[1]+'/master_scoreboard.json',6,thumb)
            addGameDir(__language__(30012),base+dateStr.day[3]+'/master_scoreboard.json',6,thumb)
            addGameDir(__language__(30013),base+dateStr.day[2]+'/master_scoreboard.json',6,thumb)
            addGameDir(__language__(30014),'',11,'http://mlbmc-xbmc.googlecode.com/svn/icons/mlb.tv.png')
        else:
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30016)+",30000,"+icon+")")
            __settings__.openSettings()


def condensedGames():
        base = 'http://www.mlb.com/gdcross/components/game/mlb/'
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/condensed.png'
        addGameDir(__language__(30010),base+dateStr.day[0]+'/grid.json',13,thumb)
        addGameDir(__language__(30011),base+dateStr.day[1]+'/grid.json',13,thumb)
        addGameDir(__language__(30012),base+dateStr.day[3]+'/grid.json',13,thumb)
        addGameDir(__language__(30014),'',15,'http://mlbmc-xbmc.googlecode.com/svn/icons/condensed.png')


def gameHighlights():
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/highlights.png'
        addGameDir(__language__(30036),'8879838',1,thumb)
        addGameDir(__language__(30037),'9781914',1,thumb)
        addGameDir(__language__(30038),'10025018',1,thumb)
        addGameDir(__language__(30039),'10023406',1,thumb)
        addGameDir(__language__(30040),'10025790',1,thumb)
        addGameDir(__language__(30041),'10025796',1,thumb)
        addGameDir(__language__(30042),'9782246',1,thumb)
        addGameDir(__language__(30043),'10023906',1,thumb)
        addGameDir(__language__(30044),'9780550',1,thumb)


def mlbNetwork():
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/mlbnet.png'
        addDir(__language__(30006),'7417714',1,thumb)
        addDir(__language__(30045),'8187248',1,thumb)
        addDir(__language__(30046),'12429102',1,thumb)
        addDir(__language__(30047),'9991168',1,thumb)
        addDir(__language__(30048),'20209194',1,thumb)
        addDir(__language__(30049),'4488754',1,thumb)


def mlb_podcasts():
        thumb = 'http://mlbmc-xbmc.googlecode.com/svn/icons/podcast.png'
        addDir(__language__(30091),'http://mlb.mlb.com/feed/podcast/c1261158.xml',10,thumb)
        addDir(__language__(30092),'http://mlb.mlb.com/feed/podcast/c1265860.xml',10,thumb)
        addDir(__language__(30093),'http://mlb.mlb.com/feed/podcast/c1508643.xml',10,thumb)
        addDir(__language__(30094),'http://mlb.mlb.com/feed/podcast/c1291376.xml',10,thumb)
        addDir(__language__(30095),'http://mlb.mlb.com/feed/podcast/c1266262.xml',10,thumb)
        addDir(__language__(30096),'http://mlb.mlb.com/feed/podcast/c17429946.xml',10,thumb)


def spring_training():
        addDir(__language__(30051),'26650176',1,icon)
        addDir(__language__(30052),'26655030',1,icon)

def postseason():
        addDir(__language__(30053),'25589412',1,icon)
        addDir(__language__(30054),'25502556',1,icon)
        addDir(__language__(30055),'25501166',1,icon)
        addDir(__language__(30056),'25386896',1,icon)
        addDir(__language__(30057),'7080252',1,icon)


def exploreMore():
        addDir(__language__(30080),'',21,icon)
        addDir(__language__(30050),'18847480',1,icon)
        addDir(__language__(30058),'17071012',1,icon)
        addDir(__language__(30059),'17074640',1,icon)
        addDir(__language__(30060),'17807232',1,icon)
        addDir(__language__(30061),'18985532',1,icon)
        addDir(__language__(30051),'',19,icon)
        addDir(__language__(30062),'20812682',1,icon)
        addDir(__language__(30063),'18236054',1,icon)
        addDir(__language__(30064),'18674140',1,icon)
        addDir(__language__(30065),'6003532',1,icon)
        addDir(__language__(30066),'22055984',1,icon)
        addDir(__language__(30067),'18881664',1,icon)
        addDir(__language__(30068),'4737232',1,icon)
        addDir(__language__(30069),'10122332',1,icon)
        addDir(__language__(30070),'11837016',1,icon)
        addDir(__language__(30071),'12678984',1,icon)
        addDir(__language__(30072),'5247106',1,icon)
        addDir(__language__(30073),'7271062',1,icon)
        addDir(__language__(30074),'6609548',1,icon)
        addDir(__language__(30075),'7961660',1,icon)
        addDir(__language__(30076),'9612588',1,icon)
        addDir(__language__(30077),'9583020',1,icon)


def getRequest(url, data=None, headers=None, cookies=False):
        try:
            if headers is None:
                headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                           'Referer' : 'http://mlb.mlb.com'}
            req = urllib2.Request(url,data,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            if debug == "true":
                addon_log( "getRequest : %s" %url )
                addon_log( response.info() )
                addon_log( response.geturl() )
            if cookies:
                ns_headers = response.headers.getheaders("Set-Cookie")
                return (data, ns_headers)
            else:
                return data
        except urllib2.URLError, e:
            addon_log( 'We failed to open "%s".' %url )
            if hasattr(e, 'reason'):
                addon_log( 'We failed to reach a server.' )
                addon_log( 'Reason: '+ str(e.reason) )
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30019)+str(e.reason)+",10000,"+icon+")")
                return
            elif hasattr(e, 'code'):
                addon_log( 'We failed with error code - %s.' % e.code )
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30019)+str(e.code)+",10000,"+icon+")")
                return


def get_podcasts(url):
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        items = soup('item')
        thumb = soup.find('itunes:image')['href']
        for i in items:
            title = i.title.string.replace('MLB.com','') #strange issue with the '.' in the xbmcgui.Listitem name??
            desc = i.description.string
            guid = i.guid.string
            # e_url = i.enclosure['url']  # same as guid
            pubdate = i.pubdate.string
            duration = i('itunes:duration')[0].string
            addLink(title,guid,duration,2,thumb,desc,True)


def getTeams():
        for team in TeamCodes.values():
            name = team[0]
            url = team[1]
            addPlaylist(name,url,5,'http://mlbmc-xbmc.googlecode.com/svn/icons/tvideo.png')


def getRealtimeVideo(url):
        try:
            soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
            videos = soup.findAll('media')
            for video in videos:
                name = video.headline.string
                vidId = video['id']
                url = vidId[-3]+'/'+vidId[-2]+'/'+vidId[-1]+'/'+vidId
                duration = video.duration.string
                thumb = video.thumb.string
                addLink(name,'http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml',duration,2,thumb)
        except:
            pass
        addDir(__language__(30017),'http://gdx.mlb.com/components/game/mlb/'+dateStr.day[1]+'/media/highlights.xml',8,icon)


def getTeamVideo(url):
        xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30079)+",5000,"+icon+")")
        url='http://mlb.mlb.com/gen/'+url+'/components/multimedia/topvideos.xml'
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        videos = soup('item')
        playlist = xbmc.PlayList(1)
        playlist.clear()
        for video in videos:
            name = video('title')[0].string
            thumb = video('picture', attrs={'type' : "dam-raw-thumb"})[0]('url')[0].string
            if video('url', attrs={'speed' : "1200"}):
                url = video('url', attrs={'speed' : "1200"})[0].string
            elif video('url', attrs={'speed' : "1000"}):
                url = video('url', attrs={'speed' : "1000"})[0].string
            elif video('url', attrs={'speed' : "800"}):
                url = video('url', attrs={'speed' : "800"})[0].string
            duration = video('duration')[0].string
            desc = video('big_blurb')[0].string
            info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
            playlist.add(url, info)
        play = xbmc.executebuiltin('playlist.playoffset(video,0)')


def playLatest(url):
        xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30079)+",5000,"+icon+")")
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://mlb.mlb.com/video/play.jsp?cid=mlb'}
        soup = BeautifulSoup(getRequest(url,None,headers), convertEntities=BeautifulSoup.HTML_ENTITIES)
        videos = soup.find('div', attrs={'id' : "playlistWrap"})('li')
        playlist = xbmc.PlayList(1)
        playlist.clear()
        for video in videos:
            name = video('p')[0].string
            try:
                thumb = video('img')[0]['data-src']
            except:
                thumb = video('img')[0]['src']
            content = video('a')[0]['rel']
            url = content[-3]+'/'+content[-2]+'/'+content[-1]+'/'+content
            url = getVideoURL('http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml')
            info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
            playlist.add(url, info)
        play = xbmc.executebuiltin('playlist.playoffset(video,0)')


def getVideos(url):
        url = 'http://mlb.mlb.com/gen/multimedia/topic/'+url+'.xml'
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        part = soup.search_query.string
        if part == None:
            try:
                vidList = soup.video_index['src']
                getVideoListXml(vidList)
            except:
                pass
            return
        maxitems = soup.topic['maxitems']
        if eval(maxitems) > 60:
            items = '60'
        else:
            items = maxitems
        url = 'http://mlb.mlb.com/ws/search/MediaSearchService?&'+part+'&hitsPerPage='+items+'&src=vpp'
        data = json.loads(getRequest(url))
        videos = data['mediaContent']
        for video in videos:
            name = video['blurb']
            duration = video['duration']
            url = video['url']
            try:
                thumb = video['thumbnails'][2]['src']
            except:
                thumb = video['thumbnails'][1]['src']
            addLink(name,url,duration,2,thumb)


def setVideoURL(link, podcasts=False):
        if podcasts:
            url = link
        else:
            url = getVideoURL(link)
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def getVideoURL(url):
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        if soup.find('url', attrs={'playback_scenario' : "FLASH_1200K_640X360"}):
            url = soup.find('url', attrs={'playback_scenario' : "FLASH_1200K_640X360"}).string
        elif soup.find('url', attrs={'playback_scenario' : "FLASH_1000K_640X360"}):
            url = soup.find('url', attrs={'playback_scenario' : "FLASH_1000K_640X360"}).string
        elif soup.find('url', attrs={'playback_scenario' : "FLASH_600K_400X224"}):
            url = soup.find('url', attrs={'playback_scenario' : "FLASH_600K_400X224"}).string
        elif soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_1000K_PROGDNLD"}):
            url = soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_1000K_PROGDNLD"}).string
        elif soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_800K_PROGDNLD"}):
            url = soup.find('url', attrs={'playback_scenario' : "MLB_FLASH_800K_PROGDNLD"}).string
        return url


def getCondensedGames(url):
        data = json.loads(getRequest(url))
        items = data['data']['games']['game']
        for i in items:
            try:
                if i['game_media']['newsroom']['media']['type'] == 'condensed_video':
                    content = i['game_media']['newsroom']['media']['id']
                    content_id = content[-3]+'/'+content[-2]+'/'+content[-1]+'/'+content
                    url = 'http://mlb.mlb.com/gen/multimedia/detail/'+content_id+'.xml'
                    name = TeamCodes[i['away_team_id']][0] + ' @ ' + TeamCodes[i['home_team_id']][0]
                    addLink(name, url, '', 2, 'http://mlbmc-xbmc.googlecode.com/svn/icons/condensed.png')
            except:
                continue


def getVideoListXml(url):
        url = 'http://mlb.mlb.com'+url
        soup = BeautifulStoneSoup(getRequest(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        items = soup('item')
        for item in items:
            name = item.blurb.string
            vidId = item['content_id']
            url = vidId[-3]+'/'+vidId[-2]+'/'+vidId[-1]+'/'+vidId
            try:
                thumb = item('image', attrs={'type' : "13"})[0].string
            except:
                thumb = item.image.string
            duration = item.duration.string
            addLink(name,'http://mlb.mlb.com/gen/multimedia/detail/'+url+'.xml',duration,2,thumb)


def Search(url):
        if url == '':
            searchStr = ''
            keyboard = xbmc.Keyboard(searchStr, 'MLB.com Video Search')
            keyboard.doModal()
            if (keyboard.isConfirmed() == False):
                return
            newStr = keyboard.getText()
            if len(newStr) == 0:
                return
            searchStr = newStr.replace(' ','%20')
            referStr = newStr.replace(' ','+')
            url = 'http://mlb.mlb.com/ws/search/MediaSearchService?start=0&site=mlb&hitsPerPage=12&hitsPerSite=10&'+\
            'type=json&c_id=&src=vpp&sort=desc&sort_type=custom&query='+searchStr
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://mlb.mlb.com/search/media.jsp?query='+referStr+'&c_id=mlb'}
        else:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://mlb.mlb.com/search/media.jsp?query='+url.split('=')[-1]+'&c_id=mlb'}
        data = json.loads(getRequest(url,None,headers))
        if data['total'] == 0:
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30078)+data['query']+"',5000,"+icon+")")
            return
        videos = data['mediaContent']
        for video in videos:
            name = video['blurb']
            desc = video['bigBlurb']
            link = video['url']
            duration = video['duration']
            try:
                thumb = video['thumbnails'][1]['src']
            except:
                thumb = video['thumbnails'][0]['src']
            addLink(name,link,duration,2,thumb)
        if data['total'] > data['end']:
            url = url.split('&',1)[0][:-1]+str(data['end']+1)+'&'+url.split('&',1)[1]
            addDir('Next Page',url,16,'http://mlbmc-xbmc.googlecode.com/svn/icons/next.png')


def getGames(url):
        data = json.loads(getRequest(url))
        try:
            games = data['data']['games']['game']
        except:
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30030)+",10000,"+icon+")")
            return
        for game in games:
            home_team = game['home_team_city']
            away_team = game['away_team_city']
            status = game['status']['status']
            name = away_team+' @ '+home_team+'  '

            try:
                event_id = game['game_media']['media'][0]['calendar_event_id']
            except:
                try:
                    event_id = game['game_media']['media']['calendar_event_id']
                except:
                    addon_log( name+'event_id exception' )
                    continue

            try:
                thumb = game['video_thumbnail']
            except:
                try:
                    thumb = game['game_media']['media']['thumbnail']
                except:
                    thumb = ''

            try:
                media_state = game['game_media']['media']['media_state']
            except:
                addon_log( name+'media_state exception' )
                media_state = ''

            if status == 'In Progress':
                try:
                    name += str(game['status']['inning_state'])+' '+str(game['status']['inning'])
                except:
                    name += status
            if status == 'ind' or status == 'Preview':
                try:
                    name += str(game['time']) + ' ' + str(game['time_zone'])
                except:
                    pass
            archive = False
            if status == 'Final':
                if media_state == 'media_archive':
                    try:
                        if game['game_media']['media']['has_mlbtv'] == 'true':
                            name += __language__(30081)
                            archive = True
                    except:
                        name += status

            try:
                if game['game_media']['media']['free'] == 'ALL':
                    name += __language__(30082)
            except:
                pass

            name = name.replace('.','').rstrip(' ')

            u=sys.argv[0]+"?url=&mode=7&name="+urllib.quote_plus(name)+"&event="+urllib.quote_plus(event_id)
            if media_state == 'media_on':
                liz=xbmcgui.ListItem(coloring( name,"cyan",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
            elif archive:
                liz=xbmcgui.ListItem(coloring( name,"orange",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
            else:
                liz=xbmcgui.ListItem(coloring( name,"lightgrey",name ), iconImage="DefaultVideo.png", thumbnailImage=thumb)
            liz.setInfo( type="Video", infoLabels={ "Title": name } )
            liz.setProperty( "Fanart_Image", fanart1 )
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


def mlbGame(event_id):
        # Get the cookie first
        url = 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'
        headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
        Data = getRequest(url,None,headers)
        if debug == "true":
            addon_log( 'These are the cookies we have received so far :' )
            for index, cookie in enumerate(cj):
                addon_log( str(index)+'  :  '+str(cookie) )

        # now authenticate
        url = 'https://secure.mlb.com/authenticate.do'
        headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13',
                   'Referer' : 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'}
        values = {'uri' : '/account/login_register.jsp',
                  'registrationAction' : 'identify',
                  'emailAddress' : __settings__.getSetting('email'),
                  'password' : __settings__.getSetting('password')}
        Data = getRequest(url,urllib.urlencode(values),headers,True)
        if debug == "true":
            addon_log( 'These are the cookies we have received so far :' )
            for index, cookie in enumerate(cj):
                addon_log( str(index)+'  :  '+str(cookie) )
        pattern = re.compile(r'Welcome to your personal (MLB|mlb).com account.')
        try:
            loggedin = re.search(pattern, Data[0]).groups()
            addon_log( "Logged in successfully!" )
        except:
            if debug == "true":
                addon_log( "Login Failed!" )
                addon_log( Data[0] )
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30020)+",5000,"+icon+")")
            return

        # Begin MORSEL extraction
        ns_headers = Data[1]
        attrs_set = cookielib.parse_ns_headers(ns_headers)
        cookie_tuples = cookielib.CookieJar()._normalized_cookie_tuples(attrs_set)
        if debug == "true":
            addon_log( repr(cookie_tuples) )
        cookies = {}
        for tup in cookie_tuples:
            name, value, standard, rest = tup
            cookies[name] = value
        if debug == "true":
            addon_log( repr(cookies) )

        # pick up the session key morsel
        url = 'http://mlb.mlb.com/enterworkflow.do?flowId=media.media'
        Data = getRequest(url,None,None,True)

        # Begin MORSEL extraction
        ns_headers = Data[1]
        attrs_set = cookielib.parse_ns_headers(ns_headers)
        cookie_tuples = cookielib.CookieJar()._normalized_cookie_tuples(attrs_set)
        if debug == "true":
            addon_log( repr(cookie_tuples) )
        for tup in cookie_tuples:
            name, value, standard, rest = tup
            cookies[name] = value

        try:
            if debug == "true":
                addon_log( "session-key = " + str(cookies['ftmu']) )
            session_key = urllib.unquote(cookies['ftmu'])
        except:
            session_key = None
            logout_url = 'https://secure.mlb.com/enterworkflow.do?flowId=registration.logout&c_id=mlb'
            Data = getRequest(logout_url)
            if debug == "true":
                addon_log( "No session key, so logged out." )

        try:
            values = {
                'eventId': event_id,
                'sessionKey': session_key,
                'fingerprint': urllib.unquote(cookies['fprt']),
                'identityPointId': cookies['ipid'],
                'subject':'LIVE_EVENT_COVERAGE',
                'platform':'WEB_MEDIAPLAYER'
            }
        except:
            addon_log( "Seems to ba a cookie problem" )
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30021)+",10000,"+icon+")")
            return

        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                   'Referer' : 'http://mlb.mlb.com/shared/flash/mediaplayer/v4.3/R1/MediaPlayer4.swf?v=14'}
        url = 'https://mlb-ws.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?'
        Data = getRequest(url,urllib.urlencode(values),headers)
        if debug == "true":
            addon_log( Data )
        soup = BeautifulStoneSoup(Data)
        status = soup.find('status-code').string
        if status != "1":
            error_str = SOAPCODES[status]
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30022)+error_str+",10000,"+icon+")")
            return

        items = soup.findAll('user-verified-content')
        try:
            session = soup.find('session-key').string
        except:
            session = ''
        event_id = soup.find('event-id').string
        for item in items:
            if item.state.string == 'MEDIA_ARCHIVE':
                if event_id.split('-')[2] != '2012':
                    scenario = __settings__.getSetting('archive_scenario')
                else:
                    scenario = 'FMS_CLOUD'
                live = False
            else:
                scenario = 'FMS_CLOUD'
                live = True
            content_id = item('content-id')[0].string
            blackout_status = item('blackout-status')[0]
            try:
                blackout = item('blackout')[0].string.replace('_',' ')
            except:
                blackout = __language__(30083)

            try:
                call_letters = item('domain-attribute', attrs={'name' : "call_letters"})[0].string
            except:
                call_letters = ''

            if item('domain-attribute', attrs={'name' : "home_team_id"})[0].string == item('domain-attribute', attrs={'name' : "coverage_association"})[0].string:
                coverage = TeamCodes[item('domain-attribute', attrs={'name' : "home_team_id"})[0].string][0]+' Coverage'
            elif item('domain-attribute', attrs={'name' : "away_team_id"})[0].string == item('domain-attribute', attrs={'name' : "coverage_association"})[0].string:
                coverage = TeamCodes[item('domain-attribute', attrs={'name' : "away_team_id"})[0].string][0]+' Coverage'
            else:
                coverage = ''

            if 'successstatus' in str(blackout_status):
                name = coverage+' - '+call_letters
            else:
                name = coverage+' '+call_letters+' '+blackout

            if item.type.string == 'audio':
                name += ' Gameday Audio'
                scenario = 'AUDIO_FMS_32K'

            name = name.replace('.','').rstrip(' ')

            if item.state.string == 'MEDIA_OFF':
                try:
                    preview = soup.find('preview-url').contents[0]
                    if re.search('innings-index',str(preview)):
                        if debug == "true":
                            addon_log( 'No preview' )
                        raise Exception
                    else:
                        name = __language__(30084)+name
                        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png")
                        liz.setInfo( type="Video", infoLabels={ "Title": name } )
                        liz.setProperty( "Fanart_Image", fanart1 )
                        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=preview,listitem=liz)
                except:
                    pass

            else:
                u=sys.argv[0]+"?url=&mode=9&name="+urllib.quote_plus(name)+"&event="+urllib.quote_plus(event_id)+"&content="+\
                urllib.quote_plus(content_id)+"&session="+urllib.quote_plus(session)+"&cookieIp="+urllib.quote_plus(cookies['ipid'])+\
                "&cookieFp="+urllib.quote_plus(cookies['fprt'])+"&scenario="+urllib.quote_plus(scenario)+"&live="+str(live)
                if 'successstatus' in str(blackout_status):
                    liz=xbmcgui.ListItem( coloring( name,"cyan",name ), iconImage=icon, thumbnailImage=icon)
                else:
                    liz=xbmcgui.ListItem(name, iconImage=icon)
                if item.type.string == 'audio':
                    liz.setInfo( type="Music", infoLabels={ "Title": name } )
                else:
                    liz.setInfo( type="Video", infoLabels={ "Title": name } )
                liz.setProperty( "Fanart_Image", fanart1 )
                liz.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)


def getGameURL(name,event,content,session,cookieIp,cookieFp,live):
        values = {
            'subject':'LIVE_EVENT_COVERAGE',
            'sessionKey': session,
            'identityPointId': cookieIp,
            'contentId': content,
            'playbackScenario': scenario,
            'eventId': event,
            'fingerprint': cookieFp,
            'platform':'WEB_MEDIAPLAYER'
        }
        url = 'https://secure.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1?'
        Data = getRequest(url,urllib.urlencode(values),None)
        if debug == "true":
            addon_log( Data )
        soup = BeautifulStoneSoup(Data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        status = soup.find('status-code').string
        if status != "1":
            try:
                error_str = SOAPCODES[status]
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30022)+error_str+",10000,"+icon+")")
            except:
                addon_log ( 'Unknown status-code: '+status )
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30022)+",10000,"+icon+")")
            return

        elif soup.find('state').string == 'MEDIA_OFF':
            addon_log( 'Status : Media Off' )
            try:
                preview = soup.find('preview-url').contents[0]
                if re.search('innings-index',str(preview)):
                    if debug == "true":
                        addon_log( 'No preview' )
                    raise Exception
                else:
                    xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30023)+",15000,"+icon+")")
                    item = xbmcgui.ListItem(path=preview)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            except:
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30023)+",5000,"+icon+")")
                return

        elif not 'successstatus' in str(soup.find('blackout-status')):
            addon_log( 'Status : Blackout' )
            try:
                blackout = item('blackout')[0].string.replace('_',' ')
            except:
                blackout = 'Blackout'
            try:
                preview = soup.find('preview-url').contents[0]
                if re.search('innings-index',str(preview)):
                    if debug == "true":
                        addon_log( 'No preview' )
                    raise Exception
                else:
                    xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30022)+blackout+__language__(30024)+",15000,"+icon+")")
                    item = xbmcgui.ListItem(path=preview)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            except:
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30022)+blackout+__language__(30024)+",5000,"+icon+")")
                return

        elif 'notauthorizedstatus' in str(soup.find('auth-status')):
            addon_log( 'Status : Not Authorized' )
            try:
                preview = soup.find('preview-url').contents[0]
                if re.search('innings-index',str(preview)):
                    if debug == "true":
                        addon_log( 'No preview' )
                    raise Exception
                else:
                    xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30025)+",15000,"+icon+")")
                    item = xbmcgui.ListItem(path=preview)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            except:
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30026)+",5000,"+icon+")")
                return

        else:
            try:
                game_url = soup.findAll('user-verified-content')[0]('user-verified-media-item')[0]('url')[0].string
                if debug == "true":
                    addon_log( 'game_url = '+game_url )
            except:
                addon_log( 'game_url not found' )
                xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30027)+",5000,"+icon+")")
                return

            if game_url.startswith('rtmp'):
                if re.search('ondemand', game_url):
                    rtmp = game_url.split('ondemand/')[0]+'ondemand?_fcs_vhost=cp65670.edgefcs.net&akmfv=1.6&'+game_url.split('?')[1]
                    playpath = ' Playpath='+game_url.split('ondemand/')[1]
                if re.search('live/', game_url):
                    rtmp = game_url.split('mlb_')[0]
                    playpath = ' Playpath=mlb_'+game_url.split('mlb_')[1]
            else:
                smil = get_smil(game_url.split('?')[0])
                rtmp = smil[0]
                playpath = ' Playpath='+smil[1]+'?'+game_url.split('?')[1]
            if 'mp3:' in game_url:
                pageurl = ' pageUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.3/R1/MP4.jsp?calendar_event_id='+soup.find('event-id').string+\
                '&content_id='+content+'&media_id=&view_key=&media_type=audio&source=MLB&sponsor=MLB&clickOrigin=Media+Grid&affiliateId=Media+Grid&feed_code=h&team=mlb'
            else:
                pageurl = ' pageUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.3/R1/MP4.jsp?calendar_event_id='+soup.find('event-id').string+\
                '&content_id=&media_id=&view_key=&media_type=video&source=MLB&sponsor=MLB&clickOrigin=MSB&affiliateId=MSB&team=mlb'
            swfurl = ' swfUrl=http://mlb.mlb.com/shared/flash/mediaplayer/v4.3/R1/MediaPlayer4.swf?v=14 swfVfy=1'
            if live:
                swfurl += ' live=1'
            final_url = rtmp+playpath+pageurl+swfurl
            if debug == "true":
                addon_log( 'final url: '+final_url )
            item = xbmcgui.ListItem(path=final_url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def get_smil(url):
        soup = BeautifulStoneSoup(getRequest(url))
        base = soup.meta['base']
        scenario = __settings__.getSetting('scenario')
        for i in soup('video'):
            if i['system-bitrate'] == scenario.replace('K','000'):
                path = i['src']
                return (base, path)
            else: continue


def getDate():
        date = ''
        keyboard = xbmc.Keyboard(date, 'Format: yyyy/mm/dd' )
        keyboard.doModal()
        if (keyboard.isConfirmed() == False):
            return
        date = keyboard.getText()
        if len(date) != 10:
            xbmc.executebuiltin("XBMC.Notification("+__language__(30015)+","+__language__(30028)+",5000,"+icon+")")
            return
        date = 'year_'+date.split('/')[0]+'/month_'+date.split('/')[1]+'/day_'+date.split('/')[2]
        url = 'http://mlb.mlb.com/gdcross/components/game/mlb/'+date+'/master_scoreboard.json'
        return url


class dateStr:
        today = datetime.date.today()
        ty = 'year_'+str(today).split()[0].split('-')[0]
        tm = '/month_'+str(today).split()[0].split('-')[1]
        tday = '/day_'+str(today).split()[0].split('-')[2]
        t = ty+tm+tday

        one_day = datetime.timedelta(days=1)

        yesterday = today - one_day
        yy = 'year_'+str(yesterday).split()[0].split('-')[0]
        ym = '/month_'+str(yesterday).split()[0].split('-')[1]
        yday = '/day_'+str(yesterday).split()[0].split('-')[2]
        y = yy+ym+yday

        tomorrow = today + one_day
        toy = 'year_'+str(tomorrow).split()[0].split('-')[0]
        tom = '/month_'+str(tomorrow).split()[0].split('-')[1]
        tod = '/day_'+str(tomorrow).split()[0].split('-')[2]
        to = toy+tom+tod

        byesterday = yesterday - one_day
        byy = 'year_'+str(byesterday).split()[0].split('-')[0]
        bym = '/month_'+str(byesterday).split()[0].split('-')[1]
        byday = '/day_'+str(byesterday).split()[0].split('-')[2]
        by = byy+bym+byday

        day = (t,y,to,by)


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


def coloring( text , color , colorword ):
        if color == "white":
            color="FFFFFFFF"
        if color == "blue":
            color="FF0000FF"
        if color == "cyan":
            color="FF00B7EB"
        if color == "violet":
            color="FFEE82EE"
        if color == "pink":
            color="FFFF1493"
        if color == "red":
            color="FFFF0000"
        if color == "green":
            color="FF00FF00"
        if color == "lightgrey":
            color="D3D3D3D3"
        if color == "orange":
            color="FFFF8C00"
        colored_text = text.replace( colorword , "[COLOR=%s]%s[/COLOR]" % ( color , colorword ) )
        return colored_text


def addLink(name,url,duration,mode,iconimage,plot='',podcasts=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&podcasts="+str(podcasts)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "duration": duration, "plot": plot } )
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty( "Fanart_Image", fanart2 )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addGameDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart2 )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addPlaylist(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


params=get_params()

url=None
name=None
mode=None
live=None
event=None
content=None
session=None
cookieIp=None
cookieFp=None
scenario=None
podcasts=False

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    live=eval(params["live"])
except:
    pass
try:
    podcasts=eval(params["podcasts"])
except:
    pass
try:
    event=urllib.unquote_plus(params["event"])
except:
    pass
try:
    content=urllib.unquote_plus(params["content"])
except:
    pass
try:
    session=urllib.unquote_plus(params["session"])
except:
    pass
try:
    cookieIp=urllib.unquote_plus(params["cookieIp"])
except:
    pass
try:
    cookieFp=urllib.unquote_plus(params["cookieFp"])
except:
    pass

try:
    scenario=urllib.unquote_plus(params["scenario"])
except:
    pass

addon_log( "Mode: "+str(mode) )
addon_log( "URL: "+str(url) )
addon_log( "Name: "+str(name) )

if mode==None:
    categories()

if mode==1:
    getVideos(url)

if mode==2:
    if podcasts:
        setVideoURL(url,True)
    else:
        setVideoURL(url)

if mode==3:
    mlbTV()

if mode==4:
    getTeams()

if mode==5:
    getTeamVideo(url)

if mode==6:
    getGames(url)

if mode==7:
    mlbGame(event)

if mode==8:
    getRealtimeVideo(url)

if mode==9:
    getGameURL(name,event,content,session,cookieIp,cookieFp,live)

if mode==10:
    get_podcasts(url)

if mode==11:
    url = getDate()
    getGames(url)

if mode==12:
    playLatest(url)

if mode==13:
    getCondensedGames(url)

if mode==14:
    condensedGames()

if mode==15:
    url = 'http://www.mlb.com/gdcross/components/game/mlb/'+\
    getDate().split('/',7)[7].replace('/master_scoreboard.json','/grid.json')
    getCondensedGames(url)

if mode==16:
    Search(url)

if mode==17:
    gameHighlights()

if mode==18:
    mlbNetwork()

if mode==19:
    spring_training()

if mode==20:
    exploreMore()

if mode==21:
    postseason()

if mode==22:
    mlb_podcasts()

xbmcplugin.endOfDirectory(int(sys.argv[1]))