from bs4 import BeautifulSoup
import json, time, sys, os
from xbmcswift2 import Plugin, ListItem, xbmcgui
from xbmcaddon import Addon

IS_PY3 = sys.version_info[0] > 2
if IS_PY3:
    from urllib.request import Request, urlopen
else:
    from urllib2 import Request, urlopen

class TripleR():
    def __init__(self):
        self.plugin = Plugin()
        respath = os.path.join(Addon().getAddonInfo('path'), 'resources')
        self.icon = os.path.join(respath, 'icon.png')
        self.fanart = os.path.join(respath, 'fanart.png')
        self.nextpage = self.plugin.get_string(30005)

    def run(self):
        self.plugin.run()

    def main_menu(self):
        items = [
            {
                'label': self.plugin.get_string(30001),
                'path': "https://ondemand.rrr.org.au/stream/ws-hq.m3u",
                'thumbnail': self.icon,
                'properties': {
                    'StationName': self.plugin.get_string(30000),
                    'fanart_image': self.fanart
                },
                'info': {
                    'mediatype': 'music'
                },
                'is_playable': True
            },
            {'label': self.plugin.get_string(30002), 'path': self.plugin.url_for(segment_menu, page=1)},
            {'label': self.plugin.get_string(30003), 'path': self.plugin.url_for(program_menu, page=1)},
            {'label': self.plugin.get_string(30004), 'path': self.plugin.url_for(audio_archives, page=1)},
        ]
        listitems = [ListItem.from_dict(**item) for item in items]
        return listitems

    def segment_menu(self, page):
        programs = self.get_programs("segments", page)
        items = self.parse_programs(programs, page)
        if len(items) > 0:
            items.append({'label': self.nextpage, 'path': self.plugin.url_for(segment_menu, page=int(page) + 1)})
        return items

    def program_menu(self, page):
        programs = self.get_programs("episodes", page)
        items = self.parse_programs(programs, page)
        if len(items) > 0:
            items.append({'label': self.nextpage, 'path': self.plugin.url_for(program_menu, page=int(page) + 1)})
        return items

    def audio_archives(self, page):
        programs = self.get_programs("archives", page)
        items = self.parse_programs(programs, page)
        if len(items) > 0:
            items.append({'label': self.nextpage, 'path': self.plugin.url_for(audio_archives, page=int(page) + 1)})
        return items

    def get_programs(self, collection, page):
        output_final = []

        url = "https://www.rrr.org.au/on-demand/{}?page={}".format(collection, page)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        req = Request(url, headers={'User-Agent': ua})
        html = urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')

        divs = soup.findAll(class_='card__text')

        for item in divs:
            cardbody = item.find(class_='card__body')
            if not cardbody:
                continue
            textbody = ' '.join(cardbody.strings)
            if len(item.contents) < 3:
                continue
            if 'data-view-playable' not in item.contents[-1].attrs:
                continue
            viewplayable = item.contents[-1].attrs['data-view-playable']
            mediaurl = ''
            try:
                itemobj = json.loads(viewplayable)['items'][0]
                itemdata = itemobj['data']
                if itemobj['type'] == 'clip':
                    ts = itemdata['timestamp']
                    l = int(itemdata['duration'])
                    mediaurl = 'https://ondemand.rrr.org.au/getclip?bw=h&l={}&m=r&p=1&s={}'.format(l, ts)
                elif itemobj['type'] == 'broadcast_episode':
                    ts = itemdata['timestamp']
                    mediaurl = 'https://ondemand.rrr.org.au/getclip?bw=h&l=0&m=r&p=1&s={}'.format(ts)
                else:
                    if 'audio_file' not in list(itemdata.keys()):
                        continue
                    mediaurl = itemdata['audio_file']['path']

                itemtime = time.strptime(itemdata['subtitle'], '%d %B %Y')
                itemtimestr = time.strftime('%Y-%m-%d', itemtime)
                output_final.append({
                    'id': itemobj['source_id'],
                    'title': itemdata['title'],
                    'desc': '\n'.join((self.plugin.get_string(30007), '%s')) % (itemdata['subtitle'], textbody),
                    'date': time.strftime('%d.%m.%Y', itemtime),
                    'year': int(itemtimestr[0:4]),
                    'aired': itemtimestr,
                    'duration': int(itemdata['duration']) if 'duration' in list(itemdata.keys()) else 0,
                    'url': mediaurl,
                    'art': itemdata['image']['path'] if 'image' in list(itemdata.keys()) else ''
                })
            except:
                continue

        return output_final

    def parse_programs(self, programs, page):
        items = []

        for program in programs:
            item = {
                'label': program['title'],
                'label2': self.plugin.get_string(30006) % (program['aired']),
                'info_type': 'video',
                'info': {
                    'count': program['id'],
                    'title': program['title'],
                    'plot': program['desc'],
                    'date': program['date'],
                    'year': program['year'],
                    'premiered': program['aired'],
                    'aired': program['aired'],
                    'duration': program['duration'],
                    'mediatype': 'song'
                },
                'properties': {
                    'StationName': self.plugin.get_string(30000),
                    'fanart_image': self.fanart
                },
                'path': program['url'],
                'thumbnail': program['art'],
                'is_playable': True
            }
            listitem = ListItem.from_dict(**item)
            items.append(listitem)

        return items

instance = TripleR()

@instance.plugin.route('/')
def main_menu():
    return instance.main_menu()

@instance.plugin.route('/segment_menu/<page>')
def segment_menu(page):
    return instance.segment_menu(page)

@instance.plugin.route('/program_menu/<page>')
def program_menu(page):
    return instance.program_menu(page)

@instance.plugin.route('/audio_archives/<page>')
def audio_archives(page):
    return instance.audio_archives(page)
