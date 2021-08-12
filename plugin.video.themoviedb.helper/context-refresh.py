# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from resources.lib.script.router import refresh_details
from json import loads

if __name__ == '__main__':
    refresh_details(**loads(sys.listitem.getProperty('tmdbhelper.context.refresh')))
