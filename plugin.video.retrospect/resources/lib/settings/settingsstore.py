# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.logger import Logger


class SettingsStore(object):
    def __init__(self, logger):
        """ Creates a SettingsStore object.

        :param Logger logger:   A logger instance

        """

        if not logger:
            raise ValueError("Missing logger")

        self._logger = logger
        # What settings should we not expose via the logger?
        self._secure_setting_ids = ["application_key", "client_id"]

    def set_setting(self, setting_id, setting_value, channel=None):
        """ Returns a boolean value for the given setting_id.

        :param str|unicode setting_id:  The ID of the setting that is to be retrieved.
        :param any channel:             If specified the specific channel setting is retrieved.
        :param any setting_value:       The value to store for the setting.

        """

        pass

    def get_boolean_setting(self, setting_id, channel=None, default=None):
        """ Returns a boolean value for the given setting_id.

        :param str|unicode setting_id:  The ID of the setting that is to be retrieved.
        :param channel:                 If specified the specific channel setting is retrieved.
        :param bool default:            The default value in case the settings is not set yet.

        :returns: the boolean value for the given setting_id
        :rtype: bool

        """

        pass

    def get_integer_setting(self, setting_id, channel=None, default=None):
        """ Returns an integer value for the given setting_id.

        :param str|unicode setting_id:  The ID of the setting that is to be retrieved.
        :param channel:                 If specified the specific channel setting is retrieved.
        :param int default:             The default value in case the settings is not set yet.

        :returns: the integer value for the given setting_id
        :rtype: int

        """

        pass

    def get_setting(self, setting_id, channel=None, default=None):
        """ Returns an string value for the given setting_id.

        :param str|unicode setting_id:      The ID of the setting that is to be retrieved.
        :param channel:                     If specified the specific channel setting is retrieved.
        :param str|unicode|none default:    The default value in case the settings is not set yet.

        :returns: The value of the setting stored under the given ID.
        :rtype: str|unicode

        """

        pass

    def get_localized_string(self, string_id):
        """ Returns an integer value for the given setting_id.

        :param int string_id:   The ID of the localization to retrieve.

        :returns: The localized value for the string_id.
        :rtype: str|unicode

        """

        pass

    def open_settings(self):
        """ Open the corresponding settings dialogue. """

        pass

    def _get_safe_print_value(self, setting_id, setting_value):
        """ Makes sure we strip out the sensitive data while logging.

        :param str|unicode setting_id:      The settings ID to check.
        :param str|unicode setting_value:   The value to show or not.

        :return: A string value to can safely be displayed in logs.
        :rtype: str|unicode

        """

        if setting_id in self._secure_setting_ids:
            return "<no of your business>"
        return setting_value

    def __del__(self):
        pass
