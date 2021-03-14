# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from resources.lib.kodi.library import add_to_library
from json import loads

if __name__ == '__main__':
    add_to_library(**loads(sys.listitem.getProperty('tmdbhelper.context.addlibrary')))
