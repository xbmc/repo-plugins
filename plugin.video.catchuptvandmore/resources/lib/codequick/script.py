# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
import logging
import os

# Kodi imports
import xbmcaddon
import xbmcgui
import xbmc

# Package imports
from resources.lib.codequick.utils import ensure_unicode, ensure_native_str, unicode_type, string_map
from resources.lib.codequick.support import dispatcher, script_data, addon_data, logger_id

__all__ = ["Script", "Settings"]

# Logger used by the addons
addon_logger = logging.getLogger(logger_id)


class Settings(object):
    """Settings class to handle the getting and setting of "add-on" settings."""

    def __getitem__(self, key):
        """
        Returns the value of a setting as a "unicode string".

        :param str key: ID of the setting to access.

        :return: Setting as a "unicode string".
        :rtype: str
        """
        return addon_data.getSetting(key)

    def __setitem__(self, key, value):
        """
        Set add-on setting.

        :param str key: ID of the setting.
        :param str value: Value of the setting.
        """
        # noinspection PyTypeChecker
        addon_data.setSetting(key, ensure_unicode(value))

    def __delitem__(self, key):  # type: (str) -> None
        """Set an add-on setting to a blank string."""
        addon_data.setSetting(key, "")

    @staticmethod
    def get_string(key, addon_id=None):
        """
        Returns the value of a setting as a "unicode string".

        :param str key: ID of the setting to access.
        :param str addon_id: [opt] ID of another add-on to extract settings from.

        :raises RuntimeError: If ``addon_id`` is given and there is no add-on with given ID.

        :return: Setting as a "unicode string".
        :rtype: str
        """
        if addon_id:
            return xbmcaddon.Addon(addon_id).getSetting(key)
        else:
            return addon_data.getSetting(key)

    @staticmethod
    def get_boolean(key, addon_id=None):
        """
        Returns the value of a setting as a "Boolean".

        :param str key: ID of the setting to access.
        :param str addon_id: [opt] ID of another add-on to extract settings from.

        :raises RuntimeError: If ``addon_id`` is given and there is no add-on with given ID.

        :return: Setting as a "Boolean".
        :rtype: bool
        """
        setting = Settings.get_string(key, addon_id).lower()
        return setting == u"true" or setting == u"1"

    @staticmethod
    def get_int(key, addon_id=None):
        """
        Returns the value of a setting as a "Integer".

        :param str key: ID of the setting to access.
        :param str addon_id: [opt] ID of another add-on to extract settings from.

        :raises RuntimeError: If ``addon_id`` is given and there is no add-on with given ID.

        :return: Setting as a "Integer".
        :rtype: int
        """
        return int(Settings.get_string(key, addon_id))

    @staticmethod
    def get_number(key, addon_id=None):
        """
        Returns the value of a setting as a "Float".

        :param str key: ID of the setting to access.
        :param str addon_id: [opt] ID of another addon to extract settings from.

        :raises RuntimeError: If ``addon_id`` is given and there is no addon with given ID.

        :return: Setting as a "Float".
        :rtype: float
        """
        return float(Settings.get_string(key, addon_id))


