#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import io
import uuid
import shutil
import threading

import xbmc

from logger import Logger                               # this has not further references
from proxyinfo import ProxyInfo                         # this has not further references
from retroconfig import Config                          # this has not further references
from helpers.htmlentityhelper import HtmlEntityHelper   # Only has Logger as reference
from settings import localsettings, kodisettings, settingsstore

# Theoretically we could add a remote settings store too!
KODI = "kodi"
LOCAL = "local"


class AddonSettings(object):
    """ Static Class for retrieving Kodi Addon settings """

    __NO_PROXY = True

    # these are static properties that store the settings. Creating them each time is causing major slow-down
    __user_agent = None
    __kodi_version = None

    __PROXY_SETTING = "proxy"
    __LOCAL_IP_SETTING = "local_ip"
    __USER_AGENT_SETTING = "user_agent"
    __MD5_HASH_VALUE = "md_hash_value"
    __CLIENT_ID = "client_id"

    #region Setting-stores properties and intialization
    __setting_stores = {}
    __settings_lock = threading.Lock()

    __language_strings = {}
    __language_current = None

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
    def is_min_version(min_value):
        """ Checks whether the version of Kodi is higher or equal to the given version.

        :param min_value: the minimum Kodi version
        :type min_value: int

        :return: True if higher or equal, False otherwise.
        :rtype: bool

        """

        version = int(AddonSettings.get_kodi_version().split(".")[0])
        return version >= min_value
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

        :return: Indication weheter or not to show cloaked items.
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

        :return: Indaction if the restricted folders should be hidden
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
    def get_available_countries(as_string=False, as_country_codes=False):
        """ returns the all available ProxyGroupId's in order. The countries are:

             :param bool as_country_codes:  Returns alls the actual country codes values.
             :param bool as_string:         Returns the translation ID for all the possible country
                                            codes as strings.

             :return: List[str] A list of either country codes or translation ID's

             * other - Other languages
             * uk    - United Kingdom
             * nl    - The Netherlands
             * se    - Sweden
             * no    - Norway
             * de    - Germany
             * be    - Belgium
             * ee    - Estonia
             * lt    - Lithuani
             * lv    - Latvia
             * dk    - Danish

        """

        proxy_ids = [30025, 30300, 30301, 30307, 30302, 30305, 30309, 30306, 30308, 30303, 30304, 30310]
        proxy_codes = [None, "other", "nl", "uk", "se", "no", "de", "be", "ee", "lt", "lv", "dk"]

        if as_string:
            return [str(i) for i in proxy_ids]

        if as_country_codes:
            return proxy_codes

        return proxy_ids

    @staticmethod
    def hide_geo_locked_items_for_location(channel_region, value_only=False):
        """ Returs the config value that indicates what if we should hide items that are geografically
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
        current_geograffical_region = values[value_index]

        if value_only:
            return current_geograffical_region

        # if no geo region is selected, always show everything.
        if current_geograffical_region is None:
            return False

        # only hide if the regions don't match
        return not current_geograffical_region == channel_region
    #endregion

    #region Language caching
    @staticmethod
    def set_language():
        """ Sets the language of the current Plugin run. The value is taken from the Kodi API """

        language = xbmc.getLanguage()
        if AddonSettings.__language_current != language:
            AddonSettings.__language_strings = {}
            Logger.info("Setting language from %s to %s", AddonSettings.__language_current, language)
            AddonSettings.__language_current = language

        return

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
    def send_usage_statistics():
        """ returns true if the user allows usage statistics sending

        :return: Indication if sending GA statistics is allowed.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("send_statistics", default=True)

    @staticmethod
    def get_current_addon_xml_md5():
        """ Retrieves the current addons.xml.md5 content that was cached in the settings.

        :return: the curreent addons.xml.md5 content
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
                                            Adaptive add-onand only validate other criteria.
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

        if channel_setting is False:
            Logger.info("Adaptive Stream add-on disabled from Channel settings")
            return False

        if ignore_add_on_config:
            Logger.debug(
                "Ignoring Retrospect setting use_adaptive_addon=%s and using it anyways.", use_add_on)

        # if the add-on was disabled, don't use it, unless specified by the channel setting
        elif not use_add_on:
            # check the channel setting, if it set to True, we should obey that and not return False
            if channel_setting is not True:
                Logger.info("Adaptive Stream add-on disabled from Retrospect settings")
                return False

            Logger.info("Adaptive Stream add-on is disabled from Retrospect settings but enabled from channel")

        # we should use it, so if we can't find it, it is not so OK.
        adaptive_add_on_id = "inputstream.adaptive"
        adaptive_add_on_installed = \
            xbmc.getCondVisibility('System.HasAddon("{0}")'.format(adaptive_add_on_id)) == 1

        if not adaptive_add_on_installed:
            Logger.warning("Adaptive Stream add-on '%s' is not installed/enabled.", adaptive_add_on_id)
            return False

        kodi_leia = AddonSettings.is_min_version(18)
        Logger.info("Adaptive Stream add-on '%s' %s decryption support was found.",
                    adaptive_add_on_id, "with" if kodi_leia else "without")

        if with_encryption:
            return kodi_leia

        return adaptive_add_on_installed

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
        from envcontroller import EnvController

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
    def get_release_track():
        """ Retrieves the current release track we are on:

        0: Stable releases only.
        1: Experimental releases.

        :return: 0 for Stable, 1 for Experimental releases.
        :rtype: int

        """

        release_channel = AddonSettings.store(KODI).get_integer_setting("release_channel")
        return release_channel

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

        :return: Incidation if HTTP(s) requests should be cached or not.
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

        :rtype: int
        :returns: the maximum stream bitrate. If channel was provided, it will return the configured
                  value for that channel.

        """

        setting = "Retrospect"
        if channel is not None:
            setting = AddonSettings.get_max_channel_bitrate(channel)

        if setting == "Retrospect":
            setting = AddonSettings.store(KODI).get_setting("stream_bitrate")
            Logger.debug("Using the Retrospect Default Bitrate: %s", setting)
        else:
            Logger.debug("Using the Channel Specific Bitrate: %s", setting)
        return int(setting or 8000)

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
                 seperately.

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
    def use_subtitle():
        """Returns whether to show subtitles or not

        :return: Indication if Kodi should how subs or not
        :rtype: bool

        """

        setting = AddonSettings.store(KODI).get_setting("subtitle_mode", default="0")

        if setting == "0":
            return True
        else:
            return False

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

        :returnL: The requested log level
        :rtype: int

        """

        level = AddonSettings.store(KODI).get_integer_setting("log_level", default=2)
        # noinspection PyTypeChecker
        return int(level) * 10

    @staticmethod
    def set_channel_visiblity(channel, visible):
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
        if AddonSettings.is_min_version(18):
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
         * ee    - Estoniam
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

    @staticmethod
    def get_local_ip_header_for_channel(channel_info):
        """ returns the local IP for a specific channel

        :param channel_info: ChannelInfo - The channel to get proxy info for

        :return: The LocalIP related x-forwarded-for HTTP Header
        :rtype: dict

        """

        if AddonSettings.__NO_PROXY:
            return None

        prefix = AddonSettings.get_local_ip_header_country_code_for_channel(channel_info)
        if prefix is None:
            Logger.debug("No Local IP configured for %s", channel_info)
            return None

        Logger.debug("Country settings '%s' configured for Local IP for %s", prefix, channel_info)

        server = AddonSettings.store(KODI).get_setting("%s_local_ip" % (prefix,), default=None)
        if not server:
            Logger.debug("No Local IP found for country '%s'", prefix)
            return None

        Logger.debug("Found Local IP for channel %s:\nLocal IP: %s", channel_info, server)
        return {"X-Forwarded-For": server}

    @staticmethod
    def get_local_ip_header_country_code_for_channel(channel_info):
        """ Returns the Country code for the LocalIP that is configured for this channel

        :param channel_info:  The ChannelInfo object

        :rtype: str
        :return: 2 character ISO country code

        """
        if AddonSettings.__NO_PROXY:
            return None

        country_code = AddonSettings.store(LOCAL).\
            get_setting(AddonSettings.__LOCAL_IP_SETTING, channel_info)
        return country_code

    @staticmethod
    def set_local_ip_for_channel(channel_info, country_code):
        """ Sets the country code for the local IP for a channel

        :param channel_info:        The channel
        :param str country_code:    The country code to use for local IP configuration

        """

        if country_code == "other":
            Logger.warning("LocalIP updating to 'other' which is invalid. Setting it to None.")
            country_code = None

        AddonSettings.store(LOCAL).\
            set_setting(AddonSettings.__LOCAL_IP_SETTING, country_code, channel=channel_info)
        return

    # noinspection PyUnusedLocal
    @staticmethod
    def get_proxy_for_channel(channel_info):
        """ returns the proxy for a specific channel

        :param channel_info: The channel to get proxy info for

        :rtype: None|ProxyInfo
        :return: The ProxyInfo object to use for calls for this channel. None means no proxy.

        """

        if AddonSettings.__NO_PROXY:
            return None

        prefix = AddonSettings.get_proxy_country_code_for_channel(channel_info)
        if prefix is None:
            Logger.debug("No proxy configured for %s", channel_info)
            return None

        Logger.debug("Country settings '%s' configured for Proxy for %s", prefix, channel_info)

        server = AddonSettings.store(KODI).get_setting("%s_proxy_server" % (prefix,))
        port = AddonSettings.store(KODI).get_integer_setting("%s_proxy_port" % (prefix,), default=0)
        proxy_type = AddonSettings.store(KODI).get_setting("%s_proxy_type" % (prefix,))

        if not proxy_type or proxy_type.lower() not in ('dns', 'http') or not server:
            Logger.debug("No proxy found for country '%s'", prefix)
            return None

        username = AddonSettings.store(KODI).\
            get_setting("%s_proxy_username" % (prefix,), default="")
        password = AddonSettings.store(KODI).\
            get_setting("%s_proxy_password" % (prefix,), default="")

        p_info = ProxyInfo(server, port,
                           scheme=proxy_type.lower(), username=username, password=password)
        Logger.debug("Found proxy for channel %s:\n%s", channel_info, p_info)
        return p_info

    @staticmethod
    def get_proxy_country_code_for_channel(channel_info):
        """ Returns the Country code for the proxy that is configured for this channel

        :param channel_info:  The ChannelInfo object

        :return: 2 character ISO country code
        :rtype: str

        """

        if AddonSettings.__NO_PROXY:
            return None

        country_code = AddonSettings.store(LOCAL).\
            get_setting(AddonSettings.__PROXY_SETTING, channel_info)
        return country_code

    @staticmethod
    def set_proxy_id_for_channel(channel_info, country_code):
        """ Sets the country code for the proxy for a channel

        :param channel_info: The channel
        :param str country_code: The country code for the proxy to use.

        """

        AddonSettings.store(LOCAL).\
            set_setting(AddonSettings.__PROXY_SETTING, country_code, channel_info)
        return

    #noinspection PyUnresolvedReferences
    @staticmethod
    def update_add_on_settings_with_channels(channels, config):
        """ updats the settings.xml to include all the channels

        :param list[any] channels:  The channels to add to the settings.xml
        :param type[Config] config: The configuration object

        """

        # sort the channels
        channels.sort(key=lambda c: c.sort_key)

        # Then we read the original file
        filename_template = os.path.join(config.rootDir, "resources", "data", "settings_template.xml")
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
        from helpers.templatehelper import TemplateHelper
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
                shutil.copy(user_settings, user_settings_backup)
            else:
                Logger.warning("No user settings found at: %s", user_settings)

            # Update the addonsettings.xml by first updating a temp xml file.
            Logger.debug("Creating new settings.xml file: %s", filename_temp)
            Logger.trace(new_contents)
            with io.open(filename_temp, "w+", encoding='utf-8') as fp:
                fp.write(new_contents)

            Logger.debug("Replacing existing settings.xml file: %s", filename)
            shutil.move(filename_temp, filename)

            # restore the user profile settings.xml file when needed
            if os.path.isfile(user_settings) and os.stat(user_settings).st_size != os.stat(user_settings_backup).st_size:
                Logger.critical("User settings.xml was overwritten during setttings update. Restoring from %s", user_settings_backup)
                shutil.copy(user_settings_backup, user_settings)
        except:
            Logger.error("Something went wrong trying to update the settings.xml", exc_info=True)

            #  clean up time file
            if os.path.isfile(filename_temp):
                os.remove(filename_temp)

            # restore original settings
            with io.open(filename_temp, "w+", encoding='utf-8') as fp:
                fp.write(contents)

            shutil.move(filename_temp, filename)
            return

        Logger.info("Settings.xml updated succesfully. Reloading settings.")
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
    def __update_add_on_settings_with_channel_settings(contents, channels):
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
            if channel.moduleName not in settings:
                settings[channel.moduleName] = []

            # First any specific settings
            if channel.settings:
                # Sort the settings so they are really in the correct order, because this is not guaranteed by the
                # json parser
                channel.settings.sort(key=lambda a: a["order"])
                for channel_settings in channel.settings:
                    setting_id = channel_settings["id"]
                    setting_value = channel_settings["value"]
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

                    # existing_setting_xml_index = []
                    # for i, elem in enumerate(settings[channel.moduleName]):
                    #     if 'aa' in elem:
                    #         existing_setting_xml_index.append(i)
                    #
                    # Alternatively, as a list comprehension:
                    #
                    # indices = [i for i, elem in enumerate(settings[channel.moduleName]) if 'aa' in elem]

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

            # remove if no settings else, add them to the list with settings
            if len(settings[channel.moduleName]) == 0:
                settings.pop(channel.moduleName)
            else:
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
        value = pattern % (value, "use_subtitle", AddonSettings.use_subtitle())
        value = pattern % (value, "cache_http_responses", AddonSettings.cache_http_responses())
        value = pattern % (value, "Folder Prefx", "'%s'" % AddonSettings.get_folder_prefix())
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

        if AddonSettings.__NO_PROXY:
            return value

        try:
            proxies = AddonSettings.get_available_countries(as_country_codes=True)
            for country in proxies:
                if country is None:
                    continue
                elif country == "other":
                    country = country.title()
                else:
                    country = country.upper()

                proxy_title = "{0} Proxy".format(country)
                proxy_value = "{0} ({1})".format(
                    AddonSettings.store(KODI).get_setting(
                        "{0}_proxy_server".format(country.lower()), default="Not Set"),
                    AddonSettings.store(KODI).get_setting(
                        "{0}_proxy_type".format(country.lower()), default="Not Set"))
                value = pattern % (value, proxy_title, proxy_value)

                proxy_port_title = "{0} Proxy Port".format(country)
                proxy_port_value = \
                    AddonSettings.store(KODI).get_integer_setting(
                        "{0}_proxy_port".format(country.lower()), default=0)
                value = pattern % (value, proxy_port_title, proxy_port_value)

                local_ip_title = "{0} Local IP".format(country)
                local_ip_value = AddonSettings.store(KODI). \
                    get_setting("{0}_local_ip".format(country.lower()), default="Not Set")
                value = pattern % (value, local_ip_title, local_ip_value)
        except:
            Logger.error("Error", exc_info=True)
        return value
