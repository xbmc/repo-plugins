__author__ = 'bromix'

import re

from resources.lib import kodion
from resources.lib.kodion import items
from . import utils


def response_to_items(provider, context, json_data):
    video_id_dict = {}
    channel_item_dict = {}

    result = []

    feed = json_data.get('feed', None)
    if feed:
        entry = feed.get('entry', [])
        for item in entry:
            video_id = ''
            video_id_match = re.match('tag:youtube.com,(\d+):video:(?P<video_id>.*)', item['id']['$t'])
            if video_id_match:
                video_id = video_id_match.group('video_id')
                pass
            title = item['title']['$t']

            video_item = items.VideoItem(title,
                                         context.create_uri(['play'], {'video_id': video_id}))
            video_item.set_fanart(provider.get_fanart(context))
            result.append(video_item)

            video_id_dict[video_id] = video_item
            channel_id = item['media$group']['yt$uploaderId']['$t']
            if not channel_id in channel_item_dict:
                channel_item_dict[channel_id] = []
            channel_item_dict[channel_id].append(video_item)
            pass

        utils.update_video_infos(provider, context, video_id_dict)
        utils.update_channel_infos(provider, context, channel_item_dict)

        page = int(context.get_param('page', 1))
        items_per_page = int(feed.get('openSearch$itemsPerPage', {}).get('$t', 0))
        total = int(feed.get('openSearch$totalResults', {}).get('$t', 0))
        if page*items_per_page < total:
            new_params = {}
            new_params.update(context.get_params())
            new_params['start-index'] = (page*items_per_page)+1

            new_context = context.clone(new_params=new_params)

            current_page = int(new_context.get_param('page', 1))
            next_page_item = items.NextPageItem(new_context, current_page, fanart=provider.get_fanart(new_context))
            result.append(next_page_item)
            pass
        pass
    else:
        raise kodion.KodionException("Couldn't find feed")

    return result
