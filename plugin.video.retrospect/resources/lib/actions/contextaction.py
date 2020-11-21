# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.actions.addonaction import AddonAction
from resources.lib.chn_class import Channel
from resources.lib.logger import Logger
from resources.lib.actions.actionparser import ActionParser


class ContextMenuAction(AddonAction):
    def __init__(self, parameter_parser, channel, action):
        """ Peforms the action from a custom contextmenu

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param Channel channel:                The channel info for the channel
        :param str action:                     The name of the method to call

        """

        super(ContextMenuAction, self).__init__(parameter_parser)

        self.__channel = channel
        self.__media_item = parameter_parser.media_item
        self.__action = action

    def execute(self):
        Logger.debug("Performing Custom Contextmenu command: %s", self.__action)

        item = self.__media_item
        if not item.complete:
            Logger.debug("The contextmenu action requires a completed item. Updating %s", item)
            item = self.__channel.process_video_item(item)

            if not item.complete:
                Logger.warning(
                    "update_video_item returned an item that had item.complete = False:\n%s", item)

        # invoke the call
        function_string = "returnItem = channel_object.%s(item)" % (self.__action,)
        Logger.debug("Calling '%s'", function_string)
        try:
            # noinspection PyRedundantParentheses
            exec(function_string)  # NOSONAR We just need this here.
        except:
            Logger.error("on_action_from_context_menu :: Cannot execute '%s'.", function_string,
                         exc_info=True)
        return
