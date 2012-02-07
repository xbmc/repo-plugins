from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict
import resources.lib.scraper as scraper

__addon_name__ = 'Radio'
__id__ = 'plugin.audio.radio_de'


class Plugin_mod(Plugin):

    def add_items(self, iterable, view_mode=None, sort_method_ids=[]):
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
            xbmcplugin.endOfDirectory(self.handle)
        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage,
                              thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))
        if cleaned_info:
            li.setInfo('music', infoLabels=cleaned_info)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'], replaceItems=False)
        return options['url'], li, options.get('is_folder', True)

plugin = Plugin_mod(__addon_name__, __id__, __file__)


@plugin.route('/', default=True)
def show_root_menu():
    __log('show_root_menu start')
    items = []
    items.append({'label': plugin.get_string(30107),
                  'url': plugin.url_for('show_local_stations')})

    items.append({'label': plugin.get_string(30100),
                  'url': plugin.url_for('show_recommendation_stations')})

    items.append({'label': plugin.get_string(30101),
                  'url': plugin.url_for('show_top_stations')})

    items.append({'label': plugin.get_string(30102),
                  'url': plugin.url_for('show_station_categories',
                                        category_type='genre')})

    items.append({'label': plugin.get_string(30103),
                  'url': plugin.url_for('show_station_categories',
                                        category_type='topic')})

    items.append({'label': plugin.get_string(30104),
                  'url': plugin.url_for('show_station_categories',
                                        category_type='country')})

    items.append({'label': plugin.get_string(30105),
                  'url': plugin.url_for('show_station_categories',
                                        category_type='city')})

    items.append({'label': plugin.get_string(30106),
                  'url': plugin.url_for('show_station_categories',
                                        category_type='language')})

    items.append({'label': plugin.get_string(30200),
                  'url': plugin.url_for('search')})

    items.append({'label': plugin.get_string(30108),
                  'url': plugin.url_for('show_mystations')})

    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/local_stations/')
def show_local_stations():
    __log('show_local_stations start')
    language = __get_language()
    stations = scraper.get_most_wanted(language)
    items = __format_stations(stations['localBroadcasts'])
    __log('show_local_stations end')
    return plugin.add_items(items)


@plugin.route('/recommendation_stations/')
def show_recommendation_stations():
    __log('show_recommendation_stations start')
    language = __get_language()
    stations = scraper.get_recommendation_stations(language)
    items = __format_stations(stations)
    __log('show_recommendation_stations end')
    return plugin.add_items(items)


@plugin.route('/top_stations/')
def show_top_stations():
    __log('show_top_stations start')
    language = __get_language()
    stations = scraper.get_top_stations(language)
    items = __format_stations(stations)
    __log('show_top_stations end')
    return plugin.add_items(items)


@plugin.route('/stations_by_category/<category_type>')
def show_station_categories(category_type):
    __log('show_station_categories started with category_type=%s'
          % category_type)
    language = __get_language()
    categories = scraper.get_categories_by_category_type(language,
                                                         category_type)
    items = []
    for category in categories:
        category = category.encode('utf-8')
        try:
            items.append({'label': category,
                          'url': plugin.url_for('show_stations_by_category',
                                                category_type=category_type,
                                                category=category)})
        except:
            __log('show_station_categories EXCEPTION: %s' % repr(category))
    __log('show_station_categories end')
    return plugin.add_items(items)


@plugin.route('/stations_by_category/<category_type>/<category>/')
def show_stations_by_category(category_type, category):
    __log(('show_stations_by_category started with '
           'category_type=%s, category=%s') % (category_type, category))
    language = __get_language()
    stations = scraper.get_stations_by_category(language, category_type,
                                                category)
    items = __format_stations(stations)
    __log('show_stations_by_category end')
    return plugin.add_items(items)


@plugin.route('/search_station/')
def search():
    __log('search start')
    search_string = None
    keyboard = xbmc.Keyboard('', plugin.get_string(30201))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        __log('search gots a string: "%s"' % search_string)
        language = __get_language()
        stations = scraper.search_stations_by_string(language, search_string)
        items = __format_stations(stations)
        __log('search end')
        return plugin.add_items(items)


