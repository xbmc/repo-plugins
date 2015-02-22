__author__ = 'bromix'

import xbmc
import re
from ..abstract_system_version import AbstractSystemVersion


class XbmcSystemVersion(AbstractSystemVersion):
    def __init__(self):
        major = 0
        minor = 0
        try:
            version_str = str(xbmc.__version__)
            version_match = re.match('^(?:(?P<major>\d+)\.)?(?:(?P<minor>\d+)\.)?(?P<edition>\*|\d+)$', version_str)
            if version_match:
                major = int(version_match.group('major'))
                minor = int(version_match.group('minor'))
                pass
        except:
            pass

        name = 'Unknown XBMC System'
        if major == 1 and minor >= 4:
            name = 'Frodo'
            pass
        elif major == 2:
            if minor == 0:
                name = 'Frodo'
                pass

            if minor > 0:
                name = 'Gotham'
                pass

            if minor > 14:
                name = 'Helix'
                pass
            pass

        AbstractSystemVersion.__init__(self, major, minor, name)
        pass

    pass