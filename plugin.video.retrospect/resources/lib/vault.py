# SPDX-License-Identifier: GPL-3.0-or-later

import pyaes        #: Pure Python AES
import pyscrypt     #: Pure Python SCrypt

import base64
import random
import string
import hashlib

from resources.lib.backtothefuture import PY2
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings, LOCAL, KODI
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.encodinghelper import EncodingHelper


class Vault(object):
    # bytes representation of the key. Use bytes.decode() to get string representation
    __Key = None  # type: bytes
    __APPLICATION_KEY_SETTING = "application_key"
    __VAULT_HOWTO_SETTING = "vault_shown"

    def __init__(self):
        """ Creates a new instance of the Vault class """

        self.__newKeyGeneratedInConstructor = False    # : This was the very first time a key was generated

        # ask for PIN of no key is present
        if Vault.__Key is None:
            howto_shown = self.__show_howto()
            key = self.__get_application_key()  # type: bytes

            # was there a key? No, let's initialize it.
            if key is None:
                Logger.warning("No Application Key present. Initializing a new one.")

                # Show the how to if it was not already shown during this __init__()
                if not howto_shown:
                    self.__show_howto(force=True)

                key = self.__get_new_key()
                if not self.change_pin(key):
                    raise RuntimeError("Error creating Application Key.")
                Logger.info("Created a new Application Key with MD5: %s (length=%s)",
                            EncodingHelper.encode_md5(key), len(key))
                self.__newKeyGeneratedInConstructor = True

            Vault.__Key = key
            Logger.trace("Using Application Key with MD5: %s (length=%s)", EncodingHelper.encode_md5(key), len(key))

    def change_pin(self, application_key=None):
        """ Stores an existing ApplicationKey using a new PIN.

        :param bytes application_key: an existing ApplicationKey that will be stored. If none
                                      specified, the existing ApplicationKey of the Vault will
                                      be used.

        :return: Indication of success.
        :rtype: bool

        """

        Logger.info("Updating the ApplicationKey with a new PIN")

        if self.__newKeyGeneratedInConstructor:
            Logger.info("A key was just generated, no need to change PINs.")
            return True

        if application_key is None:
            Logger.debug("Using the ApplicationKey from the vault.")
            application_key = Vault.__Key
        else:
            Logger.debug("Using the ApplicationKey from the input parameter.")

        if not application_key:
            raise ValueError("No ApplicationKey specified.")

        # Now we get a new PIN and (re)encrypt

        pin = XbmcWrapper.show_key_board(
            heading=LanguageHelper.get_localized_string(LanguageHelper.VaultNewPin),
            hidden=True)
        if not pin:
            XbmcWrapper.show_notification(
                "", LanguageHelper.get_localized_string(LanguageHelper.VaultNoPin),
                XbmcWrapper.Error)
            return False

        pin2 = XbmcWrapper.show_key_board(
            heading=LanguageHelper.get_localized_string(LanguageHelper.VaultRepeatPin),
            hidden=True)
        if pin != pin2:
            Logger.critical("Mismatch in PINs")
            XbmcWrapper.show_notification(
                "",
                LanguageHelper.get_localized_string(LanguageHelper.VaultPinsDontMatch),
                XbmcWrapper.Error)
            return False

        if PY2:
            encrypted_key = "%s=%s" % (self.__APPLICATION_KEY_SETTING, application_key)
        else:
            # make it text to store
            encrypted_key = "%s=%s" % (self.__APPLICATION_KEY_SETTING, application_key.decode())

        # let's generate a pin using the scrypt password-based key derivation
        pin_key = self.__get_pbk(pin)
        encrypted_key = self.__encrypt(encrypted_key, pin_key)
        AddonSettings.set_setting(Vault.__APPLICATION_KEY_SETTING, encrypted_key, store=LOCAL)
        Logger.info("Successfully updated the Retrospect PIN")
        return True

    @staticmethod
    def reset():
        """ Resets the Vault and Retrospect Machine key, making all encrypted values
        useless.

        :rtype: None

        """

        ok = XbmcWrapper.show_yes_no(LanguageHelper.get_localized_string(LanguageHelper.VaultReset),
                                     LanguageHelper.get_localized_string(LanguageHelper.VaultResetConfirm))
        if not ok:
            Logger.debug("Aborting Reset Vault")
            return

        Logger.info("Resetting the vault to a new initial state.")
        AddonSettings.set_setting(Vault.__APPLICATION_KEY_SETTING, "", store=LOCAL)

        # create a vault instance so we initialize a new one with a new PIN.
        Vault()
        return

    def get_channel_setting(self, channel_guid, setting_id):
        """ Retrieves channel settings for the given channel.

        :param str channel_guid: The channel object to get the channels for.
        :param str setting_id:   The setting to retrieve.

        :return: the configured value.
        :rtype: str
        """

        full_setting_id = "channel_%s_%s" % (channel_guid, setting_id)
        return self.get_setting(full_setting_id)

    def get_setting(self, setting_id):
        """ Retrieves an encrypted setting from the Kodi Add-on Settings.

        :param str setting_id: the ID for the setting to retrieve.

        :return: the decrypted value for the setting.
        :rtype: str
        """

        Logger.info("Decrypting value for setting '%s'", setting_id)
        encrypted_value = AddonSettings.get_setting(setting_id)
        if not encrypted_value:
            Logger.warning("Found empty string as encrypted data")
            return encrypted_value

        try:
            decrypted_value = self.__decrypt(encrypted_value, Vault.__Key)
            if not decrypted_value.startswith(setting_id):
                Logger.error("Invalid decrypted value for setting '%s'", setting_id)
                return None

            decrypted_value = decrypted_value[len(setting_id) + 1:]
            Logger.info("Successfully decrypted value for setting '%s'", setting_id)
        except UnicodeDecodeError:
            Logger.error("Invalid Unicode data returned from decryption. Must be wrong data")
            return None

        return decrypted_value

    def set_setting(self, setting_id, setting_name=None, setting_action_id=None):
        """ Reads a value for a setting from the keyboard and encrypts it in the Kodi
        Add-on settings.

        The settingActionId defaults to <settingId>_set

        :param str setting_id:          The ID for the Kodi Add-on setting to set.
        :param str setting_name:        The name to display in the keyboard.
        :param str setting_action_id:   The name of setting that shows the ***** if an value was
                                         encrypted.

        :rtype: None

        """

        Logger.info("Encrypting value for setting '%s'", setting_id)
        input_value = XbmcWrapper.show_key_board(
            "", LanguageHelper.get_localized_string(
                    LanguageHelper.VaultSpecifySetting
            ) % (setting_name or setting_id,)
        )

        if input_value is None:
            Logger.debug("Setting of encrypted value cancelled.")
            return

        value = "%s=%s" % (setting_id, input_value)
        encrypted_value = self.__encrypt(value, Vault.__Key)

        if setting_action_id is None:
            setting_action_id = "%s_set" % (setting_id,)

        Logger.debug("Updating '%s' and '%s'", setting_id, setting_action_id)
        AddonSettings.set_setting(setting_id, encrypted_value)
        if input_value:
            AddonSettings.set_setting(setting_action_id, "******")
        else:
            AddonSettings.set_setting(setting_action_id, "")
        Logger.info("Successfully encrypted value for setting '%s'", setting_id)
        return

    def __show_howto(self, force=False):
        """ Shows the Vault howto if it was not already shown.

        :param bool force:  Force the howto to show

        :returns: indicator if the howto was shown
        :rtype: bool

        """

        if not force:
            vault_shown = AddonSettings.store(LOCAL).get_boolean_setting(
                Vault.__VAULT_HOWTO_SETTING, default=False)
            if vault_shown:
                return False

        XbmcWrapper.show_text(LanguageHelper.VaultHowToTitle, LanguageHelper.VaultHowToText)
        AddonSettings.store(LOCAL).set_setting(Vault.__VAULT_HOWTO_SETTING, True)
        return True

    def __get_application_key(self):
        """ Gets the decrypted application key that is used for all the encryption.

        :return: The decrypted application key that is used for all the encryption.
        :rtype: bytes

        """

        application_key_encrypted = AddonSettings.get_setting(Vault.__APPLICATION_KEY_SETTING, store=LOCAL)
        # The key was never in the local store the value was None. It was "" if it was reset.
        if application_key_encrypted is None:
            application_key_encrypted = AddonSettings.get_setting(Vault.__APPLICATION_KEY_SETTING, store=KODI)
            if not application_key_encrypted:
                return None

            Logger.info("Moved ApplicationKey to local storage")
            AddonSettings.set_setting(Vault.__APPLICATION_KEY_SETTING, application_key_encrypted, store=LOCAL)

        # Still no application key? Then there was no key!
        if application_key_encrypted == "" or application_key_encrypted is None:
            return None

        vault_incorrect_pin = LanguageHelper.get_localized_string(LanguageHelper.VaultIncorrectPin)
        pin = XbmcWrapper.show_key_board(
            heading=LanguageHelper.get_localized_string(LanguageHelper.VaultInputPin),
            hidden=True)
        if not pin:
            XbmcWrapper.show_notification("", vault_incorrect_pin, XbmcWrapper.Error)
            raise RuntimeError("Incorrect Retrospect PIN specified")
        pin_key = self.__get_pbk(pin)
        application_key = self.__decrypt(application_key_encrypted, pin_key)
        if not application_key.startswith(Vault.__APPLICATION_KEY_SETTING):
            Logger.critical("Invalid Retrospect PIN")
            XbmcWrapper.show_notification("", vault_incorrect_pin, XbmcWrapper.Error)
            raise RuntimeError("Incorrect Retrospect PIN specified")

        application_key_value = application_key[len(Vault.__APPLICATION_KEY_SETTING) + 1:]
        Logger.info("Successfully decrypted the ApplicationKey.")
        if PY2:
            return application_key_value

        # We return bytes on Python 3
        return application_key_value.encode()

    def __encrypt(self, data, key):
        """ Encrypt string data (not bytes) based on the given encryption key (bytes).

        :param str data:    The data to encrypt.
        :param bytes key:   The key to use for encryption.

        :return: The encrypted base64 encoded value.
        :rtype: str

        """

        Logger.debug("Encrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)
        if PY2:
            return base64.b64encode(aes.encrypt(data))
        return base64.b64encode(aes.encrypt(data)).decode()

    def __decrypt(self, data, key):
        """ Decrypts string data (not bytes) using the given encryption key (bytes). The decrypted
        string is returned.

        :param str data:    The data to decrypt.
        :param bytes key:   The key to use for encryption.

        :return: Decrypted value.
        :rtype: str

        """

        Logger.debug("Decrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)

        if PY2:
            return aes.decrypt(base64.b64decode(data))
        return aes.decrypt(base64.b64decode(data)).decode()

    def __get_new_key(self, length=32):
        """ Returns a random key.

        :param int length:  The length of the key.

        :return: A random key of the given length.
        :rtype: bytes

        """

        new_key = ''.join(random.choice(string.digits + string.ascii_letters + string.punctuation)
                          for _ in range(length))
        if PY2:
            return new_key

        # The key is bytes in Py3
        return new_key.encode()

    def __get_pbk(self, pin):
        """ Gets the Password Based Key (PBK) based on the PIN.

        :param str pin: The pin for the key.

        :return: The PBK
        :rtype: bytes

        """

        salt = AddonSettings.get_client_id()
        pbk = pyscrypt.hash(password=pin if PY2 else pin.encode(),
                            salt=salt if PY2 else salt.encode(),
                            N=2 ** 7,  # should be so that Raspberry Pi can handle it
                            # N=1024,
                            r=1,
                            p=1,
                            dkLen=32)
        Logger.trace("Generated PBK with MD5: %s", hashlib.md5(pbk).hexdigest())
        return pbk