class Script(object):
    """
    This class is used to create "Script" callbacks. Script callbacks are callbacks
    that just execute code and return nothing.

    This class is also used as the base for all other types of callbacks i.e.
    :class:`codequick.Route<codequick.route.Route>` and :class:`codequick.Resolver<codequick.resolver.Resolver>`.
    """
    # Set the listitem types to that of a script
    is_playable = False
    is_folder = False

    #: Critical logging level, maps to "xbmc.LOGFATAL".
    CRITICAL = 50
    #: Critical logging level, maps to "xbmc.LOGWARNING".
    WARNING = 30
    #: Critical logging level, maps to "xbmc.LOGERROR".
    ERROR = 40
    #: Critical logging level, maps to "xbmc.LOGDEBUG".
    DEBUG = 10
    #: Critical logging level, maps to "xbmc.LOGNOTICE".
    INFO = 20

    #: Kodi notification warning image.
    NOTIFY_WARNING = 'warning'
    #: Kodi notification error image.
    NOTIFY_ERROR = 'error'
    #: Kodi notification info image.
    NOTIFY_INFO = 'info'

    setting = Settings()
    """
    Dictionary like interface of "add-on" settings.
    See :class:`script.Settings<codequick.script.Settings>` for more details.
    """

    #: Underlining logger object, for advanced use. See :class:`logging.Logger` for more details.
    logger = addon_logger

    #: Dictionary of all callback parameters, for advanced use.
    params = dispatcher.params

    def __init__(self):
        self._title = self.params.get(u"_title_", u"")
        self.handle = dispatcher.handle

    @classmethod
    def register(cls, callback):
        """
        Decorator used to register callback functions.

        :param callback: The callback function to register.
        :returns: The original callback function.
        """
        return dispatcher.register_callback(callback, parent=cls)

    @staticmethod
    def register_delayed(func, *args, **kwargs):
        """
        Registers a function that will be executed after Kodi has finished listing all "listitems".
        Since this function is called after the listitems has been shown, it will not slow down the
        listing of content. This is very useful for fetching extra metadata for later use.

        .. note::

            Functions will be called in reverse order to the order they are added (LIFO).

        :param func: Function that will be called after "xbmcplugin.endOfDirectory" is called.
        :param args: "Positional" arguments that will be passed to function.
        :param kwargs: "Keyword" arguments that will be passed to function.

        .. note::

            There is one optional keyword only argument ``function_type``. Values are as follows.
            * ``0`` Only run if no errors are raised. (Default)
            * ``1`` Only run if an error has occurred.
            * ``2`` Run regardless if an error was raised or not.

        .. note::

            If there is an argument called exception in the delayed function callback and an error was raised,
            then that exception argument will be set to the raised exception object.
            Otherwise it will be set to None.
        """
        function_type = kwargs.get("function_type", 0)
        dispatcher.register_delayed(func, args, kwargs, function_type)

    @staticmethod
    def log(msg, args=None, lvl=10):
        """
        Logs a message with logging level of "lvl".

        Logging Levels.
            * :attr:`Script.DEBUG<codequick.script.Script.DEBUG>`
            * :attr:`Script.INFO<codequick.script.Script.INFO>`
            * :attr:`Script.WARNING<codequick.script.Script.WARNING>`
            * :attr:`Script.ERROR<codequick.script.Script.ERROR>`
            * :attr:`Script.CRITICAL<codequick.script.Script.CRITICAL>`

        :param str msg: The message format string.
        :type args: list or tuple
        :param args: List of arguments which are merged into msg using the string formatting operator.
        :param int lvl: The logging level to use. default => 10 (Debug).

        .. Note::

            When a log level of 50(CRITICAL) is given, all debug messages that were previously logged will
            now be logged as level 30(WARNING). This allows for debug messages to show in the normal Kodi
            log file when a CRITICAL error has occurred, without having to enable Kodi's debug mode.
        """
        if args:
            addon_logger.log(lvl, msg, *args)
        else:
            addon_logger.log(lvl, msg)

    @staticmethod
    def notify(heading, message, icon=None, display_time=5000, sound=True):
        """
        Send a notification to Kodi.

        Options for icon are.
            * :attr:`Script.NOTIFY_INFO<codequick.script.Script.NOTIFY_INFO>`
            * :attr:`Script.NOTIFY_ERROR<codequick.script.Script.NOTIFY_ERROR>`
            * :attr:`Script.NOTIFY_WARNING<codequick.script.Script.NOTIFY_WARNING>`

        :param str heading: Dialog heading label.
        :param str message: Dialog message label.
        :param str icon: [opt] Icon image to use. (default => 'add-on icon image')

        :param int display_time: [opt] Ttime in "milliseconds" to show dialog. (default => 5000)
        :param bool sound: [opt] Whether or not to play notification sound. (default => True)
        """
        # Ensure that heading, message and icon
        # is encoded into native str type
        heading = ensure_native_str(heading)
        message = ensure_native_str(message)
        icon = ensure_native_str(icon if icon else Script.get_info("icon"))

        dialog = xbmcgui.Dialog()
        dialog.notification(heading, message, icon, display_time, sound)

    @staticmethod
    def localize(string_id):
        """
        Retruns a translated UI string from addon localization files.

        .. note::

            :data:`utils.string_map<codequick.utils.string_map>`
            needs to be populated before you can pass in a string as the reference.

        :param string_id: The numeric ID or gettext string ID of the localized string
        :type string_id: str or int

        :returns: Localized unicode string.
        :rtype: str

        :raises Keyword: if a gettext string ID was given but the string is not found in English :file:`strings.po`.
        :example:
            >>> Script.localize(30001)
            "Toutes les vidéos"
            >>> Script.localize("All Videos")
            "Toutes les vidéos"
        """
        if isinstance(string_id, (str, unicode_type)):
            try:
                numeric_id = string_map[string_id]
            except KeyError:
                raise KeyError("no localization found for string id '%s'" % string_id)
            else:
                return addon_data.getLocalizedString(numeric_id)

        elif 30000 <= string_id <= 30999:
            return addon_data.getLocalizedString(string_id)
        elif 32000 <= string_id <= 32999:
            return script_data.getLocalizedString(string_id)
        else:
            return xbmc.getLocalizedString(string_id)

    @staticmethod
    def get_info(key, addon_id=None):
        """
        Returns the value of an add-on property as a unicode string.

        Properties.
            * author
            * changelog
            * description
            * disclaimer
            * fanart
            * icon
            * id
            * name
            * path
            * profile
            * stars
            * summary
            * type
            * version

        :param str key: "Name" of the property to access.
        :param str addon_id: [opt] ID of another add-on to extract properties from.

        :return: Add-on property as a unicode string.
        :rtype: str

        :raises RuntimeError: If add-on ID is given and there is no add-on with given ID.
        """
        if addon_id:
            # Extract property from a different add-on
            resp = xbmcaddon.Addon(addon_id).getAddonInfo(key)
        elif key == "path_global" or key == "profile_global":
            # Extract property from resources.lib.codequick addon
            resp = script_data.getAddonInfo(key[:key.find("_")])
        else:
            # Extract property from the running addon
            resp = addon_data.getAddonInfo(key)

        # Check if path needs to be translated first
        if resp[:10] == "special://":  # pragma: no cover
            resp = xbmc.translatePath(resp)

        # Convert response to unicode
        path = resp.decode("utf8") if isinstance(resp, bytes) else resp

        # Create any missing directory
        if key.startswith("profile"):
            if not os.path.exists(path):  # pragma: no cover
                os.mkdir(path)

        return path
