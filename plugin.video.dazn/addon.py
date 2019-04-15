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
    args = dict(urlparse.parse_qs(paramstring))
    mode = args.get('mode', ['rails'])[0]
    title = args.get('title', [''])[0]
    id_ = args.get('id', ['home'])[0]
    params = args.get('params', [''])[0]
    verify_age = True if args.get('verify_age', [''])[0] == 'True' else False

    if mode == 'rails':
        parser.rails_items(client.rails(id_, params), id_)
    elif 'rail' in mode:
        parser.rail_items(client.rail(id_, params), mode)
    elif 'epg' in mode:
        date = params
        if id_ == 'date':
            date = plugin.get_date()
        parser.epg_items(client.epg(date), date, mode)
    elif mode == 'play':
        parser.playback(client.playback(id_, plugin.youth_protection_pin(verify_age)))
    elif mode == 'play_context':
        parser.playback(client.playback(id_, plugin.youth_protection_pin(verify_age)), title, True)
    elif mode == 'logout':
        if plugin.logout():
            client.signOut()
            sys.exit(0)
    elif mode == 'is_settings':
        plugin.open_is_settings()
    else:
        sys.exit(0)

if __name__ == '__main__':
    if plugin.startup or not client.TOKEN:
        playable = plugin.start_is_helper()
        client.DEVICE_ID = plugin.uniq_id()
        if client.DEVICE_ID and playable:
            client.startUp()
            if client.TOKEN:
                plugin.set_setting('startup', 'false')
                client.userProfile()
        else:
            client.TOKEN = ''

    if client.TOKEN and client.DEVICE_ID:
        router(sys.argv[2][1:])
    else:
        sys.exit(0)
