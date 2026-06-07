# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.actions import keyword
from resources.lib.actions.addonaction import AddonAction
from resources.lib.actions.actionparser import ActionParser
from resources.lib.actions.folderaction import FolderAction
from resources.lib.actions.videoaction import VideoAction
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config


class OpenShortcutAction(AddonAction):
    def __init__(self, parameter_parser):
        """

        :param ActionParser parameter_parser:  a ActionParser object to is used to parse and
                                                create urls

        """

        super(OpenShortcutAction, self).__init__(parameter_parser)

    def execute(self):
        Logger.debug("Opening shortcut")
        shortcut_name = self.parameter_parser.params[keyword.SHORTCUT]

        # Local import for performance
        from resources.lib.favourites import Favourites
        f = Favourites(Config.shortcutDir)
        item = f.get_shortcut(shortcut_name)
        Logger.info("Found item: %s", item)

        action_url = item.actionUrl
        Logger.debug("Action url: %s", action_url)
        _, params = action_url.split("?", 1)

        # Get the channel
        p = ActionParser(self.parameter_parser.pluginName, self.parameter_parser.handle, params)

        channel_url_id = p.params[keyword.CHANNEL]
        channel_code = p.params[keyword.CHANNEL_CODE]
        channel_register = ChannelIndex.get_register()
        channel = channel_register.get_channel(channel_url_id, channel_code)
        Logger.debug("Found channel for shortcut: %s", channel)

        if item.is_playable:
            action = VideoAction(p, channel)
        else:
            action = FolderAction(p, channel)
        action.execute()
