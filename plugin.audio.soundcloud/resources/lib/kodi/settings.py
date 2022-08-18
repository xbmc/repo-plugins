class Settings:

    AUDIO_FORMATS = {
        "0": {
            "mime_type": "audio/ogg; codecs=\"opus\"",
            "protocol": "hls",
        },
        "1": {
            "mime_type": "audio/mpeg",
            "protocol": "hls",
        },
        "2": {
            "mime_type": "audio/mpeg",
            "protocol": "progressive",
        }
    }

    APIV2_LOCALE = {
        "auto": "0",
        "disabled": "1"
    }

    def __init__(self, addon):
        self.addon = addon

    def get(self, id):
        return self.addon.getSetting(id)

    def set(self, id, value):
        return self.addon.setSetting(id, value)
