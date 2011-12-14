from xbmcswift import Plugin
import resources.lib.scraper as scraper

class Plugin_adv(Plugin):

    def add_items(self, iterable, view_mode=None, is_update=False,
                  sort_method_ids=[]):
        print is_update
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
                import xbmc
                xbmc.executebuiltin('Container.SetViewMode(%s)' % view_mode)
            import xbmcplugin
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
                print 'added: %d' % id
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls


plugin = Plugin_adv('4Players Videos', 'plugin.video.4players', __file__)


@plugin.route('/', default=True)
def show_categories():
    categories = scraper.getCategories()
    cat_ids = (30100, 30101, 30102, 30103, 30104, 30105, 30106, 30107,
               30108, 30109, 30110)
    items = [{'label': plugin.get_string(cat_ids[i]),
              'url': plugin.url_for('show_videos',
                                    category=category, page='1'),
             } for i, category in enumerate(categories)]
    return plugin.add_items(items)


@plugin.route('/category/<category>/<page>/')
def show_videos(category, page):
    videos, last_page_num = scraper.getVideos(category, page)
    items = [{'label': video['title'],
              'thumbnail': video['image'],
              'info': {'originaltitle': video['title'],
                       'duration': video['length'],
                       'date': video['date'],
                       'rating': float(video['rating']),
                       'votes': str(video['views'])},
              'url': plugin.url_for('watch_video', url=video['url']),
              'is_folder': False,
              'is_playable': True,
             } for video in videos]
    if int(page) < int(last_page_num):
        next_page = str(int(page) + 1)
        items.insert(0, {'label': '>> %s %s >>' % (plugin.get_string(30001),
                                                   next_page),
                         'url': plugin.url_for('show_videos',
                                               category=category,
                                               page=next_page)})
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {'label': '<< %s %s <<' % (plugin.get_string(30001),
                                                   prev_page),
                         'url': plugin.url_for('show_videos',
                                               category=category,
                                               page=prev_page)})
    is_update = (int(page) != 1)  # only update the listing if page is not 1
    sort_method_ids = (21, 3, 29)  # Playlist, date, runtime
    return plugin.add_items(items, is_update=is_update, 
                            sort_method_ids=sort_method_ids)


@plugin.route('/watch/<url>/')
def watch_video(url):
    video_url = scraper.getVideoFile(url)
    return plugin.set_resolved_url(video_url)


if __name__ == '__main__':
    plugin.run()
