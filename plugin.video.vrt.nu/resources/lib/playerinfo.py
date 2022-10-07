# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implementation of PlayerInfo class"""

from __future__ import absolute_import, division, unicode_literals
from threading import Event, Thread
from xbmc import getInfoLabel, Player, PlayList

from apihelper import ApiHelper
from data import CHANNELS
from favorites import Favorites
from kodiutils import addon_id, get_setting_bool, has_addon, jsonrpc, kodi_version_major, log, log_error, notify, set_property, url_for
from resumepoints import ResumePoints
from utils import play_url_to_id, to_unicode


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

        self.asset_str = None
        # FIXME On Kodi 17, use ListItem.Filenameandpath because Player.FilenameAndPath returns the stream manifest url and
        # this definitely breaks "Up Next" on Kodi 17, but this is not supported or available through the Kodi add-on repo anyway
        self.path_infolabel = 'ListItem.Filenameandpath' if kodi_version_major() < 18 else 'Player.FilenameAndPath'
        self.path = None
        self.title = None
        self.ep_id = None
        self.episode_id = None
        self.episode_title = None
        self.video_id = None
        from random import randint
        self.thread_id = randint(1, 10001)
        log(3, '[PlayerInfo {id}] Initialized', id=self.thread_id)
        super(PlayerInfo, self).__init__()

    def onPlayBackStarted(self):  # pylint: disable=invalid-name
        """Called when user starts playing a file"""
        self.path = getInfoLabel(self.path_infolabel)
        if self.path.startswith('plugin://plugin.video.vrt.nu/'):
            self.listen = True
        else:
            self.listen = False
            return

        log(3, '[PlayerInfo {id}] Event onPlayBackStarted', id=self.thread_id)

        # Set property to let wait_for_resumepoints function know that update resume is busy
        set_property('vrtnu_resumepoints', 'busy')

        # Update previous episode when using "Up Next"
        if self.path.startswith('plugin://plugin.video.vrt.nu/play/upnext'):
            self.push_position(position=self.last_pos, total=self.total)

        # Reset episode data
        self.video_id = None
        self.episode_id = None
        self.episode_title = None
        self.asset_str = None
        self.title = None

        ep_id = play_url_to_id(self.path)

        # Avoid setting resumepoints for livestreams
        for channel in CHANNELS:
            if ep_id.get('video_id') and ep_id.get('video_id') == channel.get('live_stream_id'):
                log(3, '[PlayerInfo {id}] Avoid setting resumepoints for livestream {video_id}', id=self.thread_id, video_id=ep_id.get('video_id'))
                self.listen = False

                # Reset vrtnu_resumepoints property before return
                set_property('vrtnu_resumepoints', None)
                return

        # Get episode data needed to update resumepoints from VRT MAX Search API
        # FIXME: Getting single episode data is broken, VRT MAX Search API return a http error 400
        # episode = self.apihelper.get_single_episode_data(video_id=ep_id.get('video_id'), whatson_id=ep_id.get('whatson_id'), video_url=ep_id.get('video_url'))
        episode = None

        # Avoid setting resumepoints without episode data
        if episode is None:
            # Reset vrtnu_resumepoints property before return
            set_property('vrtnu_resumepoints', None)
            return

        from metadata import Metadata
        self.video_id = episode.get('videoId') or None
        self.episode_id = episode.get('episodeId') or None
        self.episode_title = episode.get('title') or None
        self.asset_str = Metadata(None, None).get_asset_str(episode)
        self.title = episode.get('program')

        # Kodi 17 doesn't have onAVStarted
        if kodi_version_major() < 18:
            self.onAVStarted()

    def onAVStarted(self):  # pylint: disable=invalid-name
        """Called when Kodi has a video or audiostream"""
        if not self.listen:
            return
        log(3, '[PlayerInfo {id}] Event onAVStarted', id=self.thread_id)
        self.virtualsubclip_seektozero()
        self.quit.clear()
        self.update_position()
        self.update_total()
        # FIXME: VRT Search API is removed, so up next doesn't work
        # self.push_upnext()

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
        log(3, '[PlayerInfo {id}] Event onPlayBackSeek time={time} offset={offset}', id=self.thread_id, time=time, offset=seekOffset)
        self.last_pos = time // 1000

        # If we seek beyond the end, exit Player
        if self.last_pos >= self.total:
            self.quit.set()
            self.stop()

    def onPlayBackPaused(self):  # pylint: disable=invalid-name
        """Called when user pauses a playing file"""
        if not self.listen:
            return
        log(3, '[PlayerInfo {id}] Event onPlayBackPaused', id=self.thread_id)
        self.update_position()
        self.push_position(position=self.last_pos, total=self.total)
        self.paused = True

    def onPlayBackResumed(self):  # pylint: disable=invalid-name
        """Called when user resumes a paused file or a next playlist item is started"""
        if not self.listen:
            return
        suffix = 'after pausing' if self.paused else 'after playlist change'
        log(3, '[PlayerInfo {id}] Event onPlayBackResumed {suffix}', id=self.thread_id, suffix=suffix)
        self.paused = False

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        """Called when Kodi has ended playing a file"""
        if not self.listen:
            return
        self.last_pos = self.total
        self.quit.set()
        log(3, '[PlayerInfo {id}] Event onPlayBackEnded', id=self.thread_id)

    def onPlayBackError(self):  # pylint: disable=invalid-name
        """Called when playback stops due to an error"""
        if not self.listen:
            return
        self.quit.set()
        log(3, '[PlayerInfo {id}] Event onPlayBackError', id=self.thread_id)

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """Called when user stops Kodi playing a file"""
        if not self.listen:
            return
        self.quit.set()
        log(3, '[PlayerInfo {id}] Event onPlayBackStopped', id=self.thread_id)

    def onPlayerExit(self):  # pylint: disable=invalid-name
        """Called when player exits"""
        log(3, '[PlayerInfo {id}] Event onPlayerExit', id=self.thread_id)
        self.positionthread = None
        self.push_position(position=self.last_pos, total=self.total)

        # Set property to let wait_for_resumepoints function know that update resume is done
        set_property('vrtnu_resumepoints', 'ready')

    def stream_position(self):
        """Get latest stream position while playing"""
        while self.isPlaying() and not self.quit.is_set():
            self.update_position()
            if self.quit.wait(timeout=0.2):
                break
        self.onPlayerExit()

    def add_upnext(self, episode_id):
        """Add Up Next url to Kodi Player"""
        # Reset vrtnu_resumepoints property
        set_property('vrtnu_resumepoints', None)

        url = url_for('play_upnext', episode_id=episode_id)
        self.update_position()
        self.update_total()
        if self.isPlaying() and self.total - self.last_pos < 1:
            log(3, '[PlayerInfo {id}] Add {url} to Kodi Playlist', id=self.thread_id, url=url)
            PlayList(1).add(url)
        else:
            log(3, '[PlayerInfo {id}] Add {url} to Kodi Player', id=self.thread_id, url=url)
            self.play(url)

    def push_upnext(self):
        """Push episode info to Up Next service add-on"""
        if has_addon('service.upnext') and get_setting_bool('useupnext', default=True) and self.isPlaying():
            info_tag = self.getVideoInfoTag()
            next_info = self.apihelper.get_upnext(dict(
                program_title=to_unicode(info_tag.getTVShowTitle()),
                season_number=to_unicode(info_tag.getSeason()),
                episode_number=to_unicode(info_tag.getEpisode()),
                playcount=info_tag.getPlayCount(),
                rating=info_tag.getRating(),
                path=self.path,
                runtime=self.total,
            ))
            if next_info:
                from base64 import b64encode
                from json import dumps
                data = [to_unicode(b64encode(dumps(next_info).encode()))]
                sender = '{addon_id}.SIGNAL'.format(addon_id=addon_id())
                notify(sender=sender, message='upnext_data', data=data)

    def update_position(self):
        """Update the player position, when possible"""
        try:
            self.last_pos = self.getTime()
        except RuntimeError:
            pass

    def virtualsubclip_seektozero(self):
        """VRT MAX already offers some programs (mostly current affairs programs) as video on demand while the program is still being broadcasted live.
           To do so, a start timestamp is added to the livestream url so the Unified Origin streaming platform knows
           it should return a time bounded manifest file that indicates the beginning of the program.
           This is called a Live-to-VOD stream or virtual subclip: https://docs.unified-streaming.com/documentation/vod/player-urls.html#virtual-subclips
           e.g. https://live-cf-vrt.akamaized.net/groupc/live/8edf3bdf-7db3-41c3-a318-72cb7f82de66/live.isml/.mpd?t=2020-07-20T11:07:00

           For some unclear reason the virtual subclip defined by a single start timestamp still behaves as a ordinary livestream
           and starts at the live edge of the stream. It seems this is not a Kodi or Inputstream Adaptive bug, because other players
           like THEOplayer or DASH-IF's reference player treat this kind of manifest files the same way.
           The only difference is that seeking to the beginning of the program is possible. So if the url contains a single start timestamp,
           we can work around this problem by automatically seeking to the beginning of the program.
        """
        playing_file = self.getPlayingFile()
        if any(param in playing_file for param in ('?t=', '&t=')):
            try:  # Python 3
                from urllib.parse import parse_qs, urlsplit
            except ImportError:  # Python 2
                from urlparse import parse_qs, urlsplit
            import re
            # Detect single start timestamp
            timestamp = parse_qs(urlsplit(playing_file).query).get('t')[0]
            rgx = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
            is_single_start_timestamp = bool(re.match(rgx, timestamp))
            if is_single_start_timestamp:
                # Check resume status
                resume_info = jsonrpc(method='Player.GetItem', params=dict(playerid=1, properties=['resume'])).get('result')
                if resume_info:
                    resume_position = resume_info.get('item').get('resume').get('position')
                    is_resumed = abs(resume_position - self.getTime()) < 1
                    # Seek to zero if the user didn't resume the program
                    if not is_resumed:
                        log(3, '[PlayerInfo {id}] Virtual subclip: seeking to the beginning of the program', id=self.thread_id)
                        self.seekTime(0)
                else:
                    log_error('Failed to start virtual subclip {playing_file} at start timestamp', playing_file=playing_file)

    def update_total(self):
        """Update the total video time"""
        try:
            total = self.getTotalTime()
            # Kodi Player sometimes returns a total time of 0.0 and this causes unwanted behaviour with VRT MAX Resumepoints API.
            if total > 0.0:
                self.total = total
        except RuntimeError:
            pass

    def push_position(self, position, total):
        """Push player position to VRT MAX resumepoints API and reload container"""
        # Not all content has an video_id
        if not self.video_id:
            return

        # Push resumepoint to VRT MAX
        self.resumepoints.update_resumepoint(
            video_id=self.video_id,
            asset_str=self.asset_str,
            title=self.title,
            position=position,
            total=total,
            path=self.path,
        )
