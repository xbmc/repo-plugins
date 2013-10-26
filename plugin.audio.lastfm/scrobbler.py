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

from utils import *

SESSION = 'scrobbler'

class Main:
    def __init__( self ):
        # get addon settings
        self._get_settings()
        # initialize variables
        self._init_vars()
        # read scrobble cache from file
        log('read from file from disk', SESSION)
        data = read_file(self.file)
        if data:
            self.queue = data
        # start daemon
        while (not xbmc.abortRequested):
            xbmc.sleep(1000)
        # clear skin properties
        clear_prop('LastFM.CanLove')
        clear_prop('LastFM.CanBan')
        clear_prop('LastFM.RadioPlaying')

    def _get_settings( self, puser=False, ppwd=False ):
        log('get settings', SESSION)
        # if available, pass the old user and pwd to readsettings
        settings     = read_settings(SESSION, puser, ppwd)
        user         = settings['user']
        pwd          = settings['pwd']
        songs        = settings['songs']
        radio        = settings['radio']
        self.sesskey = settings['sesskey']
        # init the player class (re-init when settings have changed)
        self.player = MyPlayer(action=self._lastfm_submit, user=user, pwd=pwd, songs=songs, radio=radio, sesskey=self.sesskey)
        # init the player class (re-init when settings have changed)
        self.monitor = MyMonitor(action=self._get_settings, user=user, pwd=pwd)

    def _init_vars( self ):
        # init vars
        self.queue   = []
        self.file    = 'lastfm.xml'

    def _lastfm_submit( self, tags ):
        tstamp = int(time.time())
        # check if there's something in our queue for submission
        log('submission queue %s' % str(self.queue), SESSION)
        if self.queue:
            self._lastfm_scrobble(tstamp)
        # check if there's something to announce (playback ended/stopped will call us with None)
        if tags:
            # nowplaying announce
            self._lastfm_nowplaying(tags)
            # add track to the submission queue
            self.queue.extend([tags])
            # save queue to disk
            log('save file to disk', SESSION)
            write_file(self.file, self.queue)
        else:
            # playback stopped, clear prorties regardless of whether they've been set
            clear_prop('LastFM.CanBan')
            clear_prop('LastFM.RadioPlaying')

    def _lastfm_nowplaying( self, tags ):
        # update now playing status on last.fm
        log('nowplaying', SESSION)
        # collect post data
        data = {}
        data['method'] = 'track.updateNowPlaying'
        data['album'] = tags.get('album','')
        data['artist'] = tags.get('artist','')
        data['duration'] = tags.get('duration','')
        data['mbid'] = tags.get('mbid','')
        data['track'] = tags.get('title','')
        data['trackNumber'] = tags.get('track','')
        data['sk'] = self.sesskey
        # connect to last.fm
        result = lastfm.post(data, SESSION)
        if not result:
            return
        # parse response
        if result.has_key('nowplaying'):
            return
        elif result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm nowplaying returned failed response: %s' % msg, SESSION)
            # evaluate error response
            if code == 9:
                # inavlid session key response, drop the key
                log('drop session key')
                drop_sesskey()
            return
        else:
            log('Last.fm returned an unknown nowplaying response', SESSION)
            return

    def _lastfm_scrobble( self, tstamp ):
        # scrobble track
        log('scrobbling', SESSION)
        # check the backlog
        if len(self.queue) > 500:
            # something is wrong, reset the queue
            self.queue = []
            log('error: queue exceeded 1000 items', SESSION)
            return
        # we are allowed to submit max 50 tracks in one go
        submitlist = self.queue[:50]
        unqualified = []
        count = 0
        # collect post data
        data = {}
        for item in submitlist:
            # only submit items that are at least 30 secs long and have been played at least half or at least 4 minutes
            if (int(item.get('duration')) > 30) and ((tstamp - item.get('timestamp') > int(int(item.get('duration'))/2)) or (tstamp - int(item.get('timestamp')) > 240)):
                data['album[%d]' % count] = item.get('album','')
                data['artist[%d]' % count] = item.get('artist','')
                data['duration[%d]' % count] = item.get('duration','')
                data['mbid[%d]' % count] = item.get('mbid','')
                data['streamid[%d]' % count] = item.get('streamid','')
                data['timestamp[%d]' % count] = str(item.get('timestamp',''))
                data['track[%d]' % count] = item.get('title','')
                data['trackNumber[%d]' % count] = item.get('track','')
                data['user[%d]' % count] = item.get('user','')
            else:
                # item does not qualify for a scrobble
                unqualified.append(item)
            count += 1
        # check if we have any valid tracks to submit
        if not data:
            # remove tracks from the queue that don't qualify
            self._remove_invalid(unqualified)
            # sync queue to disk
            log('save file to disk', SESSION)
            write_file(self.file, self.queue)
            return
        data['method'] = 'track.scrobble'
        data['sk'] = self.sesskey
        # connect to last.fm
        result = lastfm.post(data, SESSION)
        if not result:
            # remove tracks from the queue that don't qualify
            self._remove_invalid(unqualified)
            # sync queue to disk
            log('save file to disk', SESSION)
            write_file(self.file, self.queue)
            return
        # parse response
        if result.has_key('scrobbles'):
            # remove submitted items from the list
            self.queue = self.queue[50:]
        elif result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm scrobble returned failed response: %s' % msg, SESSION)
            # evaluate error response
            if code == 9:
                # inavlid session key response, drop the new key
                log('drop session key', SESSION)               
                drop_sesskey()
                # remove tracks from the queue that don't qualify
                self._remove_invalid(unqualified)
            # flush the queue unless it's a temp error on last.fm side
            elif not (code == 11 or code == 16):
                self.queue = []
            else:
                # remove tracks from the queue that don't qualify
                self._remove_invalid(unqualified)
        else:
            log('Last.fm returned an unknown scrobble response', SESSION)
            # unknown error. flush the queue
            self.queue = []
        # check if there's anything left in the queue to scrobble (if we started with more than 50 tracks)
        if self.queue:
            log('tracks left to scrobble', SESSION)
            self_lastfm_scrobble( self, tstamp )
        # sync queue to disk
        log('save file to disk', SESSION)
        write_file(self.file, self.queue)

    def _remove_invalid( self, unqualified ):
        log('removing unqualified items from the list', SESSION)
        # iterate over the invalid items and remove them from the queue
        for item in unqualified:
            self.queue.remove(item)

