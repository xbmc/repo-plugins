# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from resources.lib.script import Script

if __name__ == '__main__':
    TMDbScript = Script()
    TMDbScript.get_params()
    TMDbScript.router()
