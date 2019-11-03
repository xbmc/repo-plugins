# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import io
import json
import shutil

from . import settingsstore


class LocalSettings(settingsstore.SettingsStore):
    __settings = None

    __SETTINGS_KEY = "settings"
    __CHANNELS_KEY = "channels"

    def __init__(self, addon_data_folder, logger):
        super(LocalSettings, self).__init__(logger)

        if not addon_data_folder or not os.path.isdir(addon_data_folder):
            raise ValueError("Invalid add-data path: {0}".format(addon_data_folder))

        self.addon_data_folder = addon_data_folder
        self.local_settings_file = os.path.join(self.addon_data_folder, "settings.json")

        # load the settings each time. A new instance will use the same __settings object, but
        # each new install will cause a reload of the settings from disk. In theory there should
        # only be a single store active
        self.__load_settings()

    def set_setting(self, setting_id, setting_value, channel=None):
        if channel is None:
            LocalSettings.__settings[LocalSettings.__SETTINGS_KEY][setting_id] = setting_value
            self._logger.debug("Local Setting Updated: %s: '%s'",
                               setting_id,
                               self._get_safe_print_value(setting_id, setting_value))
        else:
            if channel.id not in LocalSettings.__settings[LocalSettings.__CHANNELS_KEY]:
                LocalSettings.__settings[LocalSettings.__CHANNELS_KEY][channel.id] = {}

            LocalSettings.__settings[LocalSettings.__CHANNELS_KEY][channel.id][setting_id] = \
                setting_value

            self._logger.debug("Local Channel Setting Updated: %s:%s: '%s'",
                               channel.id, setting_id,
                               self._get_safe_print_value(setting_id, setting_value))

        # store the file
        self.__store_settings()
        return setting_value

    def get_boolean_setting(self, setting_id, channel=None, default=None):
        return self.get_setting(setting_id, channel, default)

    def get_integer_setting(self, setting_id, channel=None, default=None):
        return self.get_setting(setting_id, channel, default)

    def get_setting(self, setting_id, channel=None, default=None):
        if channel is None:
            setting_value = LocalSettings.__settings["settings"].get(setting_id, default)

            self._logger.trace("Local Setting: %s='%s'", setting_id,
                               self._get_safe_print_value(setting_id, setting_value))
        else:
            channel_settings = LocalSettings.__settings["channels"].get(channel.id, {})
            setting_value = channel_settings.get(setting_id, default)
            self._logger.trace("Local Channel Setting: %s.%s='%s'", channel.id, setting_id,
                               self._get_safe_print_value(setting_id, setting_value))

        # the default was already retrieved by the dict.get(key, default)
        return setting_value

    def open_settings(self):
        raise NotImplementedError()

    def get_localized_string(self, string_id):
        raise NotImplementedError()

    # this really only works if no reference to the <store> object is kept somewhere.
    def __del__(self):
        if LocalSettings.__settings is not None:
            del LocalSettings.__settings
            LocalSettings.__settings = None
        self._logger.debug("Removed Local settings-store")

    def __str__(self):
        return "LocalSettings store: {0}".format(self.local_settings_file)

    def __load_settings(self):
        if not os.path.isfile(self.local_settings_file):
            LocalSettings.__settings = self.__empty_settings()
            self._logger.warning("No local settings file found: %s", self.local_settings_file)
            return

        try:
            with io.open(self.local_settings_file, mode="rb") as fp:
                content = fp.read()
                if not content:
                    LocalSettings.__settings = self.__empty_settings()
                    self._logger.warning("Empty local settings file found: %s", self.local_settings_file)
                    return

                # Print the content might expose secret settings. See self._secure_setting_ids
                # self._logger.Trace("Loading settings: %s", content)
                LocalSettings.__settings = json.loads(content, encoding='utf-8')
        except:
            self._logger.error("Error loading JSON settings. Resetting all settings.", exc_info=True)
            LocalSettings.__settings = self.__empty_settings()
            backup = self.local_settings_file.replace(".json", ".error.json")
            self._logger.warning("Creating backup of settings file: %s", backup)
            shutil.copy(
                self.local_settings_file,
                backup
            )
            self.__store_settings()
            return

    def __store_settings(self):
        if LocalSettings.__settings is None or not list(LocalSettings.__settings.keys()):
            raise ValueError("Empty settings object cannot save.")

        # open the file as binary file, as json.dumps will already encode as utf-8 bytes
        with io.open(self.local_settings_file, mode='w+b') as fp:
            content = json.dumps(LocalSettings.__settings, indent=4).encode('utf-8')
            fp.write(content)

            # Print the content might expose secret settings. See self._secure_setting_ids
            # self._logger.Debug("Storing settings: %s", content)

    def __empty_settings(self):
        return {
            LocalSettings.__SETTINGS_KEY: {},
            LocalSettings.__CHANNELS_KEY: {}
        }
