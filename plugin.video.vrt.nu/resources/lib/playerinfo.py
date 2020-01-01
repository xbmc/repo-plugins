# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implementation of PlayerInfo class"""

from __future__ import absolute_import, division, unicode_literals
from threading import Event, Thread
from xbmc import getInfoLabel, Player, PlayList

from apihelper import ApiHelper
from data import CHANNELS
from favorites import Favorites
from kodiutils import addon_id, get_setting, has_addon, kodi_version, log, notify, set_property
from resumepoints import ResumePoints
from utils import assetpath_to_id, play_url_to_id, to_unicode, url_to_episode


class PlayerInfo(Player, object):  # pylint: disable=useless-object-inheritance
    """Class for communication with Kodi player"""

    def __init__(self):
        """PlayerInfo initialisation"""
        self.resumepoints = ResumePoints()
        self.apihelper = ApiHelper(Favorites(), self.resumepoints)
        self.last_pos = None
        self.listen = False
        self.paused = False
        self.total = 100
        self.positionthread = None
        self.quit = Event()

        self.asset_id = None
        # FIXME On Kodi 17, use ListItem.Filenameandpath because Player.FilenameAndPath returns the stream manifest url and
        # this definitely breaks "Up Next" on Kodi 17, but this is not supported or available through the Kodi add-on repo anyway
        self.path_infolabel = 'ListItem.Filenameandpath' if kodi_version() < 18 else 'Player.FilenameAndPath'
        self.path = None
        self.title = None
        self.ep_id = None
        self.url = None
        self.whatson_id = None
        from random import randint
        self.thread_id = randint(1, 10001)
        log(3, '[PlayerInfo %d] Initialized' % self.thread_id)
        super(PlayerInfo, self).__init__()

    def onPlayBackStarted(self):  # pylint: disable=invalid-name
        """Called when user starts playing a file"""
        self.path = getInfoLabel(self.path_infolabel)
        if self.path.startswith('plugin://plugin.video.vrt.nu/'):
            self.listen = True
        else:
            self.listen = False
            return

        log(3, '[PlayerInfo %d] Event onPlayBackStarted' % self.thread_id)

        # Update previous episode when using "Up Next"
        if self.path.startswith('plugin://plugin.video.vrt.nu/play/upnext'):
            self.push_position(position=self.last_pos, total=self.total)

        # Reset episode data
        self.asset_id = None
        self.title = None
        self.url = None
        self.whatson_id = None

        ep_id = play_url_to_id(self.path)

        # Avoid setting resumepoints for livestreams
        for channel in CHANNELS:
            if ep_id.get('video_id') and ep_id.get('video_id') == channel.get('live_stream_id'):
                log(3, '[PlayerInfo %d] Avoid setting resumepoints for livestream %s' % (self.thread_id, ep_id.get('video_id')))
                self.listen = False
                return

        # Get episode data needed to update resumepoints from VRT NU Search API
        episode = self.apihelper.get_single_episode_data(video_id=ep_id.get('video_id'), whatson_id=ep_id.get('whatson_id'), video_url=ep_id.get('video_url'))

        # Avoid setting resumepoints without episode data
        if episode is None:
            return

        self.asset_id = assetpath_to_id(episode.get('assetPath'))
        self.title = episode.get('program')
        self.url = url_to_episode(episode.get('url', ''))
        self.whatson_id = episode.get('whatsonId') or None  # Avoid empty string

        # Kodi 17 doesn't have onAVStarted
        if kodi_version() < 18:
            self.onAVStarted()

    def onAVStarted(self):  # pylint: disable=invalid-name
        """Called when Kodi has a video or audiostream"""
        if not self.listen:
            return
        log(3, '[PlayerInfo %d] Event onAVStarted' % self.thread_id)
        self.quit.clear()
        self.update_position()
        self.update_total()
        self.push_upnext()

        # StreamPosition thread keeps running when watching multiple episode with "Up Next"
        # only start StreamPosition thread when it doesn't exist yet.
        if not self.positionthread:
            self.positionthread = Thread(target=self.stream_position, name='StreamPosition')
            self.positionthread.start()

    def onAVChange(self):  # pylint: disable=invalid-name
        """Called when Kodi has a video, audio or subtitle stream. Also happens when the stream changes."""

    def onPlayBackSeek(self, time, seekOffset):  # pylint: disable=invalid-name
        """Called when user seeks to a time"""
        if not self.listen:
            return
        log(3, '[PlayerInfo %d] Event onPlayBackSeek time=%d offset=%d' % (self.thread_id, time, seekOffset))
        self.last_pos = time // 1000

        # If we seek beyond the start or end, set property to let wait_for_resumepoints function know that update resume is busy
        if self.last_pos >= self.total:
            set_property('vrtnu_resumepoints', 'busy')
            # Exit Player faster
            self.quit.set()
            self.stop()

        if self.last_pos < 0:
            set_property('vrtnu_resumepoints', 'busy')

    def onPlayBackPaused(self):  # pylint: disable=invalid-name
        """Called when user pauses a playing file"""
        if not self.listen:
            return
        log(3, '[PlayerInfo %d] Event onPlayBackPaused' % self.thread_id)
        self.update_position()
        self.push_position(position=self.last_pos, total=self.total)
        self.paused = True

    def onPlayBackResumed(self):  # pylint: disable=invalid-name
        """Called when user resumes a paused file or a next playlist item is started"""
        if not self.listen:
            return
        suffix = 'after pausing' if self.paused else 'after playlist change'
        log(3, '[PlayerInfo %d] Event onPlayBackResumed %s' % (self.thread_id, suffix))
        self.paused = False

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        """Called when Kodi has ended playing a file"""
        if not self.listen:
            return
        self.last_pos = self.total
        self.quit.set()
        log(3, '[PlayerInfo %d] Event onPlayBackEnded' % self.thread_id)

    def onPlayBackError(self):  # pylint: disable=invalid-name
        """Called when playback stops due to an error"""
        if not self.listen:
            return
        self.quit.set()
        log(3, '[PlayerInfo %d] Event onPlayBackError' % self.thread_id)

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """Called when user stops Kodi playing a file"""
        if not self.listen:
            return
        self.quit.set()
        log(3, '[PlayerInfo %d] Event onPlayBackStopped' % self.thread_id)

    def onPlayerExit(self):  # pylint: disable=invalid-name
        """Called when player exits"""
        log(3, '[PlayerInfo %d] Event onPlayerExit' % self.thread_id)
        self.positionthread = None
        self.push_position(position=self.last_pos, total=self.total)

    def stream_position(self):
        """Get latest stream position while playing"""
        while self.isPlaying() and not self.quit.is_set():
            self.update_position()
            if self.quit.wait(timeout=0.2):
                break
        self.onPlayerExit()

    def add_upnext(self, video_id):
        """Add Up Next url to Kodi Player"""
        url = 'plugin://plugin.video.vrt.nu/play/upnext/%s' % video_id
        self.update_position()
        self.update_total()
        if self.isPlaying() and self.total - self.last_pos < 1:
            log(3, '[PlayerInfo] %d Add %s to Kodi Playlist' % (self.thread_id, url))
            PlayList(1).add(url)
        else:
            log(3, '[PlayerInfo] %d Add %s to Kodi Player' % (self.thread_id, url))
            self.play(url)

    def push_upnext(self):
        """Push episode info to Up Next service add-on"""
        if has_addon('service.upnext') and get_setting('useupnext', 'true') == 'true' and self.isPlaying():
            info_tag = self.getVideoInfoTag()
            next_info = self.apihelper.get_upnext(dict(
                program=to_unicode(info_tag.getTVShowTitle()),
                playcount=info_tag.getPlayCount(),
                rating=info_tag.getRating(),
                path=self.path,
                runtime=self.total,
            ))
            if next_info:
                from base64 import b64encode
                from json import dumps
                data = [to_unicode(b64encode(dumps(next_info).encode()))]
                sender = '%s.SIGNAL' % addon_id()
                notify(sender=sender, message='upnext_data', data=data)

    def update_position(self):
        """Update the player position, when possible"""
        try:
            self.last_pos = self.getTime()
        except RuntimeError:
            pass

    def update_total(self):
        """Update the total video time"""
        try:
            total = self.getTotalTime()
            # Kodi Player sometimes returns a total time of 0.0 and this causes unwanted behaviour with VRT NU Resumepoints API.
            if total > 0.0:
                self.total = total
        except RuntimeError:
            pass

    def push_position(self, position, total):
        """Push player position to VRT NU resumepoints API and reload container"""
        # Not all content has an asset_id
        if not self.asset_id:
            return

        # Set property to let wait_for_resumepoints function know that update resume is busy
        set_property('vrtnu_resumepoints', 'busy')

        # Push resumepoint to VRT NU
        self.resumepoints.update(
            asset_id=self.asset_id,
            title=self.title,
            url=self.url,
            position=position,
            total=total,
            whatson_id=self.whatson_id
        )

        # Set property to let wait_for_resumepoints function know that update resume is done
        set_property('vrtnu_resumepoints', 'ready')
