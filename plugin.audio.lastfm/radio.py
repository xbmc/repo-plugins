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
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html

# TODO  not supported in xbmc: label2 for directory items
# TODO  not supported in xbmc 12.0: SORT_METHOD_LASTPLAYED, SORT_METHOD_DATEADDED, SORT_METHOD_PLAYCOUNT. https://github.com/xbmc/xbmc/pull/2176

from utils import *
from loveban import LoveBan

SESSION = 'radio'

class Main:
    def __init__( self ):
        # check how we were started
        loveban, params = parse_argv()
        log('params: %s' % params, SESSION)
        # check if we are run as a script
        if loveban:
            if params:
                LoveBan(params)
            return
        # get addon settings
        settings     = read_settings(SESSION)
        user         = settings['user']
        self.scrob   = str(settings['radio'])
        self.sesskey = settings['sesskey']
        # initialize variables
        self._init_vars()
        # check if we have a session key
        if self.sesskey:
            url = params.get('url', user).decode("utf-8")
            mode = params.get('mode', 'root')
            sort = params.get('sort', '')
            # startup root list
            if mode == 'root':
                self._list_root(url)
            # artist list
            elif mode == 'artists':
                self._list_artists(url)
            # tag list
            elif mode == 'tags':
                self._list_tags(url)
            # custom list
            elif mode == 'custom':
                self._list_custom()
            # search
            elif mode == 'search':
                self._radio_search(url)
                return
            # search
            elif mode == 'customsearch':
                self._custom_search(url)
                return
            # create playlist
            elif mode == 'play':
                self._radio_tune(url)
                return
            # play track
            elif mode == 'playtrack':
                self._get_realurl(url)
                count = 0
                # it may take some time before the infolabels are updated after playback has started, to prevent an endless loop, bail out after 30 secs
                while (not xbmc.abortRequested) and ((not xbmc.getInfoLabel('$INFO[MusicPlayer.PlaylistLength]')) or (not xbmc.getInfoLabel('$INFO[MusicPlayer.PlaylistPosition]'))) and (count < 300):
                    count += 1
                    xbmc.sleep(100)
                # return if we couldn't get the infolabels we need
                if count >= 300:
                    return
                # fetch new tracks if we have only two items left to play
                if (int(xbmc.getInfoLabel('$INFO[MusicPlayer.PlaylistLength]')) - int(xbmc.getInfoLabel('$INFO[MusicPlayer.PlaylistPosition]'))) < 3:
                    self._get_tracks(False)
                return
            # url content list
            else:
                self._get_list(url)
            # add sort methods
            xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=1)
            if sort == 'date':
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=3 )
#            if sort == 'dateadded':
#                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=19 )
#            if sort == 'lastplayed':
#                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=34 )
            if sort == 'count':
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=20 )
            xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def _init_vars( self ):
        # init vars
        self.quit = False

    def _get_list( self, url ):
        # get a content list
        log('get list', SESSION)
        # collect post data
        data = eval(url)
        # connect to last.fm
        result = lastfm.get(data, SESSION)
        if not result:
            return
        # parse response
        if result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm list returned failed response: %s' % msg, SESSION)
            # evaluate error response
            if code == 9:
                # inavlid session key response, drop our key
                drop_sesskey()
            return 
        else:
            self._parse_list(result, data)

    def _radio_tune( self, station ):
        # tune in to a radio station
        log('tune radio', SESSION)
        # collect post data
        data = {}
        data['method'] = 'radio.tune'
        data['station'] = station
        data['sk'] = self.sesskey
        # connect to last.fm
        result = lastfm.post(data, SESSION)
        if not result:
            return
        # parse response
        if result.has_key('station'):
            station = result['station']['url']
        elif result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm radio tune returned failed response: %s' % msg, SESSION)
            # evaluate error response
            if code == 9:
                # inavlid session key response, drop our key
                drop_sesskey()
            return
        else:
            log('Last.fm radio tune returned an unknown response', SESSION)
            return
        # get tracks for this station
        self._get_tracks(True)

    def _radio_search( self, url ):
        # search a radio station
        log('search radio', SESSION)
        keyboard = xbmc.Keyboard('', LANGUAGE(32078), False)
        keyboard.doModal()
        if (keyboard.isConfirmed() and keyboard.getText() != ''):
            text = keyboard.getText()
            # collect post data
            data = eval(url)
            data[1] = text
            # connect to last.fm
            result = lastfm.get(data, SESSION)
            if not result:
                return
            # parse response
            if result.has_key('error'):
                code = result['error']
                msg = result['message'] 
                xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
                log('Last.fm list returned failed response: %s' % msg, SESSION)
                # evaluate error response
                if code == 9:
                    # inavlid session key response, drop our key
                    drop_sesskey()
                return
            elif result.has_key('stations') and result['stations'] != '\n' and result['stations'].has_key('station'):
                url = result['stations']['station']['url']
                self._radio_tune(url)
            else:
                xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32079), text, 7000))

    def _custom_search( self, url ):
        # search a radio station
        log('custom search', SESSION)
        url = eval(url)
        if url[1] == 'artist':
            header = xbmc.getLocalizedString(557)
        elif url[1] == 'tag':
            header = LANGUAGE(32088)
        else:
            header = xbmc.getLocalizedString(20142)
        # get search string
        keyboard = xbmc.Keyboard('', header, False)
        keyboard.doModal()
        if (keyboard.isConfirmed() and keyboard.getText() != ''):
            text = keyboard.getText()
            # artist or tag search
            if url[2]:
                # collect post data
                data = [url[2], text, url[1]]
                # connect to last.fm
                result = lastfm.get(data, SESSION)
                if not result:
                    return
                # parse response
                items = []
                if result.has_key('error'):
                    code = result['error']
                    msg = result['message'] 
                    xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
                    log('Last.fm list returned failed response: %s' % msg, SESSION)
                    # evaluate error response
                    if code == 9:
                        # inavlid session key response, drop our key
                        drop_sesskey()
                    return
                elif result.has_key('results') and result['results'].has_key('artistmatches') and result['results']['artistmatches'] != '\n' and result['results']['artistmatches'].has_key('artist'):
                    for item in result['results']['artistmatches']['artist']:
                        items.append(item['name'])
                elif result.has_key('results') and result['results']['tagmatches'] != '\n' and result['results']['tagmatches'].has_key('tag'):
                    for item in result['results']['tagmatches']['tag']:
                        items.append(item['name'])
                else:
                    xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32079), text, 7000))
                # select item from search results
                selected = xbmcgui.Dialog().select(url[1], items)
                if selected == -1:
                    # dialog was cancelled
                    return
                text = items[selected]
            # tune radio station
            self._radio_tune(url[0] % text)

    def _get_tracks( self, newstation ):
        # get the playlist for the tuned radio station
        log('get radio tracks', SESSION)
        # collect post data
        data = {}
        data['method'] = 'radio.getPlaylist'
        data['rtp'] = self.scrob
        data['sk'] = self.sesskey
        # connect to last.fm
        result = lastfm.post(data, SESSION)
        if not result:
            return
        # parse response
        if result.has_key('playlist'):
            tracks = result['playlist']['trackList']['track']
        elif result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm radio playlist returned failed response: %s' % msg, SESSION)
            # evaluate error response
            if code == 9:
                # inavlid session key response, drop our key
                drop_sesskey()
            return
        else:
            log('Last.fm radio playlist returned an unknown response', SESSION)
            return
        self._create_playlist(tracks, newstation )

    def _create_playlist( self, tracks, newstation ):
        # select the music playlist
        log('create playlist', SESSION)
        self.playlist  = xbmc.PlayList(0)
        # clear the playlist if we tune to a new station
        if newstation:
            self.playlist.clear()
        for item in tracks:
            artist   = item['creator']
            album    = item['album']
            song     = item['title']
            duration = int(item['duration']) / 1000
            thumb    = item['image']
            path     = item['location']
            comment  = item['extension']['streamid'] # track id needed for scrobbling
            url = sys.argv[0] + '?url=' + urllib.quote_plus(path.encode('utf-8')) + '&mode=playtrack'
            listitem = xbmcgui.ListItem(song, thumbnailImage=thumb)
            listitem.setInfo('music', {'Title': song, 'Artist': artist, 'Album': album, 'Duration': duration, 'Comment': comment})
            self.playlist.add(url=url, listitem=listitem)
        if newstation:
            log('start playback', SESSION)
            xbmc.Player().play( self.playlist )

    def _get_realurl( self, url):
        # get the redirected url for playback
        success = False
        realurl = lastfm.redirect(url)
        if realurl:
            success = True
        listitem = xbmcgui.ListItem(path=realurl)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, listitem)

    def _list_root( self, user ):
        # root listing
        self._add_listitem(LANGUAGE(32080)       , '', ' ', '', True, 'custom', 'name')
        self._add_listitem(LANGUAGE(32051) % user, '', '["user.getFriends", "%s", "user"]' % user, '', True, 'list', 'name')
        self._add_listitem(LANGUAGE(32052) % user, '', '["user.getNeighbours", "%s", "user"]' % user, '', True, 'list', 'name')
        self._add_listitem(LANGUAGE(32053) % user, '', '["user.getTopAlbums", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32054) % user, '', '["user.getTopArtists", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32055) % user, '', '["user.getTopTags", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32056) % user, '', '["user.getTopTracks", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32057) % user, '', '["user.getBannedTracks", "%s", "user"]' % user, '', True, 'list', 'date')
