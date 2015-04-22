__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.youtube.helper import utils


def my_subscriptions_to_items(provider, context, json_data):
    result = []
    video_id_dict = {}

    items = json_data.get('items', [])
    for item in items:
        video_id = item['id']
        video_item = utils.make_video_item_from_json_data(context, provider, item)
        result.append(video_item)

        video_id_dict[video_id] = video_item
        pass

    channel_item_dict = {}
    utils.update_video_infos(provider, context, video_id_dict, channel_items_dict=channel_item_dict)
    utils.update_fanarts(provider, context, channel_item_dict)

    # next page
    continuations = json_data.get('continuations', '')
    if continuations:
        new_params = {}
        new_params.update(context.get_params())
        new_params['continuations'] = continuations

        new_context = context.clone(new_params=new_params)

        current_page = int(new_context.get_param('page', 1))
        next_page_item = kodion.items.NextPageItem(new_context, current_page, fanart=provider.get_fanart(new_context))
        result.append(next_page_item)
        pass

    return result
