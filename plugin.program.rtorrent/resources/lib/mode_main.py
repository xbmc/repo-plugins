'''Displays rTorrent torrents'''
# Imports
import sys
import xbmcgui
import xbmcplugin
from . import functions as f
from . import globals as g

def main():
    '''Main program code'''
    dlds = []
    dlds = f.d_multicall_dict('main', [
        "d.name=", "d.hash=", "d.completed_chunks=", "d.size_chunks=",
        "d.size_files=", "d.is_active=", "d.complete=", "d.priority=", "d.size_bytes="]
    )
    if g.rtc.success:
        dlds_len = len(dlds)
        for dld in dlds:
            dld_percent_complete = dld['completed_chunks']*100/dld['size_chunks']
            dld_size_bytes = int(dld['size_bytes'])
            tbn=f.get_icon(dld['size_files'],dld['is_active'],dld['complete'],dld['priority'])

            cm_startstop_action = 'd_stop' if dld['is_active']==1 else 'd_start'
            cm_startstop_label = g.__lang__(30101) if dld['is_active']==1 else g.__lang__(30100)

            if dld_percent_complete<100:
                li_name = '{} ({:.1f}%)'.format(dld['name'], dld_percent_complete)
            else:
                li_name = dld['name']

            context_menu = [
                (cm_startstop_label, f.run_string(
                    'action', {'method': cm_startstop_action, 'download_hash': dld['hash']})),
                (g.__lang__(30102), f.run_string(
                    'action', {'method': 'd_erase', 'download_hash': dld['hash']})),
                (g.__lang__(30120), f.run_string(
                    'action', {'method': 'd_priority', 'download_hash': dld['hash'], 'priority': 3})),
                (g.__lang__(30121), f.run_string(
                    'action', {'method': 'd_priority', 'download_hash': dld['hash'], 'priority': 2})),
                (g.__lang__(30122), f.run_string(
                    'action', {'method': 'd_priority', 'download_hash': dld['hash'], 'priority': 1})),
                (g.__lang__(30123), f.run_string(
                    'action', {'method': 'd_priority', 'download_hash': dld['hash'], 'priority': 0}))
            ]

            list_item = xbmcgui.ListItem(li_name)
            list_item.setArt({ 'icon': tbn, 'thumbnail': tbn})
            list_item.addContextMenuItems(items=context_menu,replaceItems=True)
            list_item.setInfo('video',{ 'title':li_name, 'size':dld_size_bytes})
            if dld['size_files']>1:
                if not xbmcplugin.addDirectoryItem(int(sys.argv[1]),
                    f.run_string(
                        'files', {'digest': dld['hash'], 'numfiles': dld['size_files']}, False),
                    list_item,isFolder=True,totalItems=dlds_len): break
            else:
                if not xbmcplugin.addDirectoryItem(int(sys.argv[1]),
                    f.run_string(
                        'play',{'digest':dld['hash'], 'file_hash':f.file_hash(dld['hash'], 0)}, False),
                    list_item,totalItems=dlds_len): break
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_TITLE )
        xbmcplugin.addSortMethod(int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
        xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
