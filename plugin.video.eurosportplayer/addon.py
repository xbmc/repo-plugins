# -*- coding: utf-8 -*-

import sys
import urlparse
from resources.lib.common import Common
from resources.lib.client import Client
from resources.lib.parser import Parser

handle_ = int(sys.argv[1])
url_ = sys.argv[0]

plugin = Common(
    addon_handle=handle_,
    addon_url=url_
)
client = Client(plugin)
parser = Parser(plugin)

def router(paramstring):
    args = dict(urlparse.parse_qs(sys.argv[2][1:]))
    mode = args.get('mode', ['root'])[0]
    id_ = args.get('id', [''])[0]
    params = args.get('params', [''])[0]

    if mode == 'root':
        parser.channel(client.channels())
    elif mode == 'sports':
        parser.sport(client.categories())
    elif mode == 'all_sports':
        parser.all_sports(client.category_all())
    elif mode == 'events':
        parser.events(client.events())
    elif mode == 'event':
        parser.event(client.event(id_))
    elif mode == 'videos':
        parser.video(client.videos(id_), id_)
    elif 'epg' in mode:
        prev_date = params
        date = id_
        if date == 'date':
            prev_date, date = plugin.get_date()
        parser.epg(client.epg(prev_date, date), prev_date, date)
    elif mode == 'play':
        if id_:
            parser.play(client.streams(id_))
    elif mode == 'license_renewal':
        parser.license_renewal(client.license_key())
    elif mode == 'is_settings':
        plugin.open_is_settings()

if __name__ == '__main__':
    if plugin.startup:
        playable = plugin.start_is_helper()
        client.DEVICE_ID = plugin.uniq_id()
        if client.DEVICE_ID and playable:
            client.refresh_token()
            if client.ACCESS_TOKEN:
                plugin.set_setting('startup', 'false')
        else:
            client.ACCESS_TOKEN = ''

    if client.ACCESS_TOKEN and client.DEVICE_ID:
        router(sys.argv[2][1:])
