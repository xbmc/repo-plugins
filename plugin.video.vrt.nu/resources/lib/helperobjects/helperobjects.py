class TitleItem:

    def __init__(self, title, url_dictionary, is_playable, thumbnail = None, video_dictionary=None):
        self.title = title
        self.url_dictionary = url_dictionary
        self.is_playable = is_playable
        self.thumbnail = thumbnail
        self.video_dictionary = video_dictionary

class StreamURLS:

    def __init__(self, stream_url, subtitle_url=None, license_key=None):
        self.stream_url = stream_url
        self.subtitle_url = subtitle_url
        self.license_key = license_key


class Credentials:

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self.reload()

    def are_filled_in(self):
        return not (self.username is None or self.password is None or self.username == '' or self.password == '')

    def reload(self):
        self.username = self._kodi_wrapper.get_setting('username')
        self.password = self._kodi_wrapper.get_setting('password')

