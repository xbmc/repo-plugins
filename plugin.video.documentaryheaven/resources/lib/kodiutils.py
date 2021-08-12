import os
import sys
import json
import xbmc
import xbmcaddon
import xbmcvfs


class AddonInfo():

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
        self.search_history = SearchHistory(self.profile)


    def localize(self, string_id):
        return self.addon.getLocalizedString(string_id)


    @staticmethod
    def get_user_input(prompt_msg=""):
        keyboard = xbmc.Keyboard("", prompt_msg)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return ""

        input_str = keyboard.getText()
        return input_str


class SearchHistory():
    filename = "search_history.json"


    def __init__(self, profile):
        os.makedirs(profile, exist_ok=True)
        self.save_path = os.path.join(profile, self.filename)
        self.load()


    def load(self):
        try:
            with open(self.save_path, "r") as history_file:
                self.history_json = json.load(history_file)
        except FileNotFoundError:
            self.history_json = {}
            self.history_json["queries"] = []
            self.save()


    def save(self):
        with open(self.save_path, "w") as history_file:
            json.dump(self.history_json, history_file)


    def get(self, query_id):
        return self.get_queries()[int(query_id)]


    def get_id(self, query, reload_data=False):
        if reload_data:
            self.load()

        try:
            return self.get_queries().index(query)
        except ValueError:
            return None


    def get_queries(self):
        return self.history_json["queries"]


    def add(self, query):
        queries = self.history_json["queries"]
        if query not in queries:
            queries.insert(0, query)
        self.save()


    def remove(self,  query_id):
        del self.history_json["queries"][int(query_id)]
        self.save()


    def clear(self):
        self.history_json["queries"] = []
        self.save()
