from xbmcswift2 import Plugin

from resources.lib import scraper


plugin = Plugin()


@plugin.route('/')
def main_menu():
    return plugin.redirect(plugin.url_for('show_podcasts', page_no=1))


@plugin.route('/podcasts/<page_no>')
def show_podcasts(page_no):
    url = 'http://podcasts.joerogan.net/podcasts/page/{0}?load'.format(page_no)
    next_page = int(page_no) + 1

    html = scraper.get(url)
    podcasts = scraper.get_podcasts(html)
    items = [{
        'label': podcast[0],
        'path': plugin.url_for('play_podcast', slug=podcast[1]),
        'thumbnail': podcast[2],
        'is_playable': True,
    } for podcast in podcasts]
    items.append(
        {'label': 'Next Page',
         'path': plugin.url_for('show_podcasts', page_no=next_page)})

    return items


@plugin.route('/podcasts/play/<slug>/')
def play_podcast(slug):
    url = ('http://podcasts.joerogan.net/wp-admin/admin-ajax.php'
           '?action=loadPermalink&slug={0}').format(slug)
    data = scraper.get_video_id(scraper.get(url))
    if data['provider'] == 'audio':
        url = data['id']
    else:
        url = ('plugin://plugin.video.{0}/'
               '?action=play_video&videoid={1}').format(
            data['provider'], data['id'])
    plugin.log.info('Playing url: %s' % url)
    plugin.set_resolved_url(url)


if __name__ == '__main__':
    plugin.run()
