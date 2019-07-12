#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import pyaes        #: Pure Python AES
import pyscrypt     #: Pure Python SCrypt
import base64
import random
import string
import hashlib

from backtothefuture import PY2
from logger import Logger
from addonsettings import AddonSettings, LOCAL, KODI
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper


class Vault(object):
    __Key = None
    __APPLICATION_KEY_SETTING = "application_key"

    def __init__(self):
        """ Creates a new instance of the Vault class """

        self.__newKeyGeneratedInConstructor = False    # : This was the very first time a key was generated

        # ask for PIN of no key is present
        if Vault.__Key is None:
            key = self.__get_application_key()

            # was there a key? No, let's initialize it.
            if key is None:
                Logger.warning("No Application Key present. Intializing a new one.")
                key = self.__get_new_key()
                if not self.change_pin(key):
                    raise RuntimeError("Error creating Application Key.")
                Logger.info("Created a new Application Key with MD5: %s (lengt=%s)",
                            hashlib.md5(key).hexdigest(), len(key))
                self.__newKeyGeneratedInConstructor = True

            Vault.__Key = key
            Logger.trace("Using Application Key with MD5: %s (lengt=%s)", hashlib.md5(key).hexdigest(), len(key))

    def change_pin(self, application_key=None):
        """ Stores an existing ApplicationKey using a new PIN.

        :param str application_key: an existing ApplicationKey that will be stored. If none
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

        encrypted_key = "%s=%s" % (self.__APPLICATION_KEY_SETTING, application_key)

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
        """ Reads a value for a setting from the keyboard and encryptes it in the Kodi
        Add-on settings.

        The setttingActionId defaults to <settingId>_set

        :param str setting_id:          The ID for the Kodi Add-on setting to set.
        :param str setting_name:        The name to display in the keyboard.
        :param str setting_action_id:   The name of the action that was called.

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

    def __get_application_key(self):
        """ Gets the decrypted application key that is used for all the encryption.

        :return: The decrypted application key that is used for all the encryption.
        :rtype: str

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
        return application_key_value

    def __encrypt(self, data, key):
        """ Encrypt data based on the given encryption key.

        :param str data:    The data to encrypt.
        :param str key:     The key to use for encryption.

        :return: The encrypted base64 encoded value.
        :rtype: str

        """

        Logger.debug("Encrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)
        if PY2:
            return base64.b64encode(aes.encrypt(data))
        return base64.b64encode(aes.encrypt(data).encode())

    def __decrypt(self, data, key):
        """ Decrypts data based on the given encryption key.

        :param str data:    The data to decrypt.
        :param str key:     The key to use for encryption.

        :return: Decrypted value.
        :rtype: str

        """

        Logger.debug("Decrypting with keysize: %s", len(key))
        aes = pyaes.AESModeOfOperationCTR(key)

        if PY2:
            return aes.decrypt(base64.b64decode(data))
        return aes.decrypt(base64.b64decode(data.encode()))

    def __get_new_key(self, length=32):
        """ Returns a random key.

        :param int length:  The lenght of the key.

        :return: A random key of the given length.
        :rtype: str

        """

        return ''.join(random.choice(string.digits + string.ascii_letters + string.punctuation)
                       for _ in range(length))

    def __get_pbk(self, pin):
        """ Gets the Password Based Key (PBK) based on the PIN.

        :param str pin: The pin for the key.

        :return: The PBK
        :rtype: str

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
