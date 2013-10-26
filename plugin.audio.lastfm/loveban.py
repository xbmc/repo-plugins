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

SESSION = 'loveban'

class LoveBan:
    def __init__( self, params ):
        artist = xbmc.getInfoLabel('MusicPlayer.Artist').decode("utf-8")
        song   = xbmc.getInfoLabel('MusicPlayer.Title').decode("utf-8")
        action = params.get( 'action' )
        # check if the skin provided valid params
        if artist and song and (action == 'LastFM.Love' or action == 'LastFM.Ban' or action == 'LastFM.UnLove' or action == 'LastFM.UnBan'):
            settings = read_settings(SESSION)
            sesskey  = settings['sesskey']
            confirm  = settings['confirm']
            # check if we have an artist name and song title
            if sesskey:
                self._submit_loveban(action, artist, song, confirm, sesskey)
            else:
                log('no sessionkey, artistname or songname provided', SESSION)

    def _submit_loveban( self, action, artist, song, confirm, sesskey ):
        # love a track
        if action == 'LastFM.Love':
            action = 'track.love'
            # popup a confirmation dialog if specified by the skin
            if confirm:
                dialog = xbmcgui.Dialog()
                ack = dialog.yesno(LANGUAGE(32011), LANGUAGE(32012), artist + ' - ' + song)
                if not ack:
                    return
            # submit data to last.fm
            result = self._post_data(action, artist, song, sesskey)
            # notify user on success / fail
            if result:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32014) % song, 7000)
            else:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32015) % song, 7000)
        # ban a track
        elif action == 'LastFM.Ban' and xbmcgui.Window( 10000 ).getProperty('LastFM.RadioPlaying') == 'true':
            action = 'track.ban'
            # popup a confirmation dialog if specified by the skin
            if confirm:
                dialog = xbmcgui.Dialog()
                ack = dialog.yesno(LANGUAGE(32011), LANGUAGE(32013), artist + ' - ' + song)
                if not ack:
                    return
            # submit data to last.fm
            result = self._post_data(action, artist, song, sesskey)
            # notify user on success / fail
            if result:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32016) % song, 7000)
            else:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32017) % song, 7000)
            # if a song is banned, we skip to the next track
            xbmc.executebuiltin('playercontrol(next)')
        # unlove a track
        elif action == 'LastFM.UnLove':
            action = 'track.unlove'
            # popup a confirmation dialog if specified by the skin
            if confirm:
                dialog = xbmcgui.Dialog()
                ack = dialog.yesno(LANGUAGE(32011), LANGUAGE(32018), artist + ' - ' + song)
                if not ack:
                    return
            # submit data to last.fm
            result = self._post_data(action, artist, song, sesskey)
            # notify user on success / fail
            if result:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32020) % song, 7000)
            else:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32021) % song, 7000)
        # unban a track
        elif action == 'LastFM.UnBan':
            action = 'track.unban'
            # popup a confirmation dialog if specified by the skin
            if confirm:
                dialog = xbmcgui.Dialog()
                ack = dialog.yesno(LANGUAGE(32011), LANGUAGE(32019), artist + ' - ' + song)
                if not ack:
                    return
            # submit data to last.fm
            result = self._post_data(action, artist, song, sesskey)
            # notify user on success / fail
            if result:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32022) % song, 7000)
            else:
                msg = 'Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32023) % song, 7000)
        xbmc.executebuiltin(msg.encode("utf-8"))

    def _post_data( self, action, artist, song, sesskey ):
        # love, ban, unlove, unban
        log('love/ban submission', SESSION)
        # collect post data
        data = {}
        data['method'] = action
        data['artist'] = artist
        data['track'] = song
        data['sk'] = sesskey
        # connect to last.fm
        result = lastfm.post(data, SESSION)
        if not result:
            return False
        # parse response
        if result.has_key('status'):
            result = result['status']
            return True
        elif result.has_key('error'):
            code = result['error']
            msg = result['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('%s returned failed response: %s' % (action,msg), SESSION)
            # evaluate error response
            if code == 9:
                # inavlid SESSION key response, drop our key
                drop_sesskey()
        else:
            log('%s returned an unknown response' % action, SESSION)
        return False
