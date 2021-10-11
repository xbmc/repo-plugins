''' Playing torrents '''
import os
import xbmc
import xbmcgui
from . import functions as f
from . import globals as g


#XBMC file player code
def main(digest, file_hash):
    '''Play files from torrents'''
    xbmc.log('file_hash: %s' % file_hash )
    # Check to see if the file has completely downloaded.
    if g.__islocal__==1:
        url = g.rtc.call('f.frozen_path', file_hash)
    else:
        f_name = g.rtc.call('f.path', file_hash)
        dld_name = g.rtc.call('d.name', digest)
        dld_is_multi_file = int(g.rtc.call('d.is_multi_file', digest))
        dld_complete = int(g.rtc.call('d.complete', digest))

        # Create the path to file to be played
        if dld_is_multi_file==0:
            path = f_name
        else:
            path = os.path.join(dld_name,f_name)
        # Files that would be in the complete folder
        if dld_complete==1:
            url = os.path.join(g.__setting__('remote_folder_complete'),path)
        else:
            url = os.path.join(g.__setting__('remote_folder_downloading'),path)

    f_completed_chunks = int(g.rtc.call('f.completed_chunks', file_hash))
    f_size_chunks = int(g.rtc.call('f.size_chunks', file_hash))
    f_percent_complete = f_completed_chunks*100/f_size_chunks

    if f_percent_complete<100:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(g.__lang__(30150), "\n".join((g.__lang__(30151), g.__lang__(30152))))
        if ret is True:
            f.play_file(url)
    else:
        f.play_file(url)
