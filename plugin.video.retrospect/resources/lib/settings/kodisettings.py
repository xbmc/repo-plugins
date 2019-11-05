# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmcaddon

from . import settingsstore


class KodiSettings(settingsstore.SettingsStore):
    def __init__(self, logger, addon_id=None):
        super(KodiSettings, self).__init__(logger)

        self.__channel_setting_format = "channel_{0}_{1}"
        self.__addon_settings = xbmcaddon.Addon() if addon_id is None else xbmcaddon.Addon(addon_id)

    def set_setting(self, setting_id, setting_value, channel=None):
        setting_value = str(setting_value)

        if channel:
            channel_setting_id = self.__channel_setting_format.format(channel.guid, setting_id)
            self.__addon_settings.setSetting(channel_setting_id, str(setting_value))
            self._logger.trace("Kodi Channel Setting Updated: %s.%s(%s)='%s'",
                               channel.id, setting_id, channel_setting_id,
                               self._get_safe_print_value(setting_id, setting_value))
        else:
            self.__addon_settings.setSetting(setting_id, str(setting_value))
            self._logger.trace("Kodi Setting Updated: %s='%s'", setting_id,
                               self._get_safe_print_value(setting_id, setting_value))

        return setting_value

    def get_boolean_setting(self, setting_id, channel=None, default=True):
        bool_value = self.get_setting(setting_id, channel)
        if bool_value is None:
            return default

        return bool_value == "true"

    def get_integer_setting(self, setting_id, channel=None, default=None):
        int_value = self.get_setting(setting_id, channel)
        if int_value is None:
            return default

        return int(int_value)

    def get_setting(self, setting_id, channel=None, default=None):
        if channel:
            channel_setting_id = self.__channel_setting_format.format(channel.guid, setting_id)
            setting_value = self.__addon_settings.getSetting(channel_setting_id)
            self._logger.trace("Kodi Channel Setting: %s.%s(%s)='%s'",
                               channel.id, setting_id, channel_setting_id,
                               self._get_safe_print_value(setting_id, setting_value))
        else:
            setting_value = self.__addon_settings.getSetting(setting_id)
            self._logger.trace("Kodi Setting: %s='%s'", setting_id,
                               self._get_safe_print_value(setting_id, setting_value))

        return setting_value or default

    def get_localized_string(self, string_id):
        return self.__addon_settings.getLocalizedString(string_id)

    def open_settings(self):
        self.__addon_settings.openSettings()

    # this really only works if no reference to the <store> object is kept somewhere.
    def __del__(self):
        if self.__addon_settings is not None:
            del self.__addon_settings
            self.__addon_settings = None
            self._logger.debug("Removed Kodi settings-store")
