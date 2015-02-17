__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.youtube.helper import v2, v3


def _process_related_videos(provider, context, re_match):
    result = []

    provider.set_content_type(context, kodion.constants.content_type.EPISODES)

    page_token = context.get_param('page_token', '')
    video_id = context.get_param('video_id', '')
    if video_id:
        json_data = provider.get_client(context).get_related_videos(video_id=video_id, page_token=page_token)
        result.extend(v3.response_to_items(provider, context, json_data, process_next_page=False))
        pass

    return result


def _process_popular_right_now(provider, context, re_match):
    provider.set_content_type(context, kodion.constants.content_type.EPISODES)

    result = []

    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_popular_videos(page_token=page_token)
    result.extend(v3.response_to_items(provider, context, json_data))

    return result


def _process_browse_channels(provider, context, re_match):
    result = []

    page_token = context.get_param('page_token', '')
    guide_id = context.get_param('guide_id', '')
    if guide_id:
        json_data = provider.get_client(context).get_guide_category(guide_id)
        result.extend(v3.response_to_items(provider, context, json_data))
        pass
    else:
        json_data = provider.get_client(context).get_guide_categories()
        result.extend(v3.response_to_items(provider, context, json_data))
        pass

    return result


def _process_new_uploaded_videos(provider, context, re_match):
    provider.set_content_type(context, kodion.constants.content_type.EPISODES)

    result = []
    start_index = int(context.get_param('start-index', 0))
    json_data = provider.get_client(context).get_uploaded_videos_of_subscriptions(start_index)
    result.extend(v2.response_to_items(provider, context, json_data))

    return result


def _process_disliked_videos(provider, context, re_match):
    result = []

    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_disliked_videos(page_token=page_token)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data))
    return result


def _process_live_events(provider, context, re_match):
    def _sort(x):
        return x.get_aired()

    provider.set_content_type(context, kodion.constants.content_type.EPISODES)

    result = []

    # TODO: cache result
    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_live_events(event_type='live', page_token=page_token)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data, sort=_sort, reverse_sort=True))

    return result


def process(category, provider, context, re_match):
    result = []

    if category == 'related_videos':
        result.extend(_process_related_videos(provider, context, re_match))
        pass
    elif category == 'popular_right_now':
        result.extend(_process_popular_right_now(provider, context, re_match))
        pass
    elif category == 'browse_channels':
        result.extend(_process_browse_channels(provider, context, re_match))
        pass
    elif category == 'new_uploaded_videos':
        result.extend(_process_new_uploaded_videos(provider, context, re_match))
        pass
    elif category == 'disliked_videos':
        result.extend(_process_disliked_videos(provider, context, re_match))
        pass
    elif category == 'live':
        result.extend(_process_live_events(provider, context, re_match))
        pass
    else:
        raise kodion.KodionException("YouTube special category '%s' not found" % category)

    return result
