import os

import xbmcvfs

from bossanova808.constants import HOME_WINDOW, PROFILE, ADDON
from bossanova808.logger import Logger
from bossanova808.utilities import get_kodi_setting, set_property, clear_property
from resources.lib.playback import PlaybackList


class Store:
    """
    Helper class to read in and store the addon settings, and to provide a general centralised store
    Create one with: Store()
    """
    # Static class variables, referred to elsewhere by Store.whatever
    # https://docs.python.org/3/faq/programming.html#how-do-i-create-static-class-data-and-static-class-methods
    kodi_event_monitor = None
    kodi_player = None
    # Holds our playlist of things played back, in first is the latest order
    switchback = None
    # When something is being played back, store the details
    current_playback = None
    # Playbacks are of these possible types
    kodi_video_types = ["movie", "tvshow", "episode", "musicvideo", "video", "file"]
    kodi_music_types = ["song", "album"]
    # Addon settings
    save_across_sessions = ADDON.getSettingBool('save_across_sessions')
    maximum_list_length = ADDON.getSettingInt('maximum_list_length')
    enable_context_menu = ADDON.getSettingBool('enable_context_menu')
    episode_force_browse = ADDON.getSettingBool('episode_force_browse')
    remove_watched_playbacks = ADDON.getSettingBool('remove_watched_playbacks')

    # GUI Settings - to work out how to force browse to a show after a switchback initiated playback
    flatten_tvshows = None

    def __init__(self):
        """
        Load in the addon settings and do basic initialisation stuff
        :return:
        """
        Store.load_config_from_settings()
        Store.load_config_from_kodi_settings()
        Store.switchback = PlaybackList([], xbmcvfs.translatePath(os.path.join(PROFILE, "switchback.json")), Store.remove_watched_playbacks)
        Store.switchback.load_or_init()
        Store.update_switchback_context_menu()


    @staticmethod
    def load_config_from_settings():
        """
        Load in the addon settings, at start or reload them if they have been changed
        :return:
        """
        Logger.info("Loading configuration")
        Store.maximum_list_length = ADDON.getSettingInt('maximum_list_length')
        Logger.info(f"Maximum Switchback list length is: {Store.maximum_list_length}")
        Store.save_across_sessions = ADDON.getSettingBool('save_across_sessions')
        Logger.info(f"Save across sessions is: {Store.save_across_sessions}")
        Store.enable_context_menu = ADDON.getSettingBool('enable_context_menu')
        Logger.info(f"Enable context menu is: {Store.enable_context_menu}")
        Store.remove_watched_playbacks = ADDON.getSettingBool('remove_watched_playbacks')
        Logger.info(f"Remove watched playbacks is: {Store.remove_watched_playbacks}")
        Store.episode_force_browse = ADDON.getSettingBool('episode_force_browse')
        Logger.info(f"Episode force browse is: {Store.episode_force_browse}")

    @staticmethod
    def load_config_from_kodi_settings():
        # Note: this is an int, not a bool — 0 = Never, 1 = 'If only one season', 2 = Always
        Store.flatten_tvshows = int(get_kodi_setting('videolibrary.flattentvshows'))
        Logger.info(f"Flatten TV Shows is: {Store.flatten_tvshows}")

    @staticmethod
    def update_switchback_context_menu():
        if Store.enable_context_menu:
            Logger.debug(f"Updating Home Window Properties for context menu")
            Logger.debug("Switchback list is:", Store.switchback.list)
            set_property(HOME_WINDOW, 'Switchback_List_Length', str(len(Store.switchback.list)))
            if len(Store.switchback.list) == 1:
                set_property(HOME_WINDOW, 'Switchback_Item', Store.switchback.list[0].pluginlabel)
            elif len(Store.switchback.list) > 1:
                set_property(HOME_WINDOW, 'Switchback_Item', Store.switchback.list[1].pluginlabel)
            else:
                clear_property(HOME_WINDOW, 'Switchback_Item')

    @staticmethod
    def update_home_window_switchback_property(path: str):
        Logger.debug(f"Updating Home Window Properties for playback, path: {path}")
        set_property(HOME_WINDOW, 'Switchback', path)
