# -*- coding: utf-8 -*-
# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import resources.lib.context as context

arg = sys.argv[1]

if arg == 'play':
    context.action('play')
elif arg == 'open':
    context.action('open')
elif arg == 'watchlist':
    context.action('watchlist')
elif arg == 'collection':
    context.action('collection')
elif arg == 'history':
    context.action('history')
elif arg == 'library':
    context.action('library')
elif arg == 'library_userlist':
    context.action('library_userlist')
elif arg == 'add_to_userlist':
    context.action('add_to_userlist')
elif arg == 'remove_from_userlist':
    context.action('remove_from_userlist')
elif arg == 'refresh_item':
    context.action('refresh_item')
