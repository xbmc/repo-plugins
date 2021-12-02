import os
import sys
import xbmc
import xbmcaddon
import xbmcvfs


class AddonUtils():

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.id = self.addon.getAddonInfo("id")
        self.name = self.addon.getAddonInfo("name")
        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])

        self.path = xbmcvfs.translatePath(self.addon.getAddonInfo("path"))
        self.profile = xbmcvfs.translatePath(self.addon.getAddonInfo("profile"))
        self.resources = os.path.join(self.path, "resources")
        self.media = os.path.join(self.resources, "media")

    def localize(self, *args):
        if len(args) < 1:
            raise ValueError("String id missing")
        elif len(args) == 1:
            string_id = args[0]
            return self.addon.getLocalizedString(string_id)
        else:
            return [self.addon.getLocalizedString(string_id) for string_id in args]

    @staticmethod
    def get_user_input(prompt_msg=""):
        keyboard = xbmc.Keyboard("", prompt_msg)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return ""

        input_str = keyboard.getText()
        return input_str
