
#       Copyright (C) 2013-2014
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import time
import glob
import urllib2

import xbmc
import utils
import sfile

CacheDir  = os.path.join(utils.ADDON.getAddonInfo('profile'), 'c')
CacheSize = 100


def clearCache():
    sfile.rmtree(CacheDir)
    while sfile.exists(CacheDir):
        xbmc.sleep(50)
    checkCacheDir()


def checkCacheDir():
    sfile.makedirs(CacheDir)


def getURLNoCache(url, agent=None, tidy=True):
    req = urllib2.Request(url)
    if agent:
        req.add_header('User-Agent', agent)

    response = urllib2.urlopen(req)
    html     = response.read()
    response.close()

    if tidy:
        html = html.replace('\r', '').replace('\n', '').replace('\t', '')

    return html


def getURL(url, maxSec=0, agent=None, tidy=True):
    purgeCache()
    
    if url == None:
        return None

    if maxSec > 0:
        timestamp = getTimestamp(url)
        if timestamp > 0:
            if (time.time() - timestamp) <= maxSec:
                return getCachedData(url)
			
    data = getURLNoCache(url, agent, tidy)
    addToCache(url, data)
    return data


def getTimestamp(url):
    cacheKey  = createKey(url)
    cachePath = os.path.join(CacheDir, cacheKey)

    try:    return sfile.mtime(cachePath)
    except: pass

    return 0


def getCachedData(url):
    cacheKey  = createKey(url)
    cachePath = os.path.join(CacheDir, cacheKey)
    data      = sfile.read(cachePath)

    return data


def addToCache(url, data):
    checkCacheDir()

    cacheKey  = createKey(url)
    cachePath = os.path.join(CacheDir, cacheKey)
    f         = sfile.file(cachePath, 'w')

    f.write(data)
    f.close()

    purgeCache()


def createKey(url):
    try:
        from hashlib import md5
        return md5(url).hexdigest()
    except:
        import md5
        return md5.new(url).hexdigest()

        
def purgeCache():
    files   = sfile.glob(CacheDir)
    nFiles = len(files)

    try:
        while nFiles > gCacheSize:            
            oldestFile = getOldestFile(files)
 
            while sfile.exists(oldestFile):
                try:    sfile.remove(oldestFile)
                except: pass

            files  = sfile.glob(CacheDir)
            nFiles = len(files)
    except:
        pass


def getOldestFile(files):
    if not files:
        return None
    
    now    = time.time()
    oldest = (files[0], now - sfile.ctime(files[0]))

    for f in files[1:]:
        age = now - sfile.ctime(f)
        if age > oldest[1]:
            oldest = (f, age)

    return oldest[0]