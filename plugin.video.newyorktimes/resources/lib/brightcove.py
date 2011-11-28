'''This module contains functions to convert objects returned from
python-brightcove into dictionaries suitable for passing to xbmcswift.

'''


def update_url_for_rtmp(url):
    '''Appends playpath option for an RTMP url. Other url types are
    returned unchanged.

    For brightcove urls, the playpath is after the '&'.

    '''
    if url.startswith('rtmp'):
        return '%s playpath=%s' % (url, url.split('&', 1)[1])
    return url


def item_from_video(video):
    '''Returns a dict suitable for passing to plugin.add_items from a
    brightcove api Video.

    '''
    item = {
        'label': video.name,
        'url': update_url_for_rtmp(video.FLVURL),
        'info': info_from_video(video),
        'is_playable': True,
        'is_folder': False,
    }

    if video.videoStillURL or video.thumbnailURL:
        item.update({'thumbnail': video.videoStillURL or video.thumbnailURL})

    return item


def info_from_video(video):
    '''Returns an info dict for a video item from a brightcove api
    Video.

    '''
    return {
        'year': video.publishedDate.year,
        'plot': video.longDescription,
        'plotoutline': video.shortDescription,
        'title': video.name,
        'premiered': video.publishedDate.strftime('%Y-%m-%d'),
    }