class MyPlayer(xbmc.Player):
    def __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self )
        log('init player class', SESSION)
        self.action  = kwargs['action']
        self.user    = kwargs['user']
        self.pwd     = kwargs['pwd']
        self.sesskey = kwargs['sesskey']
        self.songs   = kwargs['songs']
        self.radio   = kwargs['radio']
        self.Audio   = False
        self.Count   = 0

    def onPlayBackStarted( self ):
        # only do something if we're playing audio and user has enabled it in settings
        if self.isPlayingAudio() and self.sesskey and self.user and self.pwd and (self.radio or self.songs):
            # we need to keep track of this bool for stopped/ended notifications
            self.Audio = True
            # keep track of onPlayBackStarted events http://trac.xbmc.org/ticket/13064
            self.Count += 1
            log('onPlayBackStarted: %i' % self.Count, SESSION)
            # tags are not available instantly and we don't what to announce right away as the user might be skipping through the songs
            xbmc.sleep(500)
            # don't announce if the user already skipped to the next track or stopped playing audio
            if self.Count == 1 and self.isPlayingAudio():
                # reset counter
                self.Count = 0
                # get tags
                tags = self._get_tags()

                # check if we have anything to submit
                if tags:
                    # announce song
                     self.action(tags)
            elif self.Count != 1:
                # multiple onPlayBackStarted events occurred, only act on the last one
                log('ignoring onPlayBackStarted %i event' % self.Count, SESSION)
                self.Count -= 1

    def onPlayBackEnded( self ):
        # ignore onPlayBackEnded notifications from the video player
        if self.Audio:
            # music playback ended
            self.Audio = False
            log('onPlayBackEnded', SESSION)
            # submit any remaining tracks
            self.action(None)

    def onPlayBackStopped( self ):
        # ignore onPlayBackStopped notifications from the video player
        if self.Audio:
            # we stopped playing audio
            self.Audio = False
            log('onPlayBackStopped', SESSION)
            # submit any remaining tracks
            self.action(None)

    def _get_tags( self ):
        # get track tags
        artist   = self.getMusicInfoTag().getArtist().decode("utf-8")
        album    = self.getMusicInfoTag().getAlbum().decode("utf-8")
        title    = self.getMusicInfoTag().getTitle().decode("utf-8")
        duration = str(self.getMusicInfoTag().getDuration())
        track    = str(self.getMusicInfoTag().getTrack())
        mbid     = '' # musicbrainz id is not yet available
        # get the track id if we're playing last fm radio
        if get_prop('LastFM.RadioPlaying') == 'true':
            streamid = self.getMusicInfoTag().getComment()
        else:
            streamid = ''
        path      = self.getPlayingFile().decode("utf-8")
        timestamp = int(time.time())
        # check if user is listening to online radio
        if path.startswith('http://') or path.startswith('rtmp://'):
            user = '0'
        else:
            user = '1'
        # check if user is listening to last.fm radio
        if path.startswith('http://') and ('last.fm/' in path):
            # set properties for skins
            set_prop('LastFM.CanBan', 'true')
            set_prop('LastFM.RadioPlaying', 'true')
        else:
            # clear prorties regardless of whether they've been set
            clear_prop('LastFM.CanBan')
            clear_prop('LastFM.RadioPlaying')
        # make sure we have artist and trackname, check user settings if we should submit this track
        if artist and track and ((user == '0' and self.radio) or (user == '1' and self.songs)):
            tracktags = dict(artist=artist, album=album, title=title, duration=duration, track=track, mbid=mbid, path=path, timestamp=timestamp, streamid=streamid, user=user)
            log('tracktags: %s' % tracktags, SESSION)
            return tracktags
        else:
            log('user settings prohibits us from submission', SESSION)
            return None

class MyMonitor(xbmc.Monitor):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )
        log('init monitor class', SESSION)
        self.user   = kwargs['user']
        self.pwd    = kwargs['pwd']
        self.action = kwargs['action']

    def onSettingsChanged( self ):
        log('onSettingsChanged', SESSION)
        # sleep before retrieving the new settings
        xbmc.sleep(500)
        # pass the previous user and pass to getsettings, so we can check if they have changed
        self.action(self.user,self.pwd)

if ( __name__ == "__main__" ):
    log('script version %s started' % ADDONVERSION, SESSION)
    Main()
log('script stopped', SESSION)
