class Settings:

    VIDEO_FORMAT = {
        "HLS (Adaptive)": "application/x-mpegURL",
        "1080p": "H264:720",  # 1080p resolution is not available anymore in brightcove player
        "720p": "H264:720",
        "360p": "H264:360",
    }

    def __init__(self, addon):
        self.addon = addon

    def get(self, setting_id):
        return self.addon.getSetting(setting_id)

    def set(self, setting_id, value):
        return self.addon.setSetting(setting_id, value)
