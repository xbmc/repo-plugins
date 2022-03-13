import os
import sys
import json
import urllib.parse
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
        self.lib = os.path.join(self.resources, "lib")
        self.media = os.path.join(self.resources, "media")
        self.icon = self.addon.getAddonInfo("icon")

    def plugin_url(self, params):
        if params:
            return "plugin://{0}?{1}".format(
                self.id, urllib.parse.urlencode(params))
        else:
            return "plugin://{0}".format(self.id)

    def localize(self, *args):
        if len(args) < 1:
            raise ValueError("String id missing")
        elif len(args) == 1:
            string_id = args[0]
            return self.addon.getLocalizedString(string_id)
        else:
            return [self.addon.getLocalizedString(string_id)
                    for string_id in args]

    def log(self, msg):
        xbmc.log(msg, xbmc.LOGDEBUG)

    @staticmethod
    def get_user_input(prompt_msg=""):
        keyboard = xbmc.Keyboard("", prompt_msg)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return ""

        input_str = keyboard.getText()
        return input_str

    def show_settings(self):
        self.addon.openSettings()

    def get_setting(self, setting):
        return self.addon.getSetting(setting).strip()

    def set_setting(self, setting, value):
        self.addon.setSetting(setting, str(value))

    def get_setting_as_bool(self, setting):
        return self.get_setting(setting).lower() == "true"

    def get_setting_as_float(self, setting):
        return float(self.get_setting(setting))

    def get_setting_as_int(self, setting):
        return int(self.get_setting_as_float(setting))


class UserDataHandler():
    filename = "userdata.json"

    def __init__(self):
        self.addon_utils = AddonUtils()
        os.makedirs(self.addon_utils.profile, exist_ok=True)
        self.filepath = os.path.join(
            self.addon_utils.profile, self.filename
        )
        self.load()

    def load(self):
        try:
            with open(self.filepath, "r") as data_file:
                self.userdata_json = json.load(data_file)
        except FileNotFoundError:
            self.userdata_json = {}
            self.save()

    def save(self):
        with open(self.filepath, "w") as data_file:
            json.dump(self.userdata_json, data_file, indent=4)

    def add(self, username, userdata):
        self.userdata_json.update({username: userdata})
        self.save()

    def remove(self, username):
        if username in self.userdata_json:
            self.userdata_json.pop(username)
            self.save()

    def clear(self):
        self.userdata_json = {}
        self.save()

    def get(self, username):
        if username in self.userdata_json:
            return self.userdata_json[username]
        else:
            return None


class SearchHistory():
    filename = "search_history.json"

    def __init__(self, username):
        self.username = username
        self.addon = AddonUtils()
        os.makedirs(self.addon.profile, exist_ok=True)
        self.save_path = os.path.join(self.addon.profile, self.filename)
        self.load()

    def load(self):
        try:
            with open(self.save_path, "r") as history_file:
                self.history_json = json.load(history_file)
                if self.username not in self.history_json:
                    self.history_json[self.username] = []
        except FileNotFoundError:
            self.history_json = {}
            self.history_json[self.username] = []
            self.save()

    def save(self):
        with open(self.save_path, "w") as history_file:
            json.dump(self.history_json, history_file, indent=4)

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
        return self.history_json[self.username]

    def add(self, query):
        queries = self.history_json[self.username]
        if query not in queries:
            queries.insert(0, query)
        self.save()

    def remove(self, query_id):
        del self.history_json[self.username][int(query_id)]
        self.save()

    def clear(self):
        self.history_json[self.username] = []
        self.save()
