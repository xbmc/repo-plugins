import os
from xbmcswift import Plugin, xbmcplugin, xbmcgui
import resources.lib.scraper as scraper


class Plugin_adv(Plugin):

    def add_items(self, iterable, sort_method_ids=[]):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        return urls

    def set_resolved_url(self, url, title=None):
        if self._mode in ['crawl', 'interactive', 'test']:
            print 'ListItem resolved to %s' % url
        li = xbmcgui.ListItem(path=url)
        if title:
            li.setLabel(title)
        xbmcplugin.setResolvedUrl(self.handle, True, li)
        if self._mode in ['interactive', 'crawl', 'test']:
            return []


plugin = Plugin_adv('Wimp.com', 'plugin.video.wimp', __file__)


@plugin.route('/', default=True)
def show_root():
    log('show_root started')
    categories = [{'label': plugin.get_string(30000),
                   'url': plugin.url_for('show_current')},
                  {'label': plugin.get_string(30001),
                   'url': plugin.url_for('watch_random'),
                   'is_folder': False,
                   'is_playable': True},
                  {'label': plugin.get_string(30002),
                   'url': plugin.url_for('show_archive')},
                  {'label': plugin.get_string(30003),
                   'url': plugin.url_for('search')}]
    return plugin.add_items(categories)


@plugin.route('/current/')
def show_current():
    log('show_current started')
    videos = scraper.get_current_videos()
    return __add_videos(videos)


@plugin.route('/watch/<video_id>/')
def watch_video(video_id):
    log('watch_video started with video_id=%s' % video_id)
    mobile = __mobile()
    video_url, title = scraper.get_video_url(video_id, mobile=mobile)
    log('watch_video finished with video_url=%s' % video_url)
    return plugin.set_resolved_url(video_url)


@plugin.route('/random/')
def watch_random():
    log('watch_random started')
    mobile = __mobile()
    video_url, title = scraper.get_random_video_url(mobile=mobile)
    log('watch_random finished with video_url=%s' % video_url)
    return plugin.set_resolved_url(video_url, title=title)


@plugin.route('/archive/')
def show_archive():
    log('show_archive started')
    archive_dates = scraper.get_archive_dates()
    items = [{'label': archive_date['title'],
              'url': plugin.url_for('show_archived_videos',
                                    archive_id=archive_date['archive_id']),
             } for archive_date in archive_dates]
    return plugin.add_items(items)


@plugin.route('/archive/<archive_id>/')
def show_archived_videos(archive_id):
    log('show_archived_videos started with archive_id: %s' % archive_id)
    videos = scraper.get_videos_by_archive_date(archive_id)
    return __add_videos(videos)


@plugin.route('/search/')
def search():
    log('search start')
    search_string = None
    keyboard = xbmc.Keyboard('', plugin.get_string(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        log('search gots a string: "%s"' % search_string)
        videos = scraper.get_search_result(search_string)
        return __add_videos(videos)


def __add_videos(videos):
    p = plugin._plugin.getAddonInfo('path').decode('utf-8')
    icon = os.path.join(xbmc.translatePath(p), 'icon.png')
    items = [{'label': video['title'],
              'thumbnail': icon,
              'url': plugin.url_for('watch_video',
                                    video_id=video['video_id']),
              'info': {'date': video['date']},
              'is_folder': False,
              'is_playable': True,
             } for video in videos]
    sort_methods = [xbmcplugin.SORT_METHOD_DATE,
                    xbmcplugin.SORT_METHOD_LABEL]
    return plugin.add_items(items, sort_method_ids=sort_methods)


def __mobile():
    return plugin.get_setting('pref_video') == '1'


def log(msg):
    xbmc.log('%s addon: %s' % ('wimp.com', msg))

if __name__ == '__main__':
    plugin.run()
