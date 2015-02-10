#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.
import xbmc
import xbmcgui

import qobuz
from debug import warn
from gui.util import notifyH, isFreeAccount, lang, setResolvedUrl, getImage, \
    getSetting
from node import Flag, getNode

"""
    @class: QobuzPlayer
"""
keyTrackId = 'QobuzPlayerTrackId'

class QobuzPlayer(xbmc.Player):

    def __init__(self, **ka):
        ka['type'] = xbmc.PLAYER_CORE_AUTO
        super(QobuzPlayer, self).__init__()
        self.track_id = None
        self.total = None
        self.elapsed = None

    """
        Playing track given a track id
    """
    def play(self, track_id):
        track = getNode(Flag.TRACK, {'nid': track_id})
        if not track.fetch(None, 1, Flag.TRACK, Flag.NONE):
            warn(self, "Cannot get track data")
#            label = "Maybe an invalid track id"
#            item = xbmcgui.ListItem("No track information", label, '', 
#                                    getImage('icon-error-256'), '')
            return False
        if not track.is_playable():
            warn(self, "Cannot get streaming URL")
            return False
        item = track.makeListItem()
        track.item_add_playing_property(item)
        '''Some tracks are not authorized for stream and a 60s sample is
        returned, in that case we overwrite the song duration
        '''
        if track.is_sample():
            item.setInfo(
                'music', infoLabels={
                'duration': 60,
            })
            '''Don't warn for free account (all songs except purchases are 60s
            limited)
            '''
            if not isFreeAccount():
                notifyH("Qobuz", "Sample returned")
        xbmcgui.Window(10000).setProperty(keyTrackId, track_id) 
        """
            Notify
        """
        if getSetting('notification_playingsong', isBool=True):
            notifyH(lang(34000), track.get_label(), track.get_image())
        """
            We are called from playlist...
        """
        if qobuz.boot.handle == -1:
            super(QobuzPlayer, self).play(track.get_streaming_url(), 
                                          item, False)
        else:
            setResolvedUrl(handle=qobuz.boot.handle,
                succeeded=True,
                listitem=item)
        return True
