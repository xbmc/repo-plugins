import time
from urllib.parse import unquote

from bossanova808.logger import Logger
from bossanova808.utilities import *
# noinspection PyPackages
from .store import Store
# noinspection PyPackages
from .playback import Playback
import xbmc
import json


class KodiPlayer(xbmc.Player):
    """
    This class represents/monitors the Kodi video player
    """

    def __init__(self, *args):
        xbmc.Player.__init__(self)
        Logger.debug('KodiPlayer __init__')

    # Use on AVStarted (vs Playback started) we want to record a playback only if the user actually _saw_ a video...
    def onAVStarted(self):
        Logger.info('onAVStarted')
        # Reload the Switchback list in case the plugin is being called after a list deletion
        Store.load_config_from_settings()

        if xbmc.getCondVisibility('Player.HasMedia'):

            # In general this tool only makes sense for video, really, but just in case, we support music.
            # Short circuit here if music is playing & the user has requested we do not record music playback via the settings (=default)
            if not xbmc.getCondVisibility('Player.HasVideo') and not Store.include_music:
                return

            # Clear any legacy recorded playback details by creating a new Playback object
            Store.current_playback = Playback()
            Store.current_playback.file = self.getPlayingFile()

            # @TODO - add support for addons/plugins?  Too many things won't play back without a token etc, so not for V1!
            if 'http' in Store.current_playback.file:
                Logger.info("Not recording playback as is an http source (plugin/addon) - not yet supported.")
                return
            # @TODO - add support for PVR recordings?  Experience errors playing these back using the PVR file URL??
            elif 'recordings' in Store.current_playback.file:
                Logger.warning("Not recording playback as is a PVR recording - not yet supported.")
                return

            # Get more info on what is playing (empty values are returned if they're not relevant/set)
            # Unfortunately, when playing from an offscreen playlist, the GetItem properties don't seem to be set,
            # but can get info from the InfoLabels instead it seems, see: https://forum.kodi.tv/showthread.php?tid=379301

            if xbmc.getCondVisibility('Player.HasVideo'):
                stub = "Video"
            else:
                stub = "Music"

            json_dict = {
                    "jsonrpc": "2.0",
                    "id": "XBMC.GetInfoLabels",
                    "method": "XBMC.GetInfoLabels",
                    "params": {"labels": [
                            "Player.Folderpath",
                            "Player.Art(thumb)",
                            "Player.Art(poster)",
                            "Player.Art(fanart)",
                            "Player.Duration",
                            "Player.Art(tvshow.poster)",
                            "Player.Art(movie.poster)",
                            # Episodes
                            "VideoPlayer.DBID",
                            "VideoPlayer.Title",
                            "VideoPlayer.Year",
                            "VideoPlayer.TVShowTitle",
                            "VideoPlayer.TvShowDBID",
                            "VideoPlayer.Season",
                            "VideoPlayer.Episode",
                            # PVR
                            "VideoPlayer.ChannelName",
                            "VideoPlayer.ChannelNumberLabel",
                            "VideoPlayer.ChannelGroup",
                            # Music
                            "MusicPlayer.DBID",
                            "MusicPlayer.Title",
                            "MusicPlayer.Year",
                            "MusicPlayer.Album",
                            "MusicPlayer.Artist",
                            "MusicPlayer.TrackNumber"
                    ]}
            }

            query = json.dumps(json_dict)
            properties_json = send_kodi_json(f'Get playback details from InfoLabels', query)
            properties = properties_json['result']

            # WHAT IS THE SOURCE - Kodi Library (...get DBID), PVR, or Non-Library Media?
            Store.current_playback.dbid = int(properties.get(f'{stub}Player.DBID')) if properties.get(f'{stub}Player.DBID') else None
            if Store.current_playback.dbid:
                Store.current_playback.source = "kodi_library"
            elif properties['VideoPlayer.ChannelName']:
                Store.current_playback.source = "pvr_live"
            else:
                # Logger.info("Not from Kodi library, not PVR, not an http source - must be a non library media file")
                Store.current_playback.source = "file"

            # TITLE
            Store.current_playback.title = properties.get(f'{stub}Player.Title', "")

            # PLAYBACK TIME and DURATION
            Store.current_playback.totaltime = Store.kodi_player.getTotalTime()
            # Times in form 1:35:23 don't seem to work properly, seeing inaccurate durations, so use float from getTotalTime() below instead
            Store.current_playback.duration = Store.kodi_player.getTotalTime()
            # This will get updated as playback progress by the service, but initialise them here...
            Store.current_playback.resumetime = Store.kodi_player.getTime()

            # ARTWORK - POSTER, FANART and THUMBNAIL
            Store.current_playback.poster = properties.get('Player.Art(tvshow.poster)') or properties.get('Player.Art(poster)')
            Store.current_playback.fanart = unquote(properties['Player.Art(fanart)']).replace("image://", "").rstrip("/")
            if not Store.current_playback.poster:
                Store.current_playback.poster = unquote(properties['Player.Art(fanart)']).replace("image://", "").rstrip("/")
            Store.current_playback.thumbnail = unquote(properties['Player.Art(thumb)']).replace("image://", "").rstrip("/")
            # @TODO - can this be improved?  Why does Kodi return e.g. '.mkv' files for thumbnail - extracted thumbs??
            if 'jpg' not in Store.current_playback.thumbnail:
                Store.current_playback.thumbnail = unquote(properties['Player.Art(fanart)']).replace("image://", "").rstrip("/")

            # DETERMINE THE MEDIA TYPE - not 100% on the logic here...
            if properties['VideoPlayer.TVShowTitle']:
                Store.current_playback.type = "episode"
                Store.current_playback.tvshowdbid = int(properties['VideoPlayer.TvShowDBID']) if properties.get('VideoPlayer.TvShowDBID') else None
            elif properties['VideoPlayer.ChannelName']:
                Store.current_playback.type = "video"
                if 'channels' in Store.current_playback.file:
                    Store.current_playback.source = "pvr.live"
                elif 'recordings' in Store.current_playback.file:
                    Store.current_playback.source = "pvr.recording"
            elif stub == 'Video' and Store.current_playback.dbid:
                Store.current_playback.type = "movie"
            elif stub == "Video":
                Store.current_playback.type = "video"
            else:
                Store.current_playback.type = "song"

            # DETAILS
            Store.current_playback.year = int(properties.get(f'{stub}Player.Year')) if properties.get(f'{stub}Player.Year') else None
            Store.current_playback.showtitle = properties.get('VideoPlayer.TVShowTitle')
            Store.current_playback.season = int(properties.get('VideoPlayer.Season')) if properties.get('VideoPlayer.Season') else None
            Store.current_playback.episode = int(properties.get('VideoPlayer.Episode')) if properties.get('VideoPlayer.Episode') else None
            Store.current_playback.channelname = properties.get('VideoPlayer.ChannelName')
            Store.current_playback.channelnumberlabel = properties.get('VideoPlayer.ChannelNumberLabel')
            Store.current_playback.channelgroup = properties.get('VideoPlayer.ChannelGroup')
            Store.current_playback.album = properties.get('MusicPlayer.Album')
            Store.current_playback.artist = properties.get('MusicPlayer.Artist')
            Store.current_playback.tracknumber = int(properties.get('MusicPlayer.TrackNumber')) if properties.get('MusicPlayer.TrackNumber') else None

    # @TODO - consider NOT recording playbacks that are fully watched?
    # More than changing this is needed though, as people rarely un things out right to the end, credits etc, so would need
    # to retrieve watched status somehow...
    def onPlayBackEnded(self):  # video ended by simply running out (i.e. user didn't stop it)
        self.onPlaybackFinished()

    def onPlayBackStopped(self):  # user stopped video
        self.onPlaybackFinished()

    @staticmethod
    def onPlaybackFinished():
        """
        Playback has finished, so update our Switchback List
        """
        Logger.debug("onPlaybackFinished with Store.current_playback:")

        if not Store.current_playback or not Store.current_playback.file:
            Logger.error("No current playback details available...not recording this playback")
            return

        Logger.debug(Store.current_playback)

        switchback_playback = HOME_WINDOW.getProperty('Switchback')
        HOME_WINDOW.clearProperty('Switchback')
        if switchback_playback == 'true':
            if Store.current_playback.type == "episode":
                Logger.debug("Force browsing to tvshow/season/ of just finished playback")
                command = json.dumps({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "GUI.ActivateWindow",
                        "params": {
                                "window": "videos",
                                # DBID is used here, not the expected TvShowDBID as I can't seem to get that infolabel set for a Switchback playback??
                                # See switchback_plugin.py - 'dbid': playback.dbid if playback.type != 'episode' else playback.tvshowdbid,
                                "parameters": [f'videodb://tvshows/titles/{Store.current_playback.dbid}/{Store.current_playback.season}'],
                        }
                })
                send_kodi_json(f'Browse to episode of {Store.current_playback.showtitle}', command)
            # @TODO - is is possible to force Kodi to browse to a particular movie?
            # (i.e. a particular movie focussed within the movies list)
            # elif Store.current_playback.type == "movie":
            #     Logger.debug("Force browsing to movie of just finished playback")
            #     command = json.dumps({
            #             "jsonrpc": "2.0",
            #             "id": 1,
            #             "method": "GUI.ActivateWindow",
            #             "params": {
            #                     "window": "videos",
            #                     "parameters": [f'videodb://movies/titles/', 'return'],
            #             }
            #     })
            #     send_kodi_json(f'Browse to movie {Store.current_playback.title}', command)

        Logger.debug(Store.switchback_list)

        # This approach keeps all the details from the original playback
        # (in case they don't make it through when the repeat playback from the Switchback list occurs - as sometimes seems to be the case)
        playback_to_remove = None
        for previous_playback in Store.switchback_list:
            if previous_playback.file == Store.current_playback.file:
                playback_to_remove = previous_playback
                break

        if playback_to_remove:
            Store.switchback_list.remove(playback_to_remove)
            # Update with the current playback times
            playback_to_remove.resumetime = Store.current_playback.resumetime
            playback_to_remove.totaltime = Store.current_playback.totaltime
            Store.switchback_list.insert(0, playback_to_remove)
        else:
            Store.switchback_list.insert(0, Store.current_playback)

        Logger.debug(Store.switchback_list)

        # Trim the list to the max length
        Store.switchback_list = Store.switchback_list[0:Store.maximum_list_length]

        # Finally, Save the playback list to file
        Store.save_switchback_list()


