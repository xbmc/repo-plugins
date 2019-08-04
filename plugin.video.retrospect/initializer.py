#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import os.path
import sys
from datetime import datetime


class Initializer:
    StartTime = datetime.now()  # : Used for duration determinination

    def __init__(self):
        """ It is a static method, so we con't get here """
        raise NotImplementedError("Static class only")

    @staticmethod
    def set_unicode():
        """Forces the environment to UTF-8"""

        if sys.version_info[0] > 2:
            return

        # noinspection PyUnresolvedReferences,PyCompatibility
        reload(sys)
        # noinspection PyUnresolvedReferences
        sys.setdefaultencoding("utf-8")  # @UndefinedVariable
        return

    @staticmethod
    def setup_python_paths():

        # Get the path we are in
        try:
            import xbmcaddon
            addon = xbmcaddon.Addon()
            path = addon.getAddonInfo('path')
        except:
            path = os.getcwd()

        if isinstance(path, bytes):
            # the Kodi libs return unicode encoded info, so we need to decode this back to string
            # noinspection PyArgumentEqualDefault
            path = path.decode('utf-8')

        # insert the path at the start to prevent other lib-add-ons to steal our class names
        sys.path.insert(0, os.path.join(path.replace(";", ""), 'resources', 'libs'))
        return path


if __name__ == "__main__":
    init = Initializer.setup_python_paths()