#        self._add_listitem(LANGUAGE(32057) % user, '', '["user.getBannedTracks", "%s", "user"]' % user, '', True, 'list', 'dateadded')
        self._add_listitem(LANGUAGE(32058) % user, '', '["user.getRecentTracks", "%s", "user"]' % user, '', True, 'list', 'date')
#        self._add_listitem(LANGUAGE(32058) % user, '', '["user.getRecentTracks", "%s", "user"]' % user, '', True, 'list', 'lastplayed')
        self._add_listitem(LANGUAGE(32059) % user, '', '["user.getLovedTracks", "%s", "user"]' % user, '', True, 'list', 'date')
#        self._add_listitem(LANGUAGE(32059) % user, '', '["user.getLovedTracks", "%s", "user"]' % user, '', True, 'list', 'dateadded')
        self._add_listitem(LANGUAGE(32060) % user, '', '["user.getWeeklyAlbumChart", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32061) % user, '', '["user.getWeeklyArtistChart", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32062) % user, '', '["user.getWeeklyTrackChart", "%s", "user"]' % user, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32095),        '', '["chart.getTopArtists", "250", "limit"]', '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32096),        '', '["chart.getTopTags", "250", "limit"]', '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32097),        '', '["chart.getTopTracks", "250", "limit"]', '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32065) % user, '', 'lastfm://user/%s/library' % user, 'DefaultPlaylist.png', False, 'play', 'none')
        self._add_listitem(LANGUAGE(32063) % user, '', 'lastfm://user/%s/mix' % user, 'DefaultPlaylist.png', False, 'play', 'none')
        self._add_listitem(LANGUAGE(32064) % user, '', 'lastfm://user/%s/neighbours' % user, 'DefaultPlaylist.png', False, 'play', 'none')
        self._add_listitem(LANGUAGE(32066) % user, '', 'lastfm://user/%s/recommended' % user, 'DefaultPlaylist.png', False, 'play', 'none')
        self._add_listitem(LANGUAGE(32078)       , '', '["radio.search", "", "name"]', 'DefaultPlaylist.png', False, 'search', 'none')

    def _list_artists( self, name ):
        # artist listing
        self._add_listitem(LANGUAGE(32067) % name, '', '["artist.getTopFans", "%s", "artist"]' % name, '', True, 'list', 'name')
        self._add_listitem(LANGUAGE(32068) % name, '', '["artist.getSimilar", "%s", "artist"]' % name, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32069) % name, '', '["artist.getTopAlbums", "%s", "artist"]' % name, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32070) % name, '', '["artist.getTopTags", "%s", "artist"]' % name, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32071) % name, '', '["artist.getTopTracks", "%s", "artist"]' % name, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32072) % name, '', 'lastfm://artist/%s/fans' % name, 'DefaultPlaylist.png', False, 'play', 'none')
        self._add_listitem(LANGUAGE(32073) % name, '', 'lastfm://artist/%s/similarartists' % name, 'DefaultPlaylist.png', False, 'play', 'none')

    def _list_tags( self, tag ):
        # tags listing
        self._add_listitem(LANGUAGE(32074) % tag,  '', '["tag.getTopAlbums", "%s", "tag"]' % tag, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32075) % tag,  '', '["tag.getTopArtists", "%s", "tag"]' % tag, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32076) % tag,  '', '["tag.getTopTracks", "%s", "tag"]' % tag, '', True, 'list', 'count')
        self._add_listitem(LANGUAGE(32077) % tag,  '', 'lastfm://globaltags/%s' % tag, 'DefaultPlaylist.png', False, 'play', 'none')

    def _list_custom( self ):
        # custom listing
        self._add_listitem(LANGUAGE(32081)       , '', '["lastfm://artist/%s/fans", "artist", "artist.search"]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32082)       , '', '["lastfm://artist/%s/similarartists", "artist", "artist.search"]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32083)       , '', '["lastfm://globaltags/%s", "tag", "tag.search"]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32091)       , '', '["lastfm://user/%s/library", "user", ""]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32092)       , '', '["lastfm://user/%s/mix", "user", ""]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32093)       , '', '["lastfm://user/%s/neighbours", "user", ""]', 'DefaultPlaylist.png', False, 'customsearch', 'none')
        self._add_listitem(LANGUAGE(32094)       , '', '["lastfm://user/%s/recommended", "user", ""]', 'DefaultPlaylist.png', False, 'customsearch', 'none')

    def _parse_list( self, data, url ):
        #parse the last.fm list
        context = ''
        tag = url[0]
        if tag == 'user.getFriends' and data.has_key('friends') and data['friends'].has_key('user'):
            items = data['friends']['user']
            getlabel = 'n'
            getlabel2 = ''
            nextmode = 'root'
        elif tag == 'user.getNeighbours' and data.has_key('neighbours') and data['neighbours'].has_key('user'):
            items = data['neighbours']['user']
            getlabel = 'n'
            getlabel2 = ''
            nextmode = 'root'
        elif tag == 'user.getTopAlbums' and data.has_key('topalbums') and data['topalbums'].has_key('album'):
            items = data['topalbums']['album']
            getlabel = 'an-n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'user.getTopArtists' and data.has_key('topartists') and data['topartists'].has_key('artist'):
            items = data['topartists']['artist']
            getlabel = 'n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'user.getTopTags' and data.has_key('toptags') and data['toptags'].has_key('tag'):
            items = data['toptags']['tag']
            getlabel = 'n'
            getlabel2 = 'c'
            nextmode = 'tags'
        elif tag == 'user.getTopTracks' and data.has_key('toptracks') and data['toptracks'].has_key('track'):
            items = data['toptracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'user.getBannedTracks' and data.has_key('bannedtracks') and data['bannedtracks'].has_key('track'):
            items = data['bannedtracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'd'
            nextmode = 'artists'
            context = 'unban'
        elif tag == 'user.getRecentTracks' and data.has_key('recenttracks') and data['recenttracks'].has_key('track'):
            items = data['recenttracks']['track']
            getlabel = 'at-n'
            getlabel2 = 'd'
            nextmode = 'artists'
        elif tag == 'user.getLovedTracks' and data.has_key('lovedtracks') and data['lovedtracks'].has_key('track'):
            items = data['lovedtracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'd'
            nextmode = 'artists'
            context = 'unlove'
        elif tag == 'user.getWeeklyAlbumChart' and data.has_key('weeklyalbumchart') and data['weeklyalbumchart'].has_key('album'):
            items = data['weeklyalbumchart']['album']
            getlabel = 'at-n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'user.getWeeklyArtistChart' and data.has_key('weeklyartistchart') and data['weeklyartistchart'].has_key('artist'):
            items = data['weeklyartistchart']['artist']
            getlabel = 'n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'user.getWeeklyTrackChart' and data.has_key('weeklytrackchart') and data['weeklytrackchart'].has_key('track'):
            items = data['weeklytrackchart']['track']
            getlabel = 'at-n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'chart.getTopArtists' and data.has_key('artists') and data['artists'].has_key('artist'):
            items = data['artists']['artist']
            getlabel = 'n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'chart.getTopTags' and data.has_key('tags') and data['tags'].has_key('tag'):
            items = data['tags']['tag']
            getlabel = 'n'
            getlabel2 = 't'
            nextmode = 'tags'
        elif tag == 'chart.getTopTracks' and data.has_key('tracks') and data['tracks'].has_key('track'):
            items = data['tracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'p'
            nextmode = 'artists'
        elif tag == 'artist.getTopFans' and data.has_key('topfans') and data['topfans'].has_key('user'):
            items = data['topfans']['user']
            getlabel = 'n'
            getlabel2 = ''
            nextmode = 'root'
        elif tag == 'artist.getSimilar' and data.has_key('similarartists') and data['similarartists'].has_key('artist'):
            items = data['similarartists']['artist']
            getlabel = 'n'
            getlabel2 = 'm'
            nextmode = 'artists'
        elif tag == 'artist.getTopAlbums' and data.has_key('topalbums') and data['topalbums'].has_key('album'):
            items = data['topalbums']['album']
            getlabel = 'an-n'
            getlabel2 = 'r'
            nextmode = 'artists'
        elif tag == 'artist.getTopTracks' and data.has_key('toptracks') and data['toptracks'].has_key('track'):
            items = data['toptracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'r'
            nextmode = 'artists'
        elif tag == 'artist.getTopTags' and data.has_key('toptags') and data['toptags'].has_key('tag'):
            items = data['toptags']['tag']
            getlabel = 'n'
            getlabel2 = 'c'
            nextmode = 'tags'
        elif tag == 'tag.getTopAlbums' and data.has_key('topalbums') and data['topalbums'].has_key('album'):
            items = data['topalbums']['album']
            getlabel = 'an-n'
            getlabel2 = 'r'
            nextmode = 'artists'
        elif tag == 'tag.getTopArtists' and data.has_key('topartists') and data['topartists'].has_key('artist'):
            items = data['topartists']['artist']
            getlabel = 'n'
            getlabel2 = 'r'
            nextmode = 'artists'
        elif tag == 'tag.getTopTracks' and data.has_key('toptracks') and data['toptracks'].has_key('track'):
            items = data['toptracks']['track']
            getlabel = 'an-n'
            getlabel2 = 'r'
            nextmode = 'artists'
        else:
            log('Last.fm returned an unknown or empty list response', SESSION)
            return
        # items can be dict or list
        items = apibug(items)
        # find items in the list
        for item in items:
            # find listitem.label and url
            label, url = self._list_getlabel(item, getlabel)
            # find listitem.label2
            label2 = self._list_getlabel2(item,getlabel2)
            # find listitem.icon
            image = self._list_getimage(item)
            # create the listitem
            self._add_listitem(label, label2, url, image, True, nextmode, 'name', context)

    def _list_getlabel( self, item, tag ):
        label = ''
        url =''
        if tag == 'n':
            url = item['name']
            label = url
        elif tag == 'an-n':
            url = item['artist']['name']
            label = url + ' - ' + item['name']
        elif tag == 'at-n':
            url = item['artist']['#text']
            label = url + ' - ' + item['name']
        return label, url

    def _list_getlabel2( self, item, tag ):
        label2 = ''
        if tag =='p':
            label2 = item['playcount']
        elif tag =='c':
            label2 = item['count']
        elif tag =='m':
            label2 = int((float(item['match'])*100)+0.5)
        elif tag =='d':
            try:
                label2 = time.strftime("%d.%m.%Y", time.localtime(float(item['date']['uts'])))
#                label2 = time.strftime("%d.%m.%Y %h:%m:%s", time.localtime(float(item['date']['uts'])))
            except:
                label2 = ''
        elif tag =='r':
            try:
                label2 = item['@attr']['rank']
            except:
                label2 = ''
        elif tag =='t':
            label2 = item['taggings']
        return label2

    def _list_getimage( self, item ):
        try:
            image = item['image'][3]['#text']
        except:
            image = ''
        return image

    def _add_listitem( self, label, label2, url, icon, dirbool, nextmode, sort, context='' ):
        # create a listitem
        item = xbmcgui.ListItem(label=label, iconImage=icon)
        # set value for label2
        if label2 and sort == 'count':
            item.setInfo('music', { 'count': int(label2) })
        elif  label2 and sort == 'date':
            item.setInfo('music', { 'date': label2 })
#        elif  label2 and sort == 'dateadded':
#            item.setInfo('music', { 'date': label2 })
#        elif  label2 and sort == 'lastplayed':
#            item.setInfo('music', { 'lastplayed': label2 })
        #add context menu items
        if context:
            # artist name
            artist = url
            # song name
            song = label.lstrip(url).lstrip(' - ')
            if context == 'unban':
                # add 'unban' to the context menu
                item.addContextMenuItems([(LANGUAGE(32025), 'XBMC.RunScript(plugin.audio.lastfm,action=LastFM.UnBan&artist=%s&song=%s)' % (artist, song),)])
            elif context == 'unlove':
                # add 'unlove' to the context menu
                item.addContextMenuItems([(LANGUAGE(32024), 'XBMC.RunScript(plugin.audio.lastfm,action=LastFM.UnLove&artist=%s&song=%s)' % (artist, song),)])
        # add listitem to the list
        directory = sys.argv[0] + '?url=' + urllib.quote_plus(url.encode('utf-8')) + '&mode=' + nextmode + '&name=' + urllib.quote_plus(label.encode('utf-8')) + '&sort=' + sort
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=directory, listitem=item, isFolder=dirbool)

if ( __name__ == "__main__" ):
    log('script version %s started' % ADDONVERSION, SESSION)
    Main()
log('script stopped', SESSION)
