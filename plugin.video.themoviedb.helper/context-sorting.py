# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from resources.lib.script.router import sort_list
from json import loads

if __name__ == '__main__':
    sort_list(**loads(sys.listitem.getProperty('tmdbhelper.context.sorting')))
