# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.actions import keyword
from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.actions import action


class VaultAction(AddonAction):
    def __init__(self, parameter_parser, vault_action):
        """ Displays the channels that are currently available in XOT as a directory
        listing.

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param str vault_action:               The action to perform in the vault

        """

        super(VaultAction, self).__init__(parameter_parser)

        self.vault_action = vault_action
        self.params = self.parameter_parser.params

    def execute(self):
        try:
            # Import vault here, as it is only used here or in a channel
            # that supports it
            from resources.lib.vault import Vault

            if self.vault_action == action.RESET_VAULT:
                Vault.reset()
                return

            v = Vault()
            if self.vault_action == action.SET_ENCRYPTION_PIN:
                v.change_pin()
            elif self.vault_action == action.SET_ENCRYPTED_VALUE:
                v.set_setting(self.params[keyword.SETTING_ID],
                              self.params.get(keyword.SETTING_NAME, ""),
                              self.params.get(keyword.SETTING_ACTION_ID, None))
        finally:
            if keyword.SETTING_TAB_FOCUS in self.params:
                AddonSettings.show_settings(
                    self.params[keyword.SETTING_TAB_FOCUS],
                    self.params.get(keyword.SETTING_FOCUS, None)
                )
