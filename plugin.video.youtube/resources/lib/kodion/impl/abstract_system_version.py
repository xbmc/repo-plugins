__author__ = 'bromix'


class AbstractSystemVersion(object):
    def __init__(self, major, minor, name):
        self._major = major
        if not self._major or not isinstance(major, int):
            self._major = 0
            pass

        self._minor = minor
        if not self._minor or not isinstance(minor, int):
            self._minor = 0
            pass

        self._name = name
        if not self._name or not isinstance(name, basestring):
            self._name = 'UNKNOWN'
            pass
        pass

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        obj_str = "%s (%d.%d)" % (self._name, self._major, self._minor)
        return obj_str

    def get_name(self):
        return self._name

    def get_major(self):
        return self._major

    def get_minor(self):
        return self._minor

    pass
