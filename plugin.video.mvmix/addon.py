# -*- coding: utf-8 -*-

import sys
import urlparse
from resources.lib.common import Common
from resources.lib.parser import Parser

handle_ = int(sys.argv[1])
url_ = sys.argv[0]

plugin = Common(
    addon_handle=handle_,
    addon_url=url_
)
parser = Parser(plugin)

def router(paramstring):
    args = dict(urlparse.parse_qs(paramstring))
    mode = args.get('mode', ['home'])[0]
    title = args.get('title', [''])[0]
    artist = args.get('artist', [''])[0]
    thumb = args.get('thumb', [''])[0]
    site = args.get('site', [''])[0]
    id_ = args.get('id', [''])[0]
    params = args.get('params', [''])[0]

    if mode == 'home':
        parser.home_items()
    elif mode == 'fm_search':
        parser.fm_artists_items()
    elif mode == 'list_local_artists':
        parser.local_artists_items()
    elif mode == 'list_artist_videos':
        parser.artist_video_items(artist, params, thumb)
    elif mode == 'play_artists':
        parser.play_artists()
    elif mode == 'play':
        parser.play(artist, params, thumb)
    elif mode == 'queue_video':
        parser.queue_video(title, thumb, params)
    elif mode == 'play_video':
        parser.play_video(title, site, id_)
    elif mode == 'hide_video':
        parser.hide_video(site, id_)
    elif mode == 'remove_artist':
        parser.remove_artist(artist)
    else:
        sys.exit(0)

if __name__ == '__main__':
    router(sys.argv[2][1:])
