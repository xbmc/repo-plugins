'''Displays rTorrent files'''

import sys
import xbmcgui
import xbmcplugin
from . import functions as f
from . import globals as g

def main(digest,numfiles):
    '''For files inside a multi-file torrent'''
    files = []
    files = g.rtc.call('f.multicall',
        digest,
        1,
        "f.path=",
        "f.completed_chunks=",
        "f.size_chunks=",
        "f.priority=",
        "f.size_bytes="
    )

    for i, file in enumerate(files):
        f_completed_chunks = int(file[1])
        f_size_chunks = int(file[2])
        f_priority = file[3]
        f_size_bytes = int(file[4])
        f_percent_complete = 100 if f_size_chunks<1 else f_completed_chunks*100/f_size_chunks
        if f_percent_complete==100:
            li_name = file[0]
            f_complete = 1
        else:
            li_name = '{} ({:.1f}%)'.format(file[0], f_percent_complete)
            f_complete = 0
        tbn=f.get_icon(0,1,f_complete,f_priority)
        list_item = xbmcgui.ListItem(label=li_name)
        list_item.setArt({'icon': tbn, 'thumb': tbn})
        context_menu = [
            (g.__lang__(30120),
                f.run_string('action',
                {'method': 'f_priority', 'file_hash': f.file_hash(digest, i), 'priority': 2})),
            (g.__lang__(30121),
                f.run_string('action',
                {'method': 'f_priority', 'file_hash': f.file_hash(digest, i), 'priority': 1})),
            (g.__lang__(30124),
                f.run_string('action',
                {'method': 'f_priority', 'file_hash': f.file_hash(digest, i), 'priority': 0}))]
        list_item.addContextMenuItems(items=context_menu,replaceItems=True)
        list_item.setInfo('video',{'title':li_name,'size':f_size_bytes})
        if not xbmcplugin.addDirectoryItem(int(sys.argv[1]),
            f.run_string('play',{'digest': digest, 'file_hash': f.file_hash(digest, i)}, False),
            list_item,totalItems=int(numfiles)): break
    xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
