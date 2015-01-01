__author__ = 'bromix'


class AbstractSystemVersion(object):
    def __init__(self, major, minor, name):
        self._major = major
        self._minor = minor
        self._name = name
        pass

    def __del__(self):
        pass

    def get_name(self):
        return self._name

    def get_major(self):
        return self._major

    def get_minor(self):
        return self._minor

    pass
