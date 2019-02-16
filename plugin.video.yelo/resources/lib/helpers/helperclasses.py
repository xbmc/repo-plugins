class Credentials:
    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self.reload()

    def are_filled_in(self):
        return not (self.username is None or self.password is None or self.username == '' or self.password == '')

    def reload(self):
        self.username = self._kodi_wrapper.get_setting('username')
        self.password = self._kodi_wrapper.get_setting('password')


class PostalCode:
    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self.reload()

    def are_filled_in(self):
        return False if int(self.postal_code) == 0 else True

    def reload(self):
        self.postal_code = self._kodi_wrapper.get_setting('postal')

class BitRate:
    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self.reload()

    def reload(self):
        self.bitrate = self._kodi_wrapper.get_setting('bitrate')
