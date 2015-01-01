__author__ = 'bromix'

import xbmcgui

from ...items import VideoItem
from . import info_labels


def to_video_item(context, video_item):
    item = xbmcgui.ListItem(label=video_item.get_name(),
                            iconImage=u'DefaultVideo.png',
                            thumbnailImage=video_item.get_image())

    # only set fanart is enabled
    settings = context.get_settings()
    if video_item.get_fanart() and settings.show_fanart():
        item.setProperty(u'fanart_image', video_item.get_fanart())
        pass
    if video_item.get_context_menu() is not None:
        item.addContextMenuItems(video_item.get_context_menu(), replaceItems=video_item.replace_context_menu())
        pass

    item.setProperty(u'IsPlayable', u'true')

    item.setInfo(type=u'video', infoLabels=info_labels.create_from_item(video_item))
    return item

def to_item(context, base_item):
    if isinstance(base_item, VideoItem):
        return to_video_item(context, base_item)

    return None