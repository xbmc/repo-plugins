# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.actions.addonaction import AddonAction
from resources.lib.chn_class import Channel
from resources.lib.logger import Logger
from resources.lib.actions.actionparser import ActionParser
from resources.lib.regexer import Regexer


class ExecuteAction(AddonAction):
    __command: str
    __channel: Channel

    def __init__(self, parameter_parser, channel, command):
        """ Peforms the action from a custom contextmenu

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param Channel channel:                The channel info for the channel
        :param str command:                    The name of the method to call

        """

        super(ExecuteAction, self).__init__(parameter_parser)

        # Make sure we can just do a method call on the channel, not some other stuff.
        if not Regexer.do_regex(r"^[a-zA-Z_]+$", command):
            raise ValueError(f"Invalid command: {command}")

        self.command = command
        self.channel = channel

    def execute(self):
        # invoke the call
        function_string = "self.channel.%s()" % (self.command,)
        Logger.debug("Calling '%s'", function_string)
        try:
            # noinspection PyRedundantParentheses
            exec(function_string)  # NOSONAR We just need this here.
        except:
            Logger.error("action-execute-command :: Cannot execute '%s'.", function_string,
                         exc_info=True)
        return
