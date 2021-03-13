# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from resources.lib.script.router import manage_artwork
from json import loads

if __name__ == '__main__':
    manage_artwork(**loads(sys.listitem.getProperty('tmdbhelper.context.artwork')))
