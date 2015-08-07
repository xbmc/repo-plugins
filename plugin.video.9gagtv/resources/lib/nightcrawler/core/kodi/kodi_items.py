__author__ = 'bromix'

import xbmcgui
import xbmcplugin

from ...exception import ProviderException
from ... import utils


def _do_info_labels(context, kodi_item, item):
    def _process_not_none_value(_info_labels, name, value):
        if value is not None:
            _info_labels[name] = value
            pass
        pass

    info_labels = {}
    item_type = item['type']

    if item_type in ['audio', 'music']:
        # 'title' = 'Blow Your Head Off' (string)
        _process_not_none_value(info_labels, 'title', item['title'])

        # 'tracknumber' = 12 (int)
        _process_not_none_value(info_labels, 'tracknumber', item.get('tracknumber', None))

        # 'year' = 1994 (int)
        _process_not_none_value(info_labels, 'year', item.get('year', None))

        # 'genre' = 'Hardcore' (string)
        _process_not_none_value(info_labels, 'genre', item.get('genre', None))

        # 'duration' = 79 (int)
        _process_not_none_value(info_labels, 'duration', item.get('duration', None))

        # 'album' = 'Buckle Up' (string)
        _process_not_none_value(info_labels, 'album', item.get('album', None))

        # 'artist' = 'Angerfist' (string)
        _process_not_none_value(info_labels, 'artist', item.get('artist', None))

        if info_labels:
            kodi_item.setInfo(type=u'music', infoLabels=info_labels)
            pass
        pass
    elif item_type in ['video', 'movie']:
        # 'plot' = '...' (string)
        _process_not_none_value(info_labels, 'plot', item.get('plot', None))

        # studio
        _process_not_none_value(info_labels, 'studio', item.get('studio', None))

        # tvshowtitle
        _process_not_none_value(info_labels, 'tvshowtitle', item.get('format', None))

        if 'published' in item:
            published_date = utils.datetime.parse(item['published'])

            # 'aired' = '2013-12-12' (string)
            info_labels['aired'] = published_date.strftime('%Y-%m-%d')

            # 'premiered' = '2013-12-12' (string)
            info_labels['premiered'] = published_date.strftime('%Y-%m-%d')

            # 'dateadded' = '2014-08-11 13:08:56' (string) will be taken from 'date'
            info_labels['dateadded'] = published_date.strftime('%Y-%m-%d %H:%M:%S')

            # fallback
            if item_type == 'video':
                info_labels['season'] = published_date.year
                info_labels['episode'] = published_date.timetuple().tm_yday
                pass
            pass

        if item_type == 'video':
            if 'season' or 'episode' in item:
                # 'episode' = 12 (int)
                _process_not_none_value(info_labels, 'episode', item.get('episode', None))

                # 'season' = 12 (int)
                _process_not_none_value(info_labels, 'season', item.get('season', None))
                pass
            pass

        if info_labels:
            kodi_item.setInfo(type=u'video', infoLabels=info_labels)
            pass

        # 'rating' = 4.5 (float)
        # _process_video_rating(info_labels, base_item.get_rating())

        # 'director' = 'Steven Spielberg' (string)
        #_process_string_value(info_labels, 'director', base_item.get_director())

        # 'code' = 'tt3458353' (string) - imdb id
        #_process_string_value(info_labels, 'code', base_item.get_imdb_id())

        # 'cast' = [] (list)
        #_process_list_value(info_labels, 'cast', base_item.get_cast())
        pass
    pass


def _do_context_menu(context, kodi_item, item):
    if item.get('context-menu', {}).get('items', None):
        kodi_item.addContextMenuItems(item['context-menu']['items'],
                                      replaceItems=item['context-menu'].get('replace', False))
        pass
    pass


def _do_fanart(context, kodi_item, item):
    fanart = item.get('images', {}).get('fanart', u'')
    if fanart and context.get_settings().show_fanart():
        kodi_item.setProperty(u'fanart_image', fanart)
        pass
    pass


def create_kodi_item(context, item):
    icon_image_map = {'folder': u'DefaultFolder.png',
                      'video': u'DefaultVideo.png',
                      'movie': u'DefaultVideo.png',
                      'audio': u'DefaultAudio.png',
                      'music': u'DefaultAudio.png',
                      'image': u'DefaultFile.png',
                      'uri': u''}

    item_type = item['type']

    # uri items will only resolve an existing item, so we can return the item here
    if item_type == 'uri':
        return xbmcgui.ListItem(path=item['uri'])

    kodi_item = xbmcgui.ListItem(label=item.get('title', item['uri']),
                                 path=item['uri'],
                                 iconImage=icon_image_map.get(item_type, u''),
                                 thumbnailImage=item.get('images', {}).get('thumbnail', u''))

    # set playable
    if item_type in ['video', 'movie', 'audio', 'music', 'uri']:
        kodi_item.setProperty(u'IsPlayable', u'true')
        pass

    # set the duration
    if item_type in ['video', 'movie'] and 'duration' in item:
        kodi_item.addStreamInfo('video', {'duration': '%d' % item['duration']})
        pass

    _do_fanart(context, kodi_item, item)
    _do_context_menu(context, kodi_item, item)
    _do_info_labels(context, kodi_item, item)

    return kodi_item


def process_item(context, item, resolve=False):
    kodi_item = create_kodi_item(context, item)

    if item['type'] == 'uri' or resolve:
        xbmcplugin.setResolvedUrl(context.get_handle(), succeeded=True, listitem=kodi_item)
        pass
    else:
        if not xbmcplugin.addDirectoryItem(handle=context.get_handle(), url=item['uri'], listitem=kodi_item,
                                           isFolder=item['type'] == 'folder'):
            raise ProviderException('Failed to add folder item')
        pass
    pass