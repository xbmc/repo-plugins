# -*- coding: utf-8 -*-
import sys
from resources.lib.sito import plugin
from resources.lib.views import custom_action, check_update

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'custom_action':
        custom_action(sys.argv)
    else:
        check_update(force=False)
        plugin.run()
