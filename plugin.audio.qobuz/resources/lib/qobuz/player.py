'''
    qobuz.player
    ~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmc  # @UnresolvedImport
import xbmcgui  # @UnresolvedImport

import qobuz  # @UnresolvedImport
from debug import warn
from gui.util import notifyH, isFreeAccount, lang, setResolvedUrl, notify_warn, notify_log
from gui.util import getSetting
from node import Flag, getNode

keyTrackId = 'QobuzPlayerTrackId'


def notify_restriction(track):
    restrictions = ''
    for restriction in track.get_restrictions():
        restrictions += '%s\n' % restriction
    if restrictions != '':
        notify_warn("Restriction", restrictions)


class QobuzPlayer(xbmc.Player):
    """
        @class: QobuzPlayer
    """

    def __init__(self, **ka):
        """Constructor"""
        ka['type'] = 0
        super(QobuzPlayer, self).__init__()
        self.track_id = None
        self.total = None
        self.elapsed = None

    def play(self, track_id):
        """Playing track given a track id
        """
        track = getNode(Flag.TRACK, {'nid': track_id})
        if not track.fetch(None, 1, Flag.TRACK, Flag.NONE):
            warn(self, "Cannot get track data")
            return False
        if not track.is_playable():
            warn(self, "Cannot get streaming URL")
            return False
        item = track.makeListItem()
        track.item_add_playing_property(item)
        """Some tracks are not authorized for stream and a 60s sample is
        returned, in that case we overwrite the song duration
        """
        if track.is_sample():
            item.setInfo(
                'music', infoLabels={
                    'duration': 60,
                })
            """Don't warn for free account (all songs except purchases are 60s
            limited)
            """
            if not isFreeAccount():
                notify_warn("Qobuz", "Sample returned")
        xbmcgui.Window(10000).setProperty(keyTrackId, track_id)
        """Notify
        """
        if getSetting('notification_playingsong', isBool=True):
            notify_restriction(track)
            notifyH(lang(30132), track.get_label(), image=track.get_image())

        """We are called from playlist...
        """
        if qobuz.boot.handle == -1:
            super(QobuzPlayer, self).play(track.get_streaming_url(),
                                          item, False)
        else:
            setResolvedUrl(handle=qobuz.boot.handle,
                           succeeded=True,
                           listitem=item)
        return True
