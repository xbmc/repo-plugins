from xbmcswift2 import Plugin
from resources.lib import nos


plugin = Plugin()


def resolve_paths(items):
    for item in items:
        item['path'] = plugin.url_for(**item['path'])
    return items


@plugin.route('/')
def index():
    return resolve_paths(nos.index())


@plugin.route('/show_category/<category_url>/')
def show_category(category_url):
    return resolve_paths(nos.show_category(category_url))


@plugin.route('/show_video/<video_url>/')
def show_video(video_url):
    file_url = nos.video_url_to_file_url(video_url)

    plugin.log.info('Playing url: {}'.format(file_url))
    plugin.set_resolved_url(file_url)


if __name__ == '__main__':
    plugin.run()
