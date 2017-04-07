# -*- coding: utf-8 -*-
'''
    plugin.video.revision3
    Copyright (C) 2017 enen92,stacked
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import urllib
import urllib2
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import os
import time
import json
import kodiutils

class Downloader:

    def __init__(self,):
        self.stop = False


    def downloadall(self,localfile,url,name):
        self.dp = xbmcgui.DialogProgress()
        self.dp.create(kodiutils.get_string(32058),kodiutils.get_string(32059))
        self.download(localfile,url,url.split("/")[-1])


    def download(self,path,url,name):
        if xbmcvfs.exists(path):
            xbmcvfs.delete(path)

        self.dp.update(0,name)
        self.path = xbmc.translatePath(path)
        xbmc.sleep(500)
        start_time = time.time()

        u = urllib2.urlopen(url)
        meta = u.info()
        meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
        meta_length = meta_func("Content-Length")
        file_size = None
        block_sz = 8192
        if meta_length:
            file_size = int(meta_length[0])
        
        file_size_dl = 0
        f = xbmcvfs.File(self.path, 'wb')
        numblocks = 0

        while not self.stop:
            buffer = u.read(block_sz)
            if not buffer:
                break

            f.write(buffer)
            file_size_dl += len(buffer)
            numblocks += 1
            self.dialogdown(name,numblocks,block_sz,file_size,self.dp,start_time)

        f.close()
        return

    def dialogdown(self,name,numblocks, blocksize, filesize, dp, start_time):
        try:
            percent = min(numblocks * blocksize * 100 / filesize, 100)
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
            kbps_speed = numblocks * blocksize / (time.time() - start_time) 
            if kbps_speed > 0: eta = (filesize - numblocks * blocksize) / kbps_speed 
            else: eta = 0 
            kbps_speed = kbps_speed / 1024 
            total = float(filesize) / (1024 * 1024) 
            mbs = '%.02f MB %s %.02f MB' % (currently_downloaded,kodiutils.get_string(32060), total) 
            e = ' (%.0f Kb/s) ' % kbps_speed 
            tempo = kodiutils.get_string(32061) + ' %02d:%02d' % divmod(eta, 60) 
            dp.update(percent,name +' - '+ mbs + e,tempo)
        except: 
            percent = 100 
            dp.update(percent) 

        if dp.iscanceled():
            self.stop = True
            dp.close()
            try: xbmcvfs.delete(self.path)
            except: xbmc.log(msg='[Revision3] Could not remove file', level=xbmc.LOGERROR)
            xbmc.log(msg='[Revision3] Download canceled', level=xbmc.LOGDEBUG)