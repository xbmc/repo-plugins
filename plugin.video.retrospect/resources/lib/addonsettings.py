# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import io
import uuid
import shutil
import threading

import xbmc

from resources.lib.logger import Logger                               # this has not further references
from resources.lib.retroconfig import Config                          # this has not further references
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper   # Only has Logger as reference
from resources.lib.settings import localsettings, kodisettings, settingsstore

# Theoretically we could add a remote settings store too!
KODI = "kodi"
LOCAL = "local"


class AddonSettings(object):
    """ Static Class for retrieving Kodi Addon settings """

    # these are static properties that store the settings. Creating them each time is causing major slow-down
    __user_agent = None
    __kodi_version = None
    __kodi_version_int = 0
    __kodi_debug_log = None

    __USER_AGENT_SETTING = "user_agent"
    __MD5_HASH_VALUE = "md_hash_value"
    __CLIENT_ID = "client_id"

    #region Setting-stores properties and initialization
    __setting_stores = {}
    __settings_lock = threading.Lock()

    __language_strings = {}
    __language_current = None

    KodiPiers = 22
    KodiOmega = 21
    KodiNexus = 20
    KodiMatrix = 19
    KodiLeia = 18
    KodiKrypton = 17

    @staticmethod
    def store(store_location):
        """ Returns the Singleton store object for the given type

        :param str|unicode store_location: Either the Kodi (KODI) store or in the Retrospect (LOCAL) store

        :return: An instance of the setting store
        :rtype:  settingsstore.SettingsStore

        """

        store = AddonSettings.__setting_stores.get(store_location, None)
        if store is not None:
            return store

        with AddonSettings.__settings_lock:
            # Just a double check in case there was a race condition??
            store = AddonSettings.__setting_stores.get(store_location, None)
            if store is not None:
                return store

            if store_location == KODI:
                store = kodisettings.KodiSettings(Logger.instance())
            elif store_location == LOCAL:
                store = localsettings.LocalSettings(Config.profileDir, Logger.instance())
            else:
                raise IndexError("Cannot find Setting store type: {0}".format(store_location))

            AddonSettings.__setting_stores[store_location] = store
            return store

    @staticmethod
    def __refresh(store_location):
        """ Removes the instance of the settings store causing a reload.

        :param str|unicode store_location:  Either the Kodi (KODI) store or in the
                                            Retrospect (LOCAL) store

        """

        store = AddonSettings.__setting_stores.pop(store_location, None)
        if store is None:
            return

        # this really only works if no reference to the <store> object is kept somewhere.
        del store

    def __init__(self):
        """Initialisation of the AddonSettings class. """

        raise NotImplementedError("Static class cannot be constructed")

    @staticmethod
    def clear_cached_addon_settings_object():
        """ Clears the cached add-on settings. This will force a reload for the next INSTANCE
        of an AddonSettings class. """

        for store_type in (KODI, LOCAL):
            store = AddonSettings.__setting_stores.pop(store_type, None)
            if store:
                del store

    #endregion

    #region Kodi version stuff
    @staticmethod
    def get_kodi_version():
        """ Retrieves the Kodi version we are running on.

        :return: the full string of the Kodi version. E.g.: 16.1 Git:20160424-c327c53
        :rtype: str

        """

        if AddonSettings.__kodi_version is None:
            AddonSettings.__kodi_version = xbmc.getInfoLabel("system.buildversion")

        return AddonSettings.__kodi_version

    @staticmethod
    def get_kodi_major_version():
        """ Retrieves the Kodi major version we are running on.

        :return: The major version of Kodi
        :rtype: int

        """

        if AddonSettings.__kodi_version_int == 0:
            AddonSettings.__kodi_version_int = int(AddonSettings.get_kodi_version().split(".")[0])

        return AddonSettings.__kodi_version_int

    @staticmethod
    def is_min_version(min_value):
        """ Checks whether the version of Kodi is higher or equal to the given version.

        :param min_value: the minimum Kodi version
        :type min_value: int

        :return: True if higher or equal, False otherwise.
        :rtype: bool

        """

        return AddonSettings.get_kodi_major_version() >= min_value
    #endregion

    #region Generic Access to Settings from other modules
    @staticmethod
    def get_setting(setting_id, store=KODI):
        """Returns the setting for the requested ID, from the cached settings.

        Arguments:
        settingId - string - the ID of the settings

        Returns:

        :type setting_id:   str
        :param setting_id:  The ID of the setting to retrieve.

        :type store:        str
        :param store:       Whether to retrieve it from the Kodi (KODI) or in the Retrospect (LOCAL) store

        :rtype:             str
        :return:            The configured Kodi add-on values for that <id>.

        """

        value = AddonSettings.store(store).get_setting(setting_id)
        return value

    @staticmethod
    def set_setting(setting_id, value, store=KODI):
        """Sets the value for the setting with requested ID, from the cached settings.

        :type setting_id:  str
        :param setting_id: The ID of the setting to store.

        :type value:       str
        :param value:      The value to store.

        :type store:       str
        :param store:      Whether to store in Kodi (KODI) or in the Retrospect (LOCAL) store

        :return: The configured Kodi add-on values for that <id>.
        :rtype:  str

        """

        AddonSettings.store(store).set_setting(setting_id, value)
        return value

    @staticmethod
    def get_channel_setting(channel, setting_id, value_for_none=None, store=KODI):
        """ Retrieves channel settings for the given channel

        :param channel:       The channel object to get the channels for

        :type setting_id:       str
        :param setting_id:      The ID of the setting to retrieve.

        :type value_for_none:   str
        :param value_for_none:  What value should we interpret as None?

        :type store:            str
        :param store:           Whether to retrieve it from the Kodi (KODI) or in the Retrospect
                                (LOCAL) store.

        :return: the setting with the given <id> for within the <channel>
        :rtype: str

        """

        return AddonSettings.store(store).get_setting(setting_id, channel, value_for_none)

    @staticmethod
    def set_channel_setting(channel, setting_id, value, store=KODI):
        """ Retrieves channel settings for the given channel

        :param channel:         The channel object to get the channels for
        :param str setting_id:  The ID of the setting to store.
        :param str value:      The value to store.
        :param str store:       Whether to store in Kodi (KODI) or in the Retrospect (LOCAL) store

        :return: The configured Kodi add-on values for that <id>.
        :rtype:  str

        """

        return AddonSettings.store(store).set_setting(setting_id, value, channel)
    #endregion

    #region Showing and hiding of items
    @staticmethod
    def show_cloaked_items():
        """ Should we show cloaked items?

        :return: Indication whether or not to show cloaked items.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_cloaked_items")

    @staticmethod
    def show_categories():
        """ Returns an indication whether channels should be nested under categories or not.

        :rtype: bool
        :return: Indication if we should show categories.

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_categories")

    @staticmethod
    def show_show_favourites_in_channel_list():
        """ Returns an indication whether an "All Favourites" item is shown in the main channel list.

        :rtype: bool
        :return: Indication if we should show "All Favourites"

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_favourites", default=False)

    @staticmethod
    def show_drm_paid_warning():
        """ Should we show a DRM warning on DRM protected (^) items?

        :return: Yes or No.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_drm_warning")

    @staticmethod
    def hide_fanart():
        """ Should we hide Fanart?

        :return: Yes or No
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_fanart")

    @staticmethod
    def use_thumbs_as_fanart():
        """ Should we show thumbs if fanart is missing?

        :rtype: bool
        :return: indicator if we should show thumbs as fanart.

        """

        return AddonSettings.store(KODI).get_boolean_setting("use_thumbs_as_fanart", False)

    @staticmethod
    def hide_drm_items():
        """ Returns whether or not to hide DRM protected items.

        :return: True/False
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_drm")

    @staticmethod
    def hide_premium_items():
        """ Returns whether or not to hide Premium/Paid items.

        :return: True/False
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_premium")

    @staticmethod
    def hide_restricted_folders():
        """ Should we hide restricted folders?

        :return: Indication if the restricted folders should be hidden
        :rtype: bool

        """

        values = [True, False]
        value = AddonSettings.store(KODI).get_integer_setting("hide_types", default=0)
        return values[value]

    @staticmethod
    def hide_first_time_messages():
        """ Indication if we should show or hide the channel initialization messages

        :return: returns true if the first time messages should be shown.
        :rtype: bool

        """

        return AddonSettings.store(KODI).\
            get_boolean_setting("hide_first_time_message", default=False)
    #endregion

    #region Geo and region stuff
    @staticmethod
    def hide_geo_locked_items_for_location(channel_region, value_only=False):
        """ Returns the config value that indicates what if we should hide items that are geographically
        locked to the region of the channel (indicated by the channel language).

        :param str|None channel_region:  the channel region (actually the channel language)
        :param bool value_only:     if set to True, it will return the settings value

        :return: Indication if Retrospect should hide the items that are geo-locked to the given
                 reason.

        """

        # This list is taken from the settings_templates.xml: geo_region
        # 30074    |30306|30309|30308|30307|30303|30304|30301|30305|30302|30310
        # Disabled |be   |de   |ee   |en-gb|lt   |lv   |nl   |no   |se   |dk
        values = [None, "be", "de", "ee", "en-gb", "lt", "lv", "nl", "no", "se", "dk"]
        value_index = AddonSettings.store(KODI).get_integer_setting("geo_region", default=0)
        current_geographical_region = values[value_index]

        if value_only:
            return current_geographical_region

        # if no geo region is selected, always show everything.
        if current_geographical_region is None:
            return False

        # only hide if the regions don't match
        return not current_geographical_region == channel_region
    #endregion

    #region Language caching
    @staticmethod
    def get_gui_language():
        """ Returns the two character ISO 639-1 value for the Kodi language

        :return: Two character ISO 639-1 value
        :rtype: str

        """

        if AddonSettings.__language_current is None:
            AddonSettings.__language_current = xbmc.getLanguage(xbmc.ISO_639_1, region=False)
            Logger.info("Setting GUI language to: %s", AddonSettings.__language_current)

        return AddonSettings.__language_current

    @staticmethod
    def get_localized_string(string_id):
        """ returns a localized string for this id

        Arguments:
        :param int string_id: The ID for the string

        :return: the localized string for this ID.
        :rtype: str

        """

        translation = AddonSettings.__language_strings.get(string_id, None)
        if translation is None:
            translation = AddonSettings.store(KODI).get_localized_string(string_id)
            AddonSettings.__language_strings[string_id] = translation

        return translation
    #endregion

    @staticmethod
    def get_current_addon_xml_md5():
        """ Retrieves the current addons.xml.md5 content that was cached in the settings.

        :return: the current addons.xml.md5 content
        :rtype: str

        """

        return AddonSettings.store(LOCAL).get_setting(AddonSettings.__MD5_HASH_VALUE)

    @staticmethod
    def update_current_addon_xml_md5(hash_value):
        """ Update the local cache with a new addons.xml.md5 hash value

        :param str hash_value: The MD5 Hash value

        """

        AddonSettings.store(LOCAL).set_setting(AddonSettings.__MD5_HASH_VALUE, hash_value)

    @staticmethod
    def get_client_id():
        """ Retrieves the GUID for this specific client. If no GUID exists, it will generate a new
        one.

        :return: The Client ID GUID
        :rtype: str

        """

        client_id = AddonSettings.store(LOCAL).get_setting(AddonSettings.__CLIENT_ID)
        if not client_id:
            client_id = AddonSettings.store(KODI).get_setting(AddonSettings.__CLIENT_ID)
            if client_id:
                Logger.info("Moved ClientID to local storage")
                AddonSettings.store(LOCAL).set_setting(AddonSettings.__CLIENT_ID, client_id)
                return client_id

            client_id = str(uuid.uuid1())
            Logger.debug("Generating new ClientID: %s", client_id)
            AddonSettings.store(LOCAL).set_setting(AddonSettings.__CLIENT_ID, client_id)
        return client_id

    @staticmethod
    def get_adaptive_mode(channel):
        """ Get the channel behaviour for the InputStream Adaptive for the channel.

        :param channel:     The channel to set the bitrate for

        :rtype: str
        :return: The bitrate for the channel as a string!
        """
        return AddonSettings.store(LOCAL).get_setting("adaptive_mode",
                                                      channel,
                                                      default=None)

    @staticmethod
    def set_adaptive_mode(channel, mode):
        """ Set the maximum channel bitrate

        :param channel:         The channel to set the bitrate for
        :param bool|None mode:  The configured mode. None = respect the Retrospect settings.

        """
        AddonSettings.store(LOCAL).set_setting("adaptive_mode", mode, channel)

    @staticmethod
    def use_adaptive_stream_add_on(with_encryption=False, ignore_add_on_config=False, channel=None):
        """ Should we use the Adaptive Stream add-on?

        :param bool with_encryption:        do we need to decrypte script.
        :param bool ignore_add_on_config:   ignore the Retrospect setting, use the InputStream
                                            Adaptive add-on and only validate other criteria.
        :param ChannelInfo channel:         If specified, the channel specific configuration is
                                            considered.

        :return: Indication whether the Adaptive Stream add-on is available.
        :rtype: bool

                          | Channel settings
                          |  None      False     True
        ------------------+----------------------------
        Retrospect  True  |  True     <False>    True
                   False  |  False     False    <True>

        So there are 2 exceptions to the normal conditions, indicated with <>

        """

        # check the Retrospect add-on setting perhaps?
        use_add_on = \
            AddonSettings.store(KODI).get_boolean_setting("use_adaptive_addon", default=True)

        channel_setting = None
        if channel is not None and channel.adaptiveAddonSelectable:
            channel_setting = AddonSettings.get_adaptive_mode(channel)

        # if the channel disables it we don't have an encrypted stream, then don't use it.
        if channel_setting is False:
            if not with_encryption:
                Logger.info("Adaptive Stream add-on disabled from Channel settings")
                return False
            else:
                Logger.info("Adaptive Stream add-on cannot be disabled from Channel settings for encrypted streams")

        if ignore_add_on_config:
            Logger.debug(
                "Ignoring Retrospect setting use_adaptive_addon=%s and using it anyways.", use_add_on)

        elif not use_add_on:
            # if the add-on was disabled, don't use it, unless specified by the channel setting
            # check the channel setting, if it set to True, we should obey that and not return False
            if channel_setting is True:
                Logger.info("Adaptive Stream add-on is disabled from Retrospect settings but enabled for channel")
            else:
                Logger.info("Adaptive Stream add-on disabled from Retrospect settings")
                return False

        # we should use it, so if we can't find it, it is not so OK.
        adaptive_add_on_id = "inputstream.adaptive"
        adaptive_add_on_installed = \
            xbmc.getCondVisibility('System.HasAddon("{0}")'.format(adaptive_add_on_id)) == 1

        if not adaptive_add_on_installed:
            Logger.warning("Adaptive Stream add-on '%s' is not installed/enabled.", adaptive_add_on_id)
            return False

        kodi_leia = AddonSettings.is_min_version(AddonSettings.KodiLeia)
        Logger.info("Adaptive Stream add-on '%s' %s decryption support was found.",
                    adaptive_add_on_id, "with" if kodi_leia else "without")

        if with_encryption:
            return kodi_leia

        return adaptive_add_on_installed

    @staticmethod
    def use_up_next():
        """ Should we use the Up Next service?

        :rtype: bool
        :return: To use Up Next or not.
        """

        if AddonSettings.is_min_version(AddonSettings.KodiMatrix):
            installed = xbmc.getCondVisibility('System.HasAddon(service.upnext) + System.AddonIsEnabled(service.upnext)') == 1
        else:
            installed = xbmc.getCondVisibility('System.HasAddon(service.upnext)') == 1

        use = AddonSettings.store(KODI).get_boolean_setting("use_up_next")
        Logger.debug("Up Next: installed=%s, use=%s", installed, use)
        return installed and use

    @staticmethod
    def update_user_agent():
        """ Creates a user agent for this instance of XOT

        this is a very slow action on lower end systems (ATV and rPi) so we minimize the number of runs

        :return: Nothing
        :rtype: None

        Actual:
        User-Agent: Kodi/16.1 (Windows NT 10.0; WOW64) App_Bitness/32 Version/16.1-Git:20160424-c327c53
        Retro:
        User-Agent: Kodi/16.1 Git:20160424-c327c53 (Windows 10;AMD64; http://kodi.tv)

        Firefox:
        User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0
        """

        # there are slow imports, so only do them here
        import platform
        from resources.lib.envcontroller import EnvController

        # noinspection PyNoneFunctionAssignment
        version = AddonSettings.get_kodi_version()
        Logger.debug("Found Kodi version: %s", version)
        git = ""
        try:
            # noinspection PyNoneFunctionAssignment
            if "Git:" in version:
                version, git = version.split("Git:", 1)
            version = version.rstrip()

            # The platform.<method> are not working on rPi and IOS
            # kernel = platform.architecture()
            # Logger.Trace(kernel)
            # machine = platform.machine()
            # Logger.Trace(machine)

            uname = platform.uname()
            Logger.trace(uname)
            if git:
                user_agent = "Kodi/%s (%s %s; %s; http://kodi.tv) Version/%s Git:%s" % \
                             (version, uname[0], uname[2], uname[4], version, git)
            else:
                user_agent = "Kodi/%s (%s %s; %s; http://kodi.tv) Version/%s" % \
                             (version, uname[0], uname[2], uname[4], version)
        except:
            Logger.warning("Error setting user agent", exc_info=True)
            current_env = EnvController.get_platform(True)
            # Kodi/14.2 (Windows NT 6.1; WOW64) App_Bitness/32 Version/14.2-Git:20150326-7cc53a9
            user_agent = "Kodi/%s (%s; <unknown>; http://kodi.tv)" % (version, current_env)

        # now we store it
        AddonSettings.store(LOCAL).set_setting(AddonSettings.__USER_AGENT_SETTING, user_agent)
        AddonSettings.__user_agent = user_agent
        Logger.info("User agent set to: %s", user_agent)
        return

    @staticmethod
    def get_notification_level():
        """ Retrieves the level for displaying notifications to the end user:

        0: Information.
        1: Warning.
        2: Error.

        :return: Array with the levels that we are showing to the end user
        :rtype: list[str]

        """
        values = ['info', 'warning', 'error']
        minimum_level = AddonSettings.store(KODI).get_integer_setting("minimum_notification_level")
        return values[minimum_level:]

    @staticmethod
    def get_user_agent():
        """ Retrieves a user agent string for this Kodi instance.

        :return: a user-agent string
        :rtype: str

        """

        if not AddonSettings.__user_agent:
            # load and cache
            user_agent = AddonSettings.store(LOCAL).get_setting(AddonSettings.__USER_AGENT_SETTING)
            AddonSettings.__user_agent = user_agent

            # double check if the version of Kodi is still OK
            if AddonSettings.__user_agent:
                # noinspection PyNoneFunctionAssignment
                version = AddonSettings.get_kodi_version()

                if version not in AddonSettings.__user_agent:
                    old = AddonSettings.__user_agent
                    # a new XBMC version was installed, update the User-agent
                    AddonSettings.update_user_agent()
                    Logger.info("User agent updated due to Kodi version change from\n%s to\n%s",
                                old, AddonSettings.__user_agent)
            else:
                AddonSettings.update_user_agent()
                Logger.info("Set initial User agent version because it was missing.")

        Logger.debug("User agent retrieved from cache: %s", AddonSettings.__user_agent)
        return AddonSettings.__user_agent

    @staticmethod
    def cache_http_responses():
        """ Returns True if the HTTP responses need to be cached

        :return: Indication if HTTP(s) requests should be cached or not.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("http_cache", default=True)

    @staticmethod
    def ignore_ssl_errors():
        """ Returns True if SSL errors should be ignored from Python

        :return: Indication if SSL certificate errors should be ignored
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("ignore_ssl_errors", default=False)

    @staticmethod
    def get_max_stream_bitrate(channel=None):
        """Returns the maximum bitrate (kbps) for streams specified by the user

        :param Channel|ChannelInfo channel:     The channel to use for channel specific bitrates.

        :rtype: int
        :return: The maximum stream bitrate. If channel was provided, it will return the configured
                  value for that channel. It will return 0 if not limit should be used.

        """

        setting = "Retrospect"
        if channel is not None:
            setting = AddonSettings.get_max_channel_bitrate(channel)

        if setting == "Retrospect":
            setting = AddonSettings.store(KODI).get_setting("stream_bitrate_limit", 0)
            Logger.debug("Using the Retrospect Default Bitrate: %s", setting)
        else:
            Logger.debug("Using the Channel Specific Bitrate: %s", setting)
        return int(setting or 0)

    @staticmethod
    def get_max_channel_bitrate(channel):
        """ Get the maximum channel bitrate configured for the channel. Keep in mind that if
        'Retrospect' was selected, the actual maximum stream bitrate is set by the overall settings.

        :param channel:     The channel to set the bitrate for

        :rtype: str
        :return: The bitrate for the channel as a string!
        """
        return AddonSettings.store(LOCAL).get_setting("bitrate", channel, default="Retrospect")

    @staticmethod
    def set_max_channel_bitrate(channel, bitrate):
        """ Set the maximum channel bitrate

        :param channel:         The channel to set the bitrate for
        :param str bitrate:     the maximum bitrate value (it's a string because it could
                                be "Retrospect"

        """

        AddonSettings.store(LOCAL).set_setting("bitrate", bitrate, channel=channel)

    @staticmethod
    def get_folder_prefix():
        """ returns the folder prefix

        :rtype: str
        :return: A prefix to show in front of folders.

        """

        setting = AddonSettings.store(KODI).get_setting("folder_prefix", default="")
        return setting

    @staticmethod
    def mix_folders_and_videos():
        """ Should we treat Folders and Videos alike

        :rtype: bool
        :return: Indication of folders and videos should be mixed while sorting (True) or sort them
                 separately.

        """

        return AddonSettings.store(KODI).get_boolean_setting("folders_as_video", default=False)

    @staticmethod
    def get_empty_list_behaviour():
        """ Retrieves how to behave of empty result lists are found.

        0 = Error
        1 = Empty List
        2 = Dummy

        :return: returns the behaviour for empty lists (1,2,3):
        :rtype: int

        """

        setting = AddonSettings.store(KODI).\
            get_integer_setting("empty_folder", default=2)

        if setting == 0:
            return "error"
        elif setting == 1:
            return "empty"
        else:
            return "dummy"

    @staticmethod
    def show_subtitles():
        """Returns whether to show subtitles or not

        :return: Indication if Kodi should how subs or not
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_subtitles", default=True)

    @staticmethod
    def get_list_limit():
        """ Retrieves the limit for a list before it is grouped alphabetically.

        :return: an integer with the limit
        :rtype: int

        """

        limit = AddonSettings.store(KODI).get_integer_setting("list_limit", default=5)
        return [-1, 10, 50, 75, 100, 150, 200, 1000][limit]

    @staticmethod
    def get_log_level():
        """ Returns the log level to be used:

        - 00: Trace
        - 10: Debug
        - 20: Info
        - 30: Warning
        - 40: Error
        - 50: Critical

        :return: The requested log level
        :rtype: int

        """

        level = AddonSettings.store(KODI).get_integer_setting("log_level", default=2)

        # Check if Kodi has debugging enabled, but only if Retrospect does not.
        if level > 1:
            # Did we already call the JSON RPC this run?
            if AddonSettings.__kodi_debug_log is None:
                rpc_call = {
                    "jsonrpc": "2.0", "method": "Settings.GetSettingValue",
                    "params": {
                        "setting": "debug.showloginfo"
                    }, "id": 1
                }

                try:
                    rpc_result = json.loads(xbmc.executeJSONRPC(json.dumps(rpc_call)))
                    kodi_debug_logging = rpc_result.get("result", {}).get("value", False)
                    AddonSettings.__kodi_debug_log = kodi_debug_logging
                except:
                    Logger.error("Error on logging RCP call", exc_info=True)
                    kodi_debug_logging = False

            else:
                # Retrieve the value that was previously retrieved.
                kodi_debug_logging = AddonSettings.__kodi_debug_log

            if kodi_debug_logging:
                Logger.warning("Debug logging enabled due to Kodi GUI settings.")
                return 10

        # noinspection PyTypeChecker
        return int(level) * 10

    @staticmethod
    def set_channel_visibility(channel, visible):
        """ Sets the visibility for the give channel.

        :param channel: the ChannelInfo object
        :param bool visible: indication for visibility

        """

        AddonSettings.store(LOCAL).set_setting("visible", visible, channel)

    @staticmethod
    def get_channel_visibility(channel):
        """ Checks if the channel should be shown

        :param channel: The channel to check.

        :rtype: bool
        :return: returns True if the channel should be visible.

        """

        return AddonSettings.store(LOCAL).get_boolean_setting("visible", channel, default=True)

    @staticmethod
    def show_channel_settings(channel):
        """ Show the add-on settings and pre-selects the channel settings tab with the correct channel
        selected.

        :param channel: The channel to display settings for.
        """

        channel_name = channel.safe_name

        # remove some HTML chars
        channel_name = HtmlEntityHelper.convert_html_entities(channel_name)
        Logger.debug("Showing channel settings for channel: %s (%s)", channel_name, channel.channelName)

        # Set the channel to be the preselected one
        AddonSettings.store(KODI).set_setting("config_channel", channel_name)

        # show settings and focus on the channel settings tab
        if AddonSettings.is_min_version(AddonSettings.KodiLeia):
            return AddonSettings.show_settings(-98)
        else:
            return AddonSettings.show_settings(102)

    @staticmethod
    def show_settings(tab_id=None, setting_id=None):
        """ Shows the settings dialog

        :param int|str tab_id:   what tab should have focus in the settings?
        :param str setting_id:   what control should have focus in the settings tab?

        """

        if tab_id is None:
            # shows the settings and blocks:
            AddonSettings.store(KODI).open_settings()  # this will open settings window
            # reload the cache because stuff might have changed

            Logger.info("Clearing Settings cache because settings dialog was shown.")
            AddonSettings.__refresh(KODI)
        else:
            # show settings and focus on a tab
            xbmc.executebuiltin('Addon.OpenSettings(%s)' % (Config.addonId,))

            if tab_id:
                # the 100 range are the tabs
                # the 200 range are the controls in a tab
                xbmc.executebuiltin('SetFocus(%i)' % int(tab_id))
                if setting_id:
                    xbmc.executebuiltin('SetFocus(%s)' % int(setting_id))

            Logger.info("Settings shown with focus on %s-%s", tab_id, setting_id or "<none>")
        return

    @staticmethod
    def show_channel_with_language(language_code):
        """ Checks if the channel with a certain languageCode should be loaded. Possible language
        code are:

         * nl    - Dutch
         * se    - Swedish
         * lt    - Lithuanian
         * lv    - Latvian
         * be    - Belgium
         * en-gb - British
         * ee    - Estonian
         * no    - Norwegian
         * dk    - Danish
         * None  - Other languages

        :param None|str|unicode language_code:  one of the language codes that are listed.

        :rtype: bool
        :return: True if the channels should be shown. If the lookup does not match
                 a NotImplementedError is thrown.

        """

        (settings_id, settings_label) = AddonSettings.__get_language_settings_id_and_label(language_code)
        return AddonSettings.store(KODI).get_boolean_setting(settings_id, default=True)

    #noinspection PyUnresolvedReferences
    @staticmethod
    def update_add_on_settings_with_channels(channels, config):
        """ Updates the settings.xml to include all the channels

        :param list[any] channels:  The channels to add to the settings.xml
        :param type[Config] config: The configuration object

        """

        # sort the channels
        channels.sort(key=lambda c: c.sort_key)

        # Then we read the original file
        filename_template = os.path.join(config.rootDir, "resources", "data", "settings_template.xml")
        if not os.path.isfile(filename_template):
            Logger.debug("No template present in '%s'. Skipping generation.", filename_template)
            return

        # noinspection PyArgumentEqualDefault
        with io.open(filename_template, "r", encoding="utf-8") as fp:
            contents = fp.read()

        new_contents = AddonSettings.__update_add_on_settings_with_country_settings(contents, channels)
        new_contents, settings_offset_for_visibility, channels_with_settings = \
            AddonSettings.__update_add_on_settings_with_channel_settings(new_contents, channels)

        new_contents = AddonSettings.__update_add_on_settings_with_channel_selection(
            new_contents, channels_with_settings)

        # Now fill the templates, we only import here due to performance penalties of the
        # large number of imports.
        from resources.lib.helpers.templatehelper import TemplateHelper
        th = TemplateHelper(Logger.instance(), template=new_contents)
        new_contents = th.transform()

        # Finally we insert the new XML into the old one
        filename = os.path.join(config.rootDir, "resources", "settings.xml")
        filename_temp = os.path.join(config.rootDir, "resources", "settings.tmp.xml")
        try:
            # Backup the user profile settings.xml because sometimes it gets reset. Because in some
            # concurrency situations, Kodi might decide to think we have no settings and just
            # erase all user settings.
            user_settings = os.path.join(Config.profileDir, "settings.xml")
            user_settings_backup = os.path.join(Config.profileDir, "settings.old.xml")
            Logger.debug("Backing-up user settings: %s", user_settings_backup)
            if os.path.isfile(user_settings):
                if os.path.isfile(user_settings_backup):
                    os.remove(user_settings_backup)
                shutil.copyfile(user_settings, user_settings_backup)
            else:
                Logger.warning("No user settings found at: %s", user_settings)

            # Update the addonsettings.xml by first updating a temp xml file.
            Logger.debug("Creating new settings.xml file: %s", filename_temp)
            Logger.trace(new_contents)
            with io.open(filename_temp, "w+", encoding='utf-8') as fp:
                fp.write(new_contents)

            Logger.debug("Replacing existing settings.xml file: %s", filename)
            if os.path.isfile(filename):
                os.remove(filename)
            shutil.move(filename_temp, filename)

            # restore the user profile settings.xml file when needed
            if os.path.isfile(user_settings) and os.stat(user_settings).st_size != os.stat(user_settings_backup).st_size:
                Logger.critical("User settings.xml was overwritten during setttings update. Restoring from %s", user_settings_backup)
                if os.path.isfile(user_settings):
                    os.remove(user_settings)
                shutil.copyfile(user_settings_backup, user_settings)
        except:
            Logger.error("Something went wrong trying to update the settings.xml", exc_info=True)

            #  clean up time file
            if os.path.isfile(filename_temp):
                os.remove(filename_temp)

            # restore original settings
            with io.open(filename_temp, "w+", encoding='utf-8') as fp:
                fp.write(contents)

            if os.path.isfile(filename):
                os.remove(filename)
            shutil.move(filename_temp, filename)
            return

        Logger.info("Settings.xml updated successfully. Reloading settings.")
        AddonSettings.__refresh(KODI)
        return

    @staticmethod
    def __update_add_on_settings_with_channel_selection(contents, channels):
        """ Adds the settings part that allows the selection of the channel for which the channel settings should
        be displayed.

        :param str  contents: The current settings
        :param list[Any] channels: The available channels

        :return: updated contents
        :rtype: str

        """

        if "<!-- start of active channels -->" not in contents:
            Logger.error("No '<!-- start of active channels -->' found in settings.xml. Stopping updating.")
            return

        # Create new XML
        channel_selection_xml = '        <!-- start of active channels -->\n' \
                                '        <setting id="config_channel" type="select" label="30040" values="'
        channel_safe_names = "|".join([c.safe_name for c in channels])
        channel_selection_xml = "%s%s" % (channel_selection_xml, channel_safe_names)
        channel_selection_xml = '%s" />' % (channel_selection_xml.rstrip("|"),)

        # replace the correct parts
        begin = contents[:contents.find('<!-- start of active channels -->')].strip()
        end = contents[contents.find('<!-- end of active channels -->'):].strip()
        contents = "%s\n%s\n        %s" % (begin, channel_selection_xml, end)
        return contents

    @staticmethod
    def __update_add_on_settings_with_channel_settings(contents, channels):  # NOSONAR
        """ Adds the channel specific settings

        This method first aggregates the settings and then adds them.

        :param str contents: The current settings
        :param list[any] channels: The available channels

        :return: updated contents and the offset in visibility
        :rtype: str

        """

        if "<!-- begin of channel settings -->" not in contents:
            Logger.error("No '<!-- begin of channel settings -->' found in settings.xml. Stopping updating.")
            return

        settings = dict()
        channels_with_settings = []

        # There are 2 settings between the selector list and the channel settings in the settings_template.xml
        setting_offset_for_visibility = 2

        # Let's make sure they are sorted by channel module. So we first go through them all and then create
        # the XML.
        for channel in channels:
            if not channel.settings:
                Logger.debug("Setting not enabled for: %s", channel)
                continue

            if channel.moduleName not in settings:
                settings[channel.moduleName] = []

            # Sort the settings so they are really in the correct order, because this is not guaranteed by the
            # json parser
            channel.settings.sort(key=lambda a: a["order"])
            for channel_settings in channel.settings:
                setting_id = channel_settings["id"]
                setting_value = channel_settings["value"]

                # Filtered in the channelinfo.py
                # if "channels" in channel_settings and channel.guid not in channel_settings["channels"]:
                #     Logger.debug("Setting not enabled for: %s", channel)
                #     continue

                if "{channel_guid}" in setting_value:
                    setting_value = setting_value.replace("{channel_guid}", channel.guid)
                Logger.debug("Adding setting: '%s' with value '%s'", setting_id,
                             setting_value)

                if setting_value.startswith("id="):
                    setting_xml_id = setting_value[4:setting_value.index('"', 4)]
                    setting_xml = "<setting %s visible=\"eq(-{0},%s)\" />" % \
                                  (setting_value, channel.safe_name)
                else:
                    setting_xml_id = "channel_{0}_{1}".format(channel.guid, setting_id)
                    setting_xml = '<setting id="%s" %s visible=\"eq(-{0},%s)\" />' % \
                                  (setting_xml_id, setting_value, channel.safe_name)

                existing_setting_xml_index = [i for i, s in
                                              enumerate(settings[channel.moduleName]) if
                                              setting_xml_id in s]
                if not existing_setting_xml_index:
                    settings[channel.moduleName].append((setting_xml_id, setting_xml))
                else:
                    xml_index = existing_setting_xml_index[0]
                    # we need to OR the visibility
                    setting_tuple = settings[channel.moduleName][xml_index]
                    setting = setting_tuple[1].replace(
                        'visible="', 'visible="eq(-{0},%s)|' % (channel.safe_name,))
                    settings[channel.moduleName][xml_index] = (setting_tuple[0], setting)

            # Add it to channels with settings
            channels_with_settings.append(channel)

        xml_content = '\n        <!-- begin of channel settings -->\n'
        # Sort them to make the result more consistent
        # noinspection PyUnresolvedReferences
        setting_keys = sorted(settings.keys())
        for py_module in setting_keys:
            xml_content = '%s        <!-- %s.py -->\n' % (xml_content, py_module)
            for setting_xml_id, setting in settings[py_module]:
                setting_offset_for_visibility += 1
                xml_content = "%s        %s\n" % (xml_content, setting.format(setting_offset_for_visibility))

        begin = contents[:contents.find('<!-- begin of channel settings -->')].strip()
        end = contents[contents.find('<!-- end of channel settings -->'):]

        Logger.trace("Generated channel settings:\n%s", xml_content)
        contents = "%s\n%s\n        %s" % (begin, xml_content.rstrip(), end)
        return contents, setting_offset_for_visibility, channels_with_settings

    @staticmethod
    def __update_add_on_settings_with_country_settings(contents, channels):
        """ Adds the channel showing/hiding to the settings.xml

        :param str|unicode contents:    The current settings
        :param list[any] channels:      The available channels

        :return: updated contents and the offset in visibility
        :rtype: str

        """

        if "<!-- start of channel selection -->" not in contents:
            Logger.error("No '<!-- start of channel selection -->' found in settings.xml. Stopping updating.")
            return

        # First we create a new bit of settings file.
        channel_xml = '        <!-- start of channel selection -->\n'

        # the distinct list of languages from the channels
        languages = [c.language for c in channels]
        languages = list(set(languages))
        languages.sort(key=lambda l: l or "")
        Logger.debug("Found languages: %s", languages)

        # get the labels and setting identifiers for those languages
        language_lookup = dict()
        for language in languages:
            language_lookup[language] = AddonSettings.__get_language_settings_id_and_label(language)

        language_lookup_sorted_keys = sorted(language_lookup.keys(), key=lambda k: k or "")

        for language in language_lookup_sorted_keys:
            channel_xml = '%s        <setting id="%s" type="bool" label="%s" subsetting="false" default="true" />\n' \
                         % (channel_xml, language_lookup[language][0], language_lookup[language][1])

        begin = contents[:contents.find('<!-- start of channel selection -->')].strip()
        end = contents[contents.find('<!-- end of channel selection -->'):].strip()
        contents = "%s\n    \n%s        %s" % (begin, channel_xml, end)
        return contents

    @staticmethod
    def __get_language_settings_id_and_label(language_code):
        """ returns the settings xml part for this language

        :param str language_code: The language string

        :return: A tuple with the label and the settingsId.
        :rtype: tuple[str,int]

        """

        if language_code == "nl":
            return "show_dutch", 30301
        elif language_code == "fi":
            return "show_finnish", 30302
        elif language_code == "se":
            return "show_swedish", 30302
        elif language_code == "lt":
            return "show_lithuanian", 30303
        elif language_code == "lv":
            return "show_latvian", 30304
        elif language_code == "en-gb":
            return "show_engb", 30307
        elif language_code == "no":
            return "show_norwegian", 30305
        elif language_code == "be":
            return "show_belgium", 30306
        elif language_code == "ee":
            return "show_estonia", 30308
        elif language_code == "dk":
            return "show_danish", 30310
        elif language_code == "de":
            return "show_german", 30309
        elif language_code is None:
            return "show_other", 30300
        else:
            raise NotImplementedError("Language code not supported: '%s'" % (language_code,))

    @staticmethod
    def print_setting_values():
        """Prints the settings"""

        pattern = "%s\n%s: %s"
        value = "%s: %s" % ("ClientId", AddonSettings.get_client_id())
        value = pattern % (value, "MaxStreamBitrate", AddonSettings.get_max_stream_bitrate())
        value = pattern % (value, "Show_subtitles", AddonSettings.show_subtitles())
        value = pattern % (value, "Cache_http_responses", AddonSettings.cache_http_responses())
        value = pattern % (value, "Folder Prefix", "'%s'" % AddonSettings.get_folder_prefix())
        value = pattern % (value, "Mix Folders & Videos", AddonSettings.mix_folders_and_videos())
        value = pattern % (value, "Empty List Behaviour", AddonSettings.get_empty_list_behaviour())
        value = pattern % (value, "ListLimit", AddonSettings.get_list_limit())
        value = pattern % (value, "Loglevel", AddonSettings.get_log_level())
        value = pattern % (value, "Ignore SSL Errors", AddonSettings.ignore_ssl_errors())
        value = pattern % (value, "Geo Location", AddonSettings.hide_geo_locked_items_for_location(None, value_only=True))
        value = pattern % (value, "Filter Folders", AddonSettings.hide_restricted_folders())
        value = pattern % (value, "DRM/Paid Warning", AddonSettings.show_drm_paid_warning())
        value = pattern % (value, "Hide DRM Items", AddonSettings.hide_drm_items())
        value = pattern % (value, "Hide Premium Items", AddonSettings.hide_premium_items())
        value = pattern % (value, "Show Cloaked Items", AddonSettings.show_cloaked_items())
        value = pattern % (value, "Show Dutch", AddonSettings.show_channel_with_language("nl"))
        value = pattern % (value, "Show Swedish", AddonSettings.show_channel_with_language("se"))
        value = pattern % (value, "Show Lithuanian", AddonSettings.show_channel_with_language("lt"))
        value = pattern % (value, "Show Latvian", AddonSettings.show_channel_with_language("lv"))
        value = pattern % (value, "Show British", AddonSettings.show_channel_with_language("en-gb"))
        value = pattern % (value, "Show German", AddonSettings.show_channel_with_language("de"))
        value = pattern % (value, "Show Finnish", AddonSettings.show_channel_with_language("fi"))
        value = pattern % (value, "Show Other languages", AddonSettings.show_channel_with_language(None))
        return value
