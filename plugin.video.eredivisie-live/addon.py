from xbmcswift2 import Plugin
from resources.lib import foxsportsnl


plugin = Plugin()


def resolve_paths(items):
    for item in items:
        item['path'] = plugin.url_for(**item['path'])
    return items


@plugin.route('/')
def index():
    return resolve_paths(foxsportsnl.index())


@plugin.route('/show_category/<category_id>/')
def show_category(category_id):
    return resolve_paths(foxsportsnl.show_category(category_id))


@plugin.route('/show_video/<video_id>/')
def show_video(video_id):
    playlist_url = foxsportsnl.video_id_to_playlist_url(video_id)

    plugin.log.info('Playing url: {}'.format(playlist_url))
    plugin.set_resolved_url(playlist_url)


if __name__ == '__main__':
    plugin.run()
