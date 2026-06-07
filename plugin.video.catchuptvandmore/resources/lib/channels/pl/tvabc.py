# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

import json
import urlquick

from codequick import Resolver

from resources.lib import web_utils


URL_API = 'https://krainaabc.tvp.pl/sess/TVPlayer2/api.php'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    channel_code = {
        'tvpabc': '442',
        'tvpabc2': '4O1',
    }
    channel_identity = {
        'tvabc': '51696812',
        'tvabc2': '57181933'
    }

    params = {
        '@method': 'getTvpConfig',
        '@callback': '__anthill_jsonp_%s__' % channel_code[item_id],
        'corsHost': 'krainaabc.tvp.pl',
        'id': channel_identity[item_id]
    }

    resp = urlquick.get(URL_API, params=params, headers=GENERIC_HEADERS, max_age=-1, timeout=30)

    # extract json content from jsonp reply
    resp_json_body = resp.text.split("(", 1)[1]
    resp_json_body = resp_json_body[:1 + resp_json_body.rfind("}")]
    # parse json
    resp_json = json.loads(resp_json_body)

    video_files = resp_json.get('content').get('files')
    for video_file in video_files:
        if 'hls' == video_file.get('type'):
            return video_file.get('url')
    default_url = video_files[0].get('url')
    if default_url is not None:
        return default_url

    return False