@plugin.route('/my_stations/')
def show_mystations():
    __log('show_mystations start')
    my_station_ids = __get_my_stations()
    language = __get_language()
    stations = []
    for station_id in my_station_ids:
        stations.append(scraper.get_station_by_station_id(language,
                                                          station_id))
    items = __format_stations(stations)
    __log('show_mystations end')
    return plugin.add_items(items)


@plugin.route('/my_stations/add/<station_id>/')
def add_station_mystations(station_id):
    __log('add_station_mystations started with station_id=%s' % station_id)
    my_stations = __get_my_stations()
    if not station_id in my_stations:
        my_stations.append(station_id)
        my_stations_string = ','.join(my_stations)
        plugin.set_setting('my_stations', my_stations_string)
    __log('add_station_mystations ended with %d items: %s' % (len(my_stations),
                                                              my_stations))


@plugin.route('/my_stations/del/<station_id>/')
def del_station_mystations(station_id):
    __log('del_station_mystations started with station_id=%s' % station_id)
    my_stations = __get_my_stations()
    if station_id in my_stations:
        my_stations.remove(station_id)
        my_stations_string = ','.join(my_stations)
        plugin.set_setting('my_stations', my_stations_string)
    __log('del_station_mystations ended with %d items: %s' % (len(my_stations),
                                                              my_stations))


@plugin.route('/station/<id>/')
def get_stream(id):
    __log('get_stream started with id=%s' % id)
    language = __get_language()
    station = scraper.get_station_by_station_id(language, id)
    stream_url = station['streamURL']
    __log('get_stream end with stream_url=%s' % stream_url)
    return plugin.set_resolved_url(stream_url)


def __format_stations(stations):
    __log('__format_stations start')
    items = []
    my_station_ids = __get_my_stations()
    for station in stations:
        if station['picture1Name']:
            thumbnail = station['pictureBaseURL'] + station['picture1Name']
        else:
            thumbnail = ''
        if not 'genresAndTopics' in station:
            station['genresAndTopics'] = ','.join(station['genres']
                                                  + station['topics'])
        if not str(station['id']) in my_station_ids:
            my_station_label = plugin.get_string(30400)
            my_station_url = plugin.url_for('add_station_mystations',
                                            station_id=str(station['id']))
        else:
            my_station_label = plugin.get_string(30401)
            my_station_url = plugin.url_for('del_station_mystations',
                                            station_id=str(station['id']))
        items.append({'label': station['name'],
                      'thumbnail': thumbnail,
                      'info': {'Title': station['name'],
                               'rating': str(station['rating']),
                               'genre': station['genresAndTopics'],
                               'Size': station['bitrate'],
                               'tracknumber': station['id'],
                               'comment': station['currentTrack']},
                      'context_menu': [(my_station_label,
                                        'XBMC.RunPlugin(%s)'
                                        % my_station_url), ],
                      'url': plugin.url_for('get_stream',
                                            id=str(station['id'])),
                      'is_folder': False,
                      'is_playable': True})
    __log('__format_stations end')
    return items


def __get_my_stations():
    __log('__get_my_stations start')
    my_stations = []
    my_stations_string = plugin.get_setting('my_stations')
    if my_stations_string:
        my_stations = my_stations_string.split(',')
    __log('__get_my_stations ended with %d items: %s' % (len(my_stations),
                                                         my_stations))
    return my_stations


def __get_language():
    if not plugin.get_setting('not_first_run'):
        xbmc_language = xbmc.getLanguage()
        __log('__get_language has first run with xbmc_language=%s'
              % xbmc_language)
        if xbmc_language == 'English':
            plugin.set_setting('language', '0')
        elif xbmc_language == 'German':
            plugin.set_setting('language', '1')
        elif xbmc_language == 'French':
            plugin.set_setting('language', '2')
        else:
            plugin.open_settings()
        plugin.set_setting('not_first_run', '1')
    lang_id = plugin.get_setting('language')
    return ('english', 'german', 'french')[int(lang_id)]


def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))

if __name__ == '__main__':
    plugin.run()
