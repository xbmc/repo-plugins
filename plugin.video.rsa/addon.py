from xbmcswift2 import Plugin

from resources.lib import rsa

plugin = Plugin()


@plugin.route('/')
def index():
    items = [{
        'label': plugin.get_string(30000),
        'path': plugin.url_for('rsa_videos', page_no=1)
    }, {
        'label': plugin.get_string(30001),
        'path': plugin.url_for('rsa_animate')
    }, {
        'label': plugin.get_string(30002),
        'path': plugin.url_for('rsa_shorts')
    }]

    return items


@plugin.route('/rsa_animate')
def rsa_animate():
    """
    Get RSA Animate videos from the RSA module and send to XBMC
    """
    items = []

    video_list = rsa.get_rsa_animate_videos()
    for video in video_list:
        items.append({
            'label': video['title'],
            'path': plugin.url_for('play_video', url=video['url']),
            'thumbnail': video['thumbnail'],
            'is_playable': True
        })

    if video_list:
        items.append({
            'label': 'Next Page',
            'path': plugin.url_for('rsa_animate')
        })

    return items


@plugin.route('/rsa_videos/<page_no>')
def rsa_videos(page_no):
    """
    Get videos from RSA module and send to XBMC
    """
    items = []
    page_no = int(page_no)

    video_list = rsa.get_videos(page_no)
    for video in video_list:
        items.append({
            'label': video['title'],
            'path': plugin.url_for('play_video', url=video['url']),
            'thumbnail': video['thumbnail'],
            'is_playable': True
        })

    if video_list:
        items.append({
            'label': 'Next Page',
            'path': plugin.url_for('rsa_videos', page_no=page_no + 1)
        })

    return items


@plugin.route('/rsa_shorts')
def rsa_shorts():
    """
    Get RSA Shorts videos from RSA module and send to XBMC
    """
    items = []

    video_list = rsa.get_rsa_shorts_videos()
    for video in video_list:
        items.append({
            'label': video['title'],
            'path': plugin.url_for('play_video', url=video['url']),
            'thumbnail': video['thumbnail'],
            'is_playable': True
        })

    return items


@plugin.route('/play_video/<url>')
def play_video(url):
    youtube_id = rsa.get_youtube_id_from_video(url)
    return plugin.set_resolved_url(
        'plugin://plugin.video.youtube?action=play_video&videoid={0}'.format(
            youtube_id)
    )


if __name__ == '__main__':
    plugin.run()
