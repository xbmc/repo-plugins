import os, json

class Settings:

    def __init__(self):
        try:
            import xbmc, xbmcaddon
            base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        except:
            base = os.getcwd()
        self.SETTINGS_FILE = os.path.join(base, 'settings.json')

    @staticmethod
    def instance():
        return Settings()


    def getSettingsFile(self):
        return self.SETTINGS_FILE


    def store(self, provider, key, stuff):
        # load
        try:
            fp = open(self.SETTINGS_FILE, 'r')
            settings = json.load(fp)
            fp.close()
        except:
            settings = {}

        if not provider in settings:
            settings[provider] = {}
        # update
        settings[provider][key] =stuff

        # save
        fp = open(self.SETTINGS_FILE, 'w')
        json.dump(settings, fp)
        fp.close()

        return True


    def get(self, provider):
        # load
        try:
            fp = open(self.SETTINGS_FILE, 'r')
            settings = json.load(fp)
            fp.close()
        except:
            return None

        if provider in settings.keys():
            return settings[provider]

        return None
