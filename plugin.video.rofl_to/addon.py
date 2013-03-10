from xbmcswift2 import Plugin, xbmc
from resources.lib.api import RoflApi, NetworkError

plugin = Plugin()


STRINGS = {
    'page': 30000,
    'category': 30001,
    'all': 30002,
}


@plugin.route('/')
def show_root():
    sort_methods = rofl_api.get_sort_methods()
    items = [{
        'label': sort_method.get('title'),
        'path': plugin.url_for(
            'show_videos',
            sort_method=sort_method['path'],
            category='all',
            page='1',
        ),
    } for sort_method in sort_methods]
    return plugin.finish(items)


@plugin.route('/<sort_method>/')
def show_categories(sort_method):
    categories = rofl_api.get_categories()
    items = [{
        'label': category.get('title'),
        'path': plugin.url_for(
            'show_videos',
            sort_method=sort_method,
            category=category.get('path'),
            page='1',
        ),
    } for category in categories]
    return plugin.finish(items, update_listing=True)


@plugin.route('/<sort_method>/<category>/<page>/')
def show_videos(sort_method, category, page):
    videos, has_next_page = rofl_api.get_videos(
        sort_method=sort_method,
        category=category,
        page=page,
    )

    items = []
    items.append({
        'label': '[[ %s: %s ]]' % (_('category'), _(category)),
        'path': plugin.url_for(
            'show_categories',
            sort_method=sort_method,
        ),
    })
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.append({
            'label': '<< %s %s <<' % (_('page'), prev_page),
            'path': plugin.url_for(
                'show_videos',
                sort_method=sort_method,
                category=category,
                page=prev_page,
            ),
        })

    items.extend([{
        'label': video.get('title'),
        'thumbnail': video.get('thumb'),
        'path': plugin.url_for(
            'play_video',
            video_id=video['video_id'],
        ),
        'stream_info': {
            'video': {'duration': video['duration']},
        },
        'is_playable': True,
    } for video in videos])

    if has_next_page:
        next_page = str(int(page) + 1)
        items.append({
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                'show_videos',
                sort_method=sort_method,
                category=category,
                page=next_page,
            ),
        })

    update_listing = int(page) > 1 or category != 'all'
    return plugin.finish(items, update_listing=update_listing)


@plugin.route('/play/<video_id>')
def play_video(video_id):
    playback_url = rofl_api.get_video_url(video_id)
    return plugin.set_resolved_url(playback_url)


def get_language():
    xbmc_language = xbmc.getLanguage().lower()
    log('xbmc_language=%s' % xbmc_language)
    if xbmc_language.startswith('english'):
        lang = 'en'
    elif xbmc_language.startswith('german'):
        lang = 'de'
    else:
        lang = 'en'
    return lang


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id)
        return string_id


def log(msg):
    plugin.log.info('%s addon: %s' % (__name__, msg))


if __name__ == '__main__':
    rofl_api = RoflApi(get_language())
    try:
        plugin.run()
    except NetworkError:
        log('NetworkError')
