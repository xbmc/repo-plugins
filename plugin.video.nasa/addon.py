from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict
import resources.lib.videos_scraper as videos_scraper
import resources.lib.streams_scraper as streams_scraper
import resources.lib.vodcasts_scraper as vodcast_scraper

__addon_name__ = 'Nasa'
__id__ = 'plugin.video.nasa'


class Plugin_mod(Plugin):

    def add_items(self, iterable, view_mode=None,
                  sort_method_ids=[], is_update=False,):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            if view_mode:
                xbmc.executebuiltin('Container.SetViewMode(%s)' % view_mode)
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls

plugin = Plugin_mod(__addon_name__, __id__, __file__)


@plugin.route('/', default=True)
def show_root_menu():
    log('show_root_menu start')
    items = []
    items.append({'label': plugin.get_string(30100),
                  'url': plugin.url_for('show_streams')})
    items.append({'label': plugin.get_string(30101),
                  'url': plugin.url_for('show_video_topics')})
    items.append({'label': plugin.get_string(30103),
                  'url': plugin.url_for('show_vodcasts')})
    log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/streams/')
def show_streams():
    log('show_streams start')
    streams = streams_scraper.get_streams()
    items = [{'label': stream['title'],
              'url': plugin.url_for('play_stream', id=stream['id']),
              'thumbnail': stream['thumbnail'],
               'info': {'originaltitle': stream['title'],
                        'plot': stream['description']},
              'is_folder': False,
              'is_playable': True,
             } for stream in streams]
    log('show_streams finished')
    return plugin.add_items(items)


@plugin.route('/videos/')
def show_video_topics():
    log('show_video_topics started')
    Scraper = videos_scraper.Scraper()
    topics = Scraper.get_video_topics()
    items = [{'label': topic['name'],
              'url': plugin.url_for('show_videos_by_topic',
                                    topic_id=topic['id'],
                                    page='1'),
             } for topic in topics]
    items.append({'label': plugin.get_string(30200),
                  'url': plugin.url_for('search')})
    log('show_video_topics finished')
    return plugin.add_items(items)


@plugin.route('/vodcasts/')
def show_vodcasts():
    log('show_vodcasts start')
    vodcasts = vodcast_scraper.get_vodcasts()
    items = [{'label': vodcast['title'],
              'url': plugin.url_for('show_vodcast_videos',
                                    rss_file=vodcast['rss_file']),
             } for vodcast in vodcasts]
    log('show_vodcasts finished')
    return plugin.add_items(items)


@plugin.route('/vodcast/<rss_file>/')
def show_vodcast_videos(rss_file):
    log('show_vodcast_videos start')
    videos = vodcast_scraper.show_vodcast_videos(rss_file)
    items = [{'label': video['title'],
              'info': {'plot': video['description']},
              'url': video['url'],
              'thumbnail': video['thumbnail'],
              'is_folder': False,
              'is_playable': True,
             } for video in videos]
    log('show_vodcast_videos finished')
    return plugin.add_items(items)


@plugin.route('/videos/<topic_id>/<page>/')
def show_videos_by_topic(topic_id, page):
    log('show_videos_by_topic started with topic_id=%s' % topic_id)
    Scraper = videos_scraper.Scraper()
    limit = 30
    page = int(page)
    start = (page - 1) * limit
    videos, count = Scraper.get_videos_by_topic_id(topic_id, start, limit)
    items = __format_videos(videos)
    if count > page * limit:
        next_page = str(page + 1)
        items.insert(0, {'label': '>> %s %s >>' % (plugin.get_string(30001),
                                                   next_page),
                         'url': plugin.url_for('show_videos_by_topic',
                                               topic_id=topic_id,
                                               page=next_page)})
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {'label': '<< %s %s <<' % (plugin.get_string(30001),
                                                   previous_page),
                         'url': plugin.url_for('show_videos_by_topic',
                                               topic_id=topic_id,
                                               page=previous_page)})
    is_update = (page != 1)
    log('show_videos_by_topic finished')
    return plugin.add_items(items, sort_method_ids=(37, 3, 4, 8),
                            is_update=is_update)


@plugin.route('/video/<id>/')
def play_video(id):
    log('play_video started with id=%s' % id)
    Scraper = videos_scraper.Scraper()
    video = Scraper.get_video(id)
    log('play_video finished with video=%s' % video)
    return plugin.set_resolved_url(video['url'])


@plugin.route('/stream/<id>/')
def play_stream(id):
    log('play_stream started with id=%s' % id)
    stream_url = streams_scraper.get_stream(id)
    log('play_stream finished with video=%s' % stream_url)
    return plugin.set_resolved_url(stream_url)


@plugin.route('/search/')
def search():
    log('search start')
    query = None
    keyboard = xbmc.Keyboard('', plugin.get_string(30201))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        query = keyboard.getText()
        log('search gots a string: "%s"' % query)
        Scraper = videos_scraper.Scraper()
        videos, count = Scraper.search_videos(query)
        items = __format_videos(videos)
        log('search end')
        return plugin.add_items(items)


def __format_videos(videos):
    return [{'label': video['title'],
             'thumbnail': video['thumbnail'],
             'info': {'originaltitle': video['title'],
                      'duration': video['duration'],
                      'plot': video['description'],
                      'date': video['date'],
                      'size': video['filesize'],
                      'credits': video['author'],
                      'genre': '|'.join(video['genres'])},
             'url': plugin.url_for('play_video', id=video['id']),
             'is_folder': False,
             'is_playable': True,
            } for video in videos]


def log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))

if __name__ == '__main__':
    plugin.run()
