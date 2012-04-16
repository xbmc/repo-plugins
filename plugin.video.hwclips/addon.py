from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict
import resources.lib.hwclips as hwclips
import resources.lib.cache

__ADDON_NAME__ = 'HWCLIPS.com'
__ADDON_ID__ = 'plugin.video.hwclips'

STRINGS = {'videos': 30000,
           'groups': 30001,
           'categories': 30002,
           'mostRecent': 30010,
           'topRated': 30011,
           'mostViewed': 30012}

OVERLAYS = {'none': xbmcgui.ICON_OVERLAY_NONE,
            'hd': xbmcgui.ICON_OVERLAY_HD}


class Plugin_adv(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[],
                  override_view_mode=False):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            self.set_content('movies')
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            if override_view_mode:
                if xbmc.getSkinDir() == 'skin.confluence':
                    xbmc.executebuiltin('Container.SetViewMode(504)')
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage,
                              thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))
        if cleaned_info:
            li.setInfo('video', cleaned_info)
            li.setProperty('Fanart_Image', iconImage)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'])
        return options['url'], li, options.get('is_folder', True)


plugin = Plugin_adv(__ADDON_NAME__, __ADDON_ID__, __file__)


@plugin.route('/', default=True)
def show_root():
    log('show_root started')
    type, data, num_pages = Api.get_list()
    if type == hwclips.API_RESPONSE_TYPE_FOLDERS:
        return __add_folders(data)
    else:
        raise Exception('Unexpected return type from api')


@plugin.route('/<path>/page/<page>')
def show_folder(path, page):
    log('show_folder started with path:%s page:%s' % (path, page))
    Cache = __get_cache()
    cache_id = '|'.join((path, page,))
    cached_data = Cache.get(cache_id, max_age=3600)
    if not cached_data:
        cached_data = Api.get_list(path, int(page))
        Cache.set(cache_id, cached_data)
    type, data, num_pages = cached_data
    if type == hwclips.API_RESPONSE_TYPE_FOLDERS:
        return __add_folders(data)
    elif type == hwclips.API_RESPONSE_TYPE_VIDEOS:
        return __add_videos(data, path, page, num_pages)
    else:
        raise Exception('Unexpected return type from api')


@plugin.route('/video/<id>/')
def watch_video(id):
    log('watch_video started with id: %s' % id)
    video = Api.get_video(id)
    log('watch_video finished with video: %s' % video)
    return plugin.set_resolved_url(video['full_path'])


def __add_folders(entries):
    items = [{'label': __format_folder_title(e['name'], int(e['count'])),
              'thumbnail': e.get('image', 'DefaultFolder.png'),
              'info': {'plot': e['description']},
              'url': plugin.url_for('show_folder', path=e['path'],
                                                   page='1'),
             } for e in entries]
    return plugin.add_items(items)


def __add_videos(entries, path, page, num_pages):
    items = [{'label': __format_video_title(e['name'], e['language']),
              'iconImage': e.get('image', 'DefaultVideo.png'),
              'info': {'originaltitle': e['name'],
                       'studio': e['username'],
                       'date': e['date'],
                       'year': e['year'],
                       'genre': ', '.join(e['keywords']),
                       'plot': e['description'],
                       'rating': float(e['rating']),
                       'votes': e['votes'],
                       'views': e['views'],
                       'overlay': __format_video_overlay(e['is_hd']),
                       'duration': e['duration']},
              'url': plugin.url_for('watch_video',
                                    id=e['id']),
              'is_folder': False,
              'is_playable': True,
             } for e in entries]
    if int(page) < int(num_pages):
        next_page = str(int(page) + 1)
        items.insert(0, {'label': '>> %s %s >>' % (plugin.get_string(30020),
                                                   next_page),
                         'url': plugin.url_for('show_folder',
                                               path=path,
                                               page=next_page)})
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {'label': '<< %s %s <<' % (plugin.get_string(30020),
                                                   prev_page),
                         'url': plugin.url_for('show_folder',
                                               path=path,
                                               page=prev_page)})
    is_update = (int(page) != 1)
    sort_methods = [xbmcplugin.SORT_METHOD_DATE,
                    xbmcplugin.SORT_METHOD_LABEL,
                    xbmcplugin.SORT_METHOD_VIDEO_RATING,
                    xbmcplugin.SORT_METHOD_VIDEO_RUNTIME]
    override_view_mode = plugin.get_setting('override_view_mode') == 'true'
    return plugin.add_items(items, is_update=is_update,
                            sort_method_ids=sort_methods,
                            override_view_mode=override_view_mode)


def __format_video_overlay(is_hd):
    if is_hd:
        overlay = OVERLAYS['hd']
    else:
        overlay = OVERLAYS['none']
    return overlay


def __format_folder_title(title, count=0):
    string_id = STRINGS.get(title)
    if string_id:
        title = plugin.get_string(string_id)
    if count and plugin.get_setting('show_count') == 'true':
        title = '%s (%d)' % (title, count)
    return title


def __format_video_title(title, lang_code):
    if lang_code and plugin.get_setting('show_lang') == 'true':
        if lang_code == 'no_lang':
            lang = 'ALL'
        else:
            lang = lang_code.split('_')[0].upper()
        title = '%s (%s)' % (title, lang)
    return title


def __get_language():
    xbmc_language = xbmc.getLanguage().lower()
    if xbmc_language.startswith('english'):
        lang = 'en'
    elif xbmc_language.startswith('german'):
        lang = 'de'
    else:
        lang = 'en'
    return lang


def __get_cache():
    profile_path = plugin._plugin.getAddonInfo('profile').decode('utf-8')
    cache_path = xbmc.translatePath(profile_path)
    return resources.lib.cache.Cache(cache_path)


def log(msg):
    xbmc.log(u'%s addon: %s' % (__ADDON_NAME__, msg))


if __name__ == '__main__':
    language = __get_language()
    Api = hwclips.Api(language)
    plugin.run()
