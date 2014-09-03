from xbmcswift2 import Plugin
from resources.lib import scraper
import pprint


plugin = Plugin()


@plugin.route('/')
def index():
    emission_types = scraper.Emission.get_emission_types()

    pprint.pprint(emission_types)
    items = [{
        'label': emission_type['name'],
        'path': plugin.url_for('show_emission_for_type', type_index=emission_type['index']),
    } for emission_type in emission_types]

    return items

@plugin.route('/emission_type/<type_index>/')
def show_emission_for_type(type_index):
    emissions = scraper.Emission.get_emissions_from_index(type_index)

    items = [{
        'label': emission['name'],
        'path': plugin.url_for('show_emission', url=emission['url']),
        'icon': emission['icon'],
    } for emission in emissions]

    return items

@plugin.route(('/emission/<url>/'))
def show_emission(url):
    videos = scraper.Video.from_url(url)

    #pprint.pprint(videos)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('play_video', url=video['url']),
        'icon': video['icon'],
        'is_playable': True,
    } for video in videos]

    return items

@plugin.route('/video/<url>/')
def play_video(url):
    media = scraper.Media.from_url(url)
    media_url = media['url']
    plugin.log.info('Playing url: %s' % media_url)
    return plugin.set_resolved_url(media_url)


if __name__ == '__main__':
    plugin.run()
