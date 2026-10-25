"""Events enhancing behavior of default Kodi player"""
from datetime import datetime, timezone
from typing import Optional, Union
import json

import xbmc
import xbmcgui
import xbmcaddon
from resources.lib import api
from resources.lib.utils import PLUGIN_NAME, PLUGIN_VERSION

# this player send request to Arte TV API
# to synchronise playback progress
# when playback is paused or stopped or crashed
# https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python___player_c_b.html


# pylint: disable=too-many-instance-attributes
class Player(xbmc.Player):
    """Events enhancing behavior of default Kodi player
    used to track in Arte TV progress time and history"""

    def __init__(self, settings, token, extended_program_data=None):
        super().__init__()
        self.last_time = 0
        self.consent_tracking = settings.consent_tracking
        # consent tracking is required to build client data
        self.client_data = self._build_client_data(token)
        # program data is built at play time, when the actual media item is known
        # and then they are cached in this variable
        self.program_data = None
        self.playlist = None
        self.fallback_listitem = None
        self.token = token
        self.extended_program_data = extended_program_data
        self.did_process_first_item_offset = False

    ####
    # client data management at player creation time
    ####

    def _build_user_data(self, token):
        """Build the user object expected by ``api.track_playback``."""
        if isinstance(token, dict) and token.get('user_id'):
            return {
                'id': token.get('user_id'),
                'type': 'AUTHENTICATED',
            }
        return {
            'type': 'ANONYMOUS',
        }

    def _build_client_data(self, token):
        """Build the client_data payload consumed by api.track_playback()."""

        return {
            'client_id': PLUGIN_NAME,
            'app_name': PLUGIN_NAME,
            'app_version': PLUGIN_VERSION,
            'platform': 'kodi',
            'locale': xbmc.getLanguage(xbmc.ISO_639_1),
            'consent': self.consent_tracking,
            'user': self._build_user_data(token),
        }

    ####
    # program data management built at play time when the actual media item is known
    ####

    def set_playback_context(self, listitem=None, playlist=None):
        """Keep Kodi playback objects available for AVStarted metadata lookup."""
        self.fallback_listitem = listitem
        self.playlist = playlist
        if self.playlist is not None:
            current_position = self.playlist.getposition()
            current_item = self.playlist[current_position]
        else:
            current_item = self.fallback_listitem
        self.program_data = self.build_program_data(current_item)

    def build_program_data(self, listitem):
        """Build the program object expected by ``api.track_playback``.

        The metadata is created when Kodi reports that the actual media item
        has started, so playlist transitions use the current list item.
        """
        if listitem is None:
            xbmc.log("Unable to build program data for playback. No listitem found.",
                     level=xbmc.LOGWARNING)
            return {}

        selected_videotag: 'xbmc.InfoTagVideo' = listitem.getVideoInfoTag()

        program_data = {
            'program_id': listitem.getProperty('arte_program_id'),
            'program_type': listitem.getProperty('arte_program_type'),
            'stream_url': listitem.getPath(),
            'title': selected_videotag.getTitle(),
            'duration': selected_videotag.getDuration(),
            'page_language': xbmc.getLanguage(xbmc.ISO_639_1),
            'page_url': xbmc.getInfoLabel('Container.FolderPath'),
        }

        tracking_fields = {
            'slug': listitem.getProperty('arte_slug'),
            'program_type': listitem.getProperty('arte_program_type'),
            'category': listitem.getProperty('arte_category'),
            'subcategory': listitem.getProperty('arte_subcategory'),
            'genre': listitem.getProperty('arte_genre'),
            'kind': listitem.getProperty('arte_kind'),
            'associated_collections': listitem.getProperty('arte_associated_collections'),
            'image_format': listitem.getProperty('arte_image_format'),
        }
        for key, value in tracking_fields.items():
            # remove key associated with null or empty value
            if value is None or value == '':
                continue
            # associated_collections is a list of strings separated by commas,
            # but Kodi ListItem properties are always strings, so it needs to be parsed
            if key == 'associated_collections':
                try:
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, list):
                        program_data[key] = parsed_value
                    else:
                        program_data[key] = [value]
                except (TypeError, ValueError):
                    program_data[key] = [item.strip() for item in value.split(',') if item.strip()]
                continue

            program_data[key] = value

        return program_data

    def onAVStarted(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Refresh the current item and track the start of playback."""
        self.program_data = {}
        try:
            # Kodi exposes the item that is actually playing here with player.getPlayingItem()
            current_item = self.getPlayingItem()

            self.program_data = self.build_program_data(current_item)

            # Kodi may return the current item without custom ListItem
            # properties. Recover the item from the playlist or initial play
            # context in that case.
            if not self.program_data.get('program_id'):
                if self.playlist is not None:
                    current_position = self.playlist.getposition()
                    current_item = self.playlist[current_position]
                else:
                    current_item = self.fallback_listitem
                self.program_data = self.build_program_data(current_item)

            # Only the first playback item can resume. Consider it after
            # fallback recovery so missing Kodi ListItem properties don't
            # suppress its saved offset, and never seek on playlist transitions.
            if not self.did_process_first_item_offset and current_item is not None:
                start_time = current_item.getProperty('arte_start_offset')
                self.did_process_first_item_offset = True
                if start_time is not None and start_time.isdecimal() and start_time.strip('0'):
                    self.seekTime(float(start_time))
        except (AttributeError, RuntimeError, TypeError, ValueError):
            xbmc.log(
                "Unable to rebuild program data for the current playback item.",
                level=xbmc.LOGWARNING
            )
        self.synch_progress('VIDEO_STARTED')

    ####
    # playback management and synchronisation along playback events
    ####

    def _get_jsonrpc_properties(self):
        """Return optional Kodi player and application properties."""
        try:
            response = xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Player.GetProperties",'
                '"params":{"playerid":1,"properties":['
                '"audiostreams","currentaudiostream",'
                '"subtitles","subtitle streams","currentsubtitle","subtitleenabled"]}}')
            player_properties = json.loads(response).get('result', {})
            response = xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Application.GetProperties",'
                '"params":{"properties":["muted","volume"]}}')
            application_properties = json.loads(response).get('result', {})
            return {**player_properties, **application_properties}
        except (AttributeError, TypeError, ValueError, KeyError):
            return {}

    def build_playback_data(self, action):
        """Build the playback object expected by ``api.track_playback``."""
        properties = self._get_jsonrpc_properties()
        current_audio = properties.get('currentaudiostream') or {}
        current_subtitles = properties.get('currentsubtitle') or {}
        # subtitle_enabled = bool(properties.get('subtitleenabled', False))
        if action in ('VIDEO_STOPPED', 'VIDEO_ENDED', 'VIDEO_ERROR'):
            # Kodi closes the media before terminal callbacks are delivered.
            current_time = max(0, round(self.last_time))
        else:
            try:
                current_time = max(0, round(self.getTime()))
            except RuntimeError:
                current_time = max(0, round(self.last_time))
        playback_data = {
            'event_time': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'action': action,
            'timecode': current_time,
            'previous_timecode': self.last_time,
            'audio_track_language': current_audio.get('language', 'fr'),
            'audio_track_type': 'STANDARD',
            'subtitles_track_language': current_subtitles.get('language', 'fr'),
            'subtitles_track_type': 'FORCED',
            'sound_muted': properties.get('muted', False) or properties.get('volume', 10) == 0,
            'playback_mode': 'DEVICE',
        }
        self.last_time = current_time
        return playback_data

    def is_playback(self):
        """Track progress time during playback"""
        try:
            # need to keep track of last time to avoid
            # RuntimeError: Kodi is not playing any media file
            # when calling player.getTime() in onPlayBackStopped()
            self.last_time = self.getTime()
            # when playing video playlist, isPlayingVideo() is False, isPlaying() is True
            return (self.isPlaying() or self.isPlayingVideo() or self.isPlayingAudio()) \
                and self.last_time >= 0
        # pylint: disable=broad-exception-caught
        # https://codedocs.xyz/MartijnKaijser/xbmc/group__python___player.html
        except Exception:
            return False

    def _keep_or_reset_start_offset(self, listitem):
        """Check the resume offset, ask end user to keep it or reset it."""
        if listitem is None:
            return

        try:
            offset_seconds = int(listitem.getProperty('arte_start_offset'))
        except (TypeError, ValueError, OverflowError):
            return
        if offset_seconds <= 0:
            return

        if offset_seconds >= 3600:
            hours, remainder = divmod(offset_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            start_offset = f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        else:
            minutes, seconds = divmod(offset_seconds, 60)
            start_offset = f'{minutes:02d}:{seconds:02d}'

        item_label = listitem.getVideoInfoTag().getTitle()
        addon = xbmcaddon.Addon()
        keep_start_offset = xbmcgui.Dialog().yesno(
            addon.getLocalizedString(30065),
            addon.getLocalizedString(30066).format(
                item_label=item_label,
                start_offset=start_offset
            ),
            # if yesnocustom, needs to stop playback if cancelled
            # xbmc.getLocalizedString(222),
            autoclose=10000,
            defaultbutton=xbmcgui.DLG_YESNO_YES_BTN
        )
        if not keep_start_offset:
            listitem.setProperty('arte_start_offset', '0')

    def play(self, item: Union[str, 'xbmc.PlayList'] = "",
             listitem: Optional['xbmcgui.ListItem'] = None,
             windowed: bool = False,
             startpos: int = -1) -> None:
        """
        Ask end-user to keep or reset start offset before playing the item.
        Start offset is used to seek the playback position. Otherwise start from the beginning.
        """
        self._keep_or_reset_start_offset(listitem)
        super().play(item, listitem, windowed, startpos)

    def synch_progress(self, action):
        """Track progress/playback time and share it with Arte TV,
        so that other device with the user account can share progress and history"""

        # Only send tracking data if the user has consented to tracking
        if not self.consent_tracking:
            xbmc.log("User has not consented to tracking. Skipping progress synchronisation.",
                     level=xbmc.LOGINFO)
            return 403

        # Only send tracking data if we have program_data already built
        # and necessary time to build playback_data
        if not self.program_data or not self.program_data.get('program_id'):
            xbmc.log("Unable to synchronise progress. Missing program_id.",
                     level=xbmc.LOGWARNING)
            return 400
        program_id = self.program_data.get('program_id')

        # Ignore timecode 0: playback has not progressed yet, so there is no
        # useful position to synchronize with Arte.
        if not self.last_time:
            xbmc.log(f"Unable to synchronise progress for {program_id}. Missing time to synch.",
                     level=xbmc.LOGWARNING)
            return 400
        self.last_time = round(self.last_time)

        status = api.track_playback(
            self.token, self.client_data, self.program_data, self.build_playback_data(action),
        )
        # keep internal progress cache up to date, if arte updates its state sucessfully
        status_code = getattr(status, 'status_code', None)
        if (self.extended_program_data is not None and isinstance(status_code, int)
                and 200 <= status_code < 300):
            self.extended_program_data.update_program(
                program_id, self.last_time, self.program_data.get('duration')
            )

        xbmc.log(f"Synchronisation of progress {self.last_time}s for program_id {program_id}" +
                 f" ended with {status}",
                 level=xbmc.LOGINFO)

        return status

    def onPlayBackStopped(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when user stops playing"""
        self.synch_progress('VIDEO_STOPPED')

    def onPlayBackEnded(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi stops playing"""
        self.synch_progress('VIDEO_ENDED')

    def onPlayBackError(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi stops playing"""
        self.synch_progress('VIDEO_ERROR')

    def onPlayBackPaused(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi pauses playing"""
        self.synch_progress('VIDEO_PAUSED')
