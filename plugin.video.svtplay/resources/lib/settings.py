from __future__ import absolute_import,unicode_literals
from resources.lib import logging

class Settings:

    def __init__(self, addon):
        self.addon = addon
        self.geo_restriction = self.__get_setting("hideonlysweden")
        self.alpha_program_listing = self.__get_setting("alpha")
        self.inappropriate_for_children = self.__get_setting("inappropriateForChildren")
        self.show_subtitles = self.__get_setting("showsubtitles")
        self.kids_mode = self.__get_setting("kidsmode")
        logging.log("Current settings: {}".format(vars(self)))

    def __get_setting(self, setting):
        return self.addon.getSetting(setting) == "true"
