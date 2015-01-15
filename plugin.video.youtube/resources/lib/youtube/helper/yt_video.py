__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.youtube.helper import v3


def _process_rate_video(provider, context, re_match):
    video_id = context.get_param('video_id', '')
    if not video_id:
        raise kodion.KodionException('video/rate: missing video_id')

    client = provider.get_client(context)
    json_data = client.get_video_rating(video_id)
    if not v3.handle_error(provider, context, json_data):
        return False

    items = json_data.get('items', [])
    if items:
        current_rating = items[0].get('rating', '')
        ratings = ['like', 'dislike', 'none']
        rating_items = []
        for rating in ratings:
            if rating != current_rating:
                rating_items.append((context.localize(provider.LOCAL_MAP['youtube.video.rate.%s' % rating]), rating))
                pass
            pass
        result = context.get_ui().on_select(context.localize(provider.LOCAL_MAP['youtube.video.rate']), rating_items)
        if result != -1:
            client = provider.get_client(context).rate_video(video_id, result)

            # this will be set if we are in the 'Liked Video' playlist
            if context.get_param('refresh_container', '0') == '1':
                context.get_ui().refresh_container()
                pass
            pass
        pass
    pass


def process(method, provider, context, re_match):
    if method == 'rate':
        return _process_rate_video(provider, context, re_match)
    else:
        raise kodion.KodionException("Unknown method '%s'" % method)

    return True
