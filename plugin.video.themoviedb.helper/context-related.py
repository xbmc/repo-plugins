# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from resources.lib.script.router import related_lists
from json import loads

if __name__ == '__main__':
    related_lists(**loads(sys.listitem.getProperty('tmdbhelper.context.related')))
