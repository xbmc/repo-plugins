from xbmcswift2 import Plugin, xbmcgui
from resources.lib import pbsfm
import urllib2
import json

plugin = Plugin()
pbsapi = 'http://pulse.emit.com/api/stations/pbs'

@plugin.route('/')
def main_menu():
    items = [
        {'label': plugin.get_string(30000),'path': "http://eno.emit.com:8000/pbsfm_live_64.mp3",'is_playable': True},
        {'label': plugin.get_string(30001), 'path': plugin.url_for('shows')},
        ]

    return items


@plugin.route('/shows/')
def shows():

    shows = fetch_shows()
    
    items = []
    for show in shows:
        items.append({
                    'label': show['name'], 
                    'path': plugin.url_for('list_episodes', slug=show['slug']) 
                    })
    return items


@plugin.route('/episodes/<slug>/')
def list_episodes(slug):

    episodes = fetch_episodes(slug)
    items = []
    if episodes:
        for episode in episodes:
            if episode['streams']:
                items.append({'label': episode['name'], 'path': episode['streams'][0]['href'], 'is_playable': True})
    else:
        last = fetch_last(slug)
        if last['lastEpisode']:
            items.append({'label': last['lastEpisode']['name'], 'path': last['lastEpisode']['streams'][0]['href'], 'is_playable': True})
        else:
            items.append({'label': 'Nothing Found!', 'path': None})
    return items

@plugin.cached(TTL=60*24*7)
def fetch_shows():
    response = urllib2.urlopen(pbsapi)
    home = json.load(response)
    shows = json.load(urllib2.urlopen(home['$shows']))
    return shows

@plugin.cached(TTL=60*24)
def fetch_episodes(slug):
    episode_list = pbsapi+'/shows/'+slug+'/episodes'
    episodes = json.load(urllib2.urlopen(episode_list))

    return episodes

@plugin.cached(TTL=60*24)
def fetch_last(slug):
    show_url = pbsapi+'/shows/'+slug
    show = json.load(urllib2.urlopen(show_url))
    return show


if __name__ == '__main__':
    plugin.run()
