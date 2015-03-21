#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcplugin
import xbmcgui

import urllib
import os, uuid
import threading, Queue

from resources.lib.utils import *
from resources.lib.dropboxclient import *
from resources.lib.accountsettings import AccountSettings

MAX_MEDIA_ITEMS_TO_LOAD_ONCE = 200

class DropboxViewer(object):
    '''
    Handles the XBMC GUI/View behaviour and takes care of caching the files
    '''
    _nrOfMediaItems = 0
    _loadedMediaItems = 0
    _totalItems = 0
    _filterFiles = False
    _loader = None
    _session = ''
    _useStreamingURLs = False
        
    def __init__( self, params, account_settings ):
        self._account_settings = account_settings
        self._client = XBMCDropBoxClient(access_token=self._account_settings.access_token)
        #get Settings
        self._filterFiles = ('true' == ADDON.getSetting('filefilter').lower())
        self._useStreamingURLs = ('true' == ADDON.getSetting('streammedia').lower())
        self._enabledSync = self._account_settings.synchronisation
        self._localSyncPath = self._account_settings.syncpath
        self._remoteSyncPath = self._account_settings.remotepath
        cache_path = get_cache_path( self._account_settings.account_name )
        self._shadowPath = cache_path + '/shadow/'
        self._thumbPath = cache_path + '/thumb/'
        #form default url
        self._nrOfMediaItems = int( params.get('media_items', '%s'%MAX_MEDIA_ITEMS_TO_LOAD_ONCE) )
        self._module = params.get('module', '')
        self._contentType = params.get('content_type', 'executable')
        self._current_path = urllib.unquote( params.get('path', DROPBOX_SEP) ).decode("utf-8")
        #Add sorting options
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_FILE)
        #Set/change 'SessionId' to let the other FolderBrowser know that it has to quit... 
        self._session = str( uuid.uuid4() ) #generate unique session id
        self.win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.win.setProperty('SessionId', self._session)
        xbmc.sleep(100)

    def buildList(self, contents):
        self._totalItems = len(contents)
        if self._totalItems > 0:
            #create and start the thread that will download the files
            self._loader = FileLoader(self._client, self._module, self._shadowPath, self._thumbPath)
        #first add all the folders
        folderItems = 0
        for f in contents:
            if f['is_dir']:
                name = os.path.basename( path_from(f['path']) )
                # the metadata 'path' is sometimes case incorrect! So use the _current_path (case-sensitive) path.
                if self._current_path == DROPBOX_SEP:
                    fpath = self._current_path + name 
                else:
                    fpath = self._current_path + DROPBOX_SEP + name
                self.addFolder(name, fpath)
                folderItems += 1
        #Change the totalItems, so that the progressbar is more realistic
        self._totalItems = folderItems + self._nrOfMediaItems
        #Now add the maximum(define) number of files
        for fileMeta in contents:
            if not fileMeta['is_dir']:
                name = os.path.basename( path_from(fileMeta['path']) )
                # the metadata 'path' is sometimes case incorrect! So use the _current_path (case-sensitive) path.
                if self._current_path == DROPBOX_SEP:
                    fpath = self._current_path + name
                else:
                    fpath = self._current_path + DROPBOX_SEP + name
                self.addFile(name, fpath, fileMeta)
            if self._loadedMediaItems >= self._nrOfMediaItems:
                #don't load more for now
                break;
        #Add a "show more" item, for loading more if required
        if self._loadedMediaItems >= self._nrOfMediaItems:
            media_items = self._loadedMediaItems+MAX_MEDIA_ITEMS_TO_LOAD_ONCE
            url = self.getUrl(self._current_path, media_items=media_items)
            listItem = xbmcgui.ListItem( LANGUAGE_STRING(30010) )
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=False, totalItems=self._totalItems)
        
    def show(self, cacheToDisc=True, succeeded=True):
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=succeeded, cacheToDisc=cacheToDisc)
        if self._loader:
            self._loader.start()
            #now wait for the FileLoader
            #We cannot run the FileLoader standalone (without) this plugin(script)
            # for that we would need to use the xbmc.abortRequested, which becomes
            # True as soon as we exit this plugin(script)
            self._loader.stopWhenFinished = True
            while self._loader.isAlive():
                if self.mustStop():
                    #force the thread to stop
                    self._loader.stop()
                    #Wait for the thread
                    self._loader.join(4) #after 5 secs it will be killed any way by XBMC
                    break
                xbmc.sleep(100)
 
    def mustStop(self):
        '''When xbmc quits or the plugin(visible menu) is changed, stop this thread'''
        #win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        session = self.win.getProperty('SessionId')
        if xbmc.abortRequested:
            log_debug("xbmc.abortRequested")
            return True
        elif session != self._session:
            log_debug("SessionId changed")
            return True
        else:
            return False

    def addFile(self, name, path, meta):
        url = None
        listItem = None
        #print "path: %s" % path
        #print "meta: ", meta
        mediatype = ''
        iconImage = 'DefaultFile.png'
        if self._contentType == 'executable' or not self._filterFiles:
            mediatype = 'other'
            iconImage = 'DefaultFile.png'
            if 'image' in meta['mime_type']:
                mediatype = 'pictures'
                iconImage = 'DefaultImage.png'
            elif 'video' in meta['mime_type']:
                mediatype = 'video'
                iconImage = 'DefaultVideo.png'
            elif 'audio' in meta['mime_type']:
                mediatype = 'music'
                iconImage = 'DefaultAudio.png'
        if (self._contentType == 'image'):
            if 'image' in meta['mime_type']:
                mediatype = 'pictures'
                iconImage = 'DefaultImage.png'
        elif (self._contentType == 'video' or self._contentType == 'image'):
            if 'video' in meta['mime_type']:
                mediatype = 'video'
                iconImage = 'DefaultVideo.png'
        elif (self._contentType == 'audio'):
            if 'audio' in meta['mime_type']:
                mediatype = 'music'
                iconImage = 'DefaultAudio.png'
        if mediatype != '':
            listItem = xbmcgui.ListItem(name, iconImage=iconImage)
            self.metadata2ItemInfo(listItem, meta, mediatype)
            if self._enabledSync and self._remoteSyncPath in path:
                #Use the synchronized location for url
                self._loadedMediaItems += 1
                url = getLocalSyncPath(self._localSyncPath, self._remoteSyncPath, path)
            elif mediatype in ['pictures','video','music']:
                self._loadedMediaItems += 1
                tumb = self._loader.getThumbnail(path, meta)
                if tumb:
                    listItem.setThumbnailImage(tumb)
                if self._useStreamingURLs and mediatype in ['video','music']:
                    #this doesn't work for pictures...
                    listItem.setProperty("IsPlayable", "true")
                    url = sys.argv[0] + '?action=play' + '&path=' + urllib.quote(path.encode("utf-8"))
                    url += '&account=' + urllib.quote(self._account_settings.account_name.encode("utf-8"))
                else:
                    url = self._loader.getFile(path)
                    #url = self.getMediaUrl(path)
            else:
                listItem.setProperty("IsPlayable", "false")
                url='No action'
            if listItem:
                contextMenuItems = []
                searchUrl = self.getUrl(self._current_path, module='search_dropbox')
                contextMenuItems.append( (LANGUAGE_STRING(30017), 'XBMC.RunPlugin(%s)'%searchUrl))
                contextMenuItems.append( (LANGUAGE_STRING(30022), self.getContextUrl(path, 'delete') ) )
                contextMenuItems.append( (LANGUAGE_STRING(30024), self.getContextUrl(path, 'copy') ) )
                contextMenuItems.append( (LANGUAGE_STRING(30027), self.getContextUrl(path, 'move') ) )
                contextMenuItems.append( (LANGUAGE_STRING(30029), self.getContextUrl(self._current_path, 'create_folder') ) )
                contextMenuItems.append( (LANGUAGE_STRING(30031), self.getContextUrl(self._current_path, 'upload') ) )
                contextMenuItems.append( (LANGUAGE_STRING(30037), self.getContextUrl(path, 'download', extra='isDir=False') ) )
                if self._enabledSync and self._remoteSyncPath in path:
                    contextMenuItems.append( (LANGUAGE_STRING(30112), self.getContextUrl(self._current_path, 'sync_now') ) )
                listItem.addContextMenuItems(contextMenuItems, replaceItems=True)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=False, totalItems=self._totalItems)
    
    def addFolder(self, name, path):
        url=self.getUrl(path, module='browse_folder')
        listItem = xbmcgui.ListItem(name,iconImage='DefaultFolder.png', thumbnailImage='DefaultFolder.png')
        listItem.setInfo( type='pictures', infoLabels={'Title': name} )
        contextMenuItems = []
        searchUrl = self.getUrl(path, module='search_dropbox')
        contextMenuItems.append( (LANGUAGE_STRING(30017), 'XBMC.RunPlugin(%s)'%searchUrl))
        contextMenuItems.append( (LANGUAGE_STRING(30022), self.getContextUrl(path, 'delete') ) )
        contextMenuItems.append( (LANGUAGE_STRING(30024), self.getContextUrl(path, 'copy') ) )
        contextMenuItems.append( (LANGUAGE_STRING(30027), self.getContextUrl(path, 'move') ) )
        contextMenuItems.append( (LANGUAGE_STRING(30029), self.getContextUrl(path, 'create_folder') ) )
        contextMenuItems.append( (LANGUAGE_STRING(30031), self.getContextUrl(path, 'upload') ) )
        contextMenuItems.append( (LANGUAGE_STRING(30037), self.getContextUrl(path, 'download', extra='isDir=True') ) )
        if self._enabledSync and self._remoteSyncPath in path:
            contextMenuItems.append( (LANGUAGE_STRING(30112), self.getContextUrl(path, 'sync_now') ) )
        listItem.addContextMenuItems(contextMenuItems, replaceItems=True)
        #no useful metadata of folder
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True, totalItems=self._totalItems)

    def getUrl(self, path, media_items=0, module=None):
        url = sys.argv[0]
        url += '?content_type=' + self._contentType
        if module:
            url += '&module=' + module
        else:
            url += '&module=' + self._module
        url += '&account=' + urllib.quote(self._account_settings.account_name.encode("utf-8"))
        url += '&path=' + urllib.quote(path.encode("utf-8"))
        if media_items != 0:
            url += '&media_items=' + str(media_items)
        return url

    def getContextUrl(self, path, action, extra = None):
        url = 'XBMC.RunScript(plugin.dbmc, '
        url += 'action=%s' %( action )
        url += '&account=' + urllib.quote(self._account_settings.account_name.encode("utf-8"))
        if action == 'upload':
            url += '&to_path=%s' %( urllib.quote(path.encode("utf-8")) )
        else:
            url += '&path=%s' %( urllib.quote(path.encode("utf-8")) )
        if extra:
            url += '&' + extra
        url += ')'
        return url
        
    def metadata2ItemInfo(self, item, metadata, mediatype):
        # example metadata from Dropbox 
        #'rev': 'a7d0389464b',
        #'thumb_exists': False,
        #'path': '/Music/Backspacer/11 - The End.mp3',
        #'is_dir': False,
        #'client_mtime': 'Sat, 27 Feb 2010 11:55:43 +0000'
        #'icon': 'page_white_sound',
        #'bytes': 4260601,
        #'modified': 'Thu, 28 Jun 2012 17:55:59 +0000',
        #'size': '4.1 MB',
        #'root': 'dropbox',
        #'mime_type': 'audio/mpeg',
        #'revision': 2685
        info = {}
        #added value for picture is only the size. the other data is retrieved from the photo itself...
        if mediatype == 'other':
            mediatype = 'pictures' #fake to get more info on the item...
        if mediatype == 'pictures':
            info['size'] = str(metadata['bytes'])
            info['title'] = path_from(metadata['path'])
        # For video and music, nothing interesting...
        # elif mediatype == 'video':
        # elif mediatype == 'music':

        if len(info) > 0: item.setInfo(mediatype, info)
        
    def getMetaData(self, path, directory=False):
        meta, changed = self._client.getMetaData(path, directory)
        if changed:
            self._removeCachedFileFolder(path, meta)
        return meta

    def _removeCachedFileFolder(self, path, metadata):
        cachedLocation = self._shadowPath + path
        cachedLocation = os.path.normpath(cachedLocation)
        tumbLocation = self._thumbPath + path
        tumbLocation = os.path.normpath(tumbLocation)
        folderItems = []
        fileItems = []
        if xbmcvfs.exists(cachedLocation.encode("utf-8")) or xbmcvfs.exists(tumbLocation.encode("utf-8")):
            #folderItems = (os.path.basename(item['path']) for item in metadata['contents'] if item['is_dir']) if folder not in folderitems of generator expression does not work...
            for item in metadata['contents']:
                if item['is_dir']:
                    folderItems.append(os.path.basename(path_from(item['path'])))
                else:
                    fileItems.append(os.path.basename(path_from(item['path'])))
        #remove shadow files/folders
        if xbmcvfs.exists(cachedLocation.encode("utf-8")):
            for f in os.listdir(cachedLocation):
                #check if folders/files needs to be removed
                fName = os.path.join(cachedLocation, f)
                if not os.path.isfile(fName):
                    if f not in folderItems:
                        log_debug('Removing cached folder: %s' % (fName))
                        shutil.rmtree(fName)
                else:
                    if f not in fileItems:
                        log_debug('Removing cached file: %s' % (fName))
                        os.remove(fName)
        #remove tumb files/folders
        if xbmcvfs.exists(tumbLocation.encode("utf-8")):
            #first replace the tumb file extention
            for i, f in enumerate(fileItems):
                fileItems[i] = replaceFileExtension(f, 'jpg')
            for f in os.listdir(tumbLocation):
                #check if folders/files needs to be removed
                fName = os.path.join(tumbLocation, f)
                if not os.path.isfile(fName):
                    if f not in folderItems:
                        log_debug('Removing tumb folder: %s' % (fName))
                        shutil.rmtree(fName)
                else:
                    if f not in fileItems:
                        log_debug('Removing tumb file: %s' % (fName))
                        os.remove(fName)


class FileLoader(threading.Thread):
    _stop = False
    stopWhenFinished = False
    _itemsHandled = 0
    _itemsTotal = 0
    
    def __init__( self, client, module, shadowPath, thumbPath):
        super(FileLoader, self).__init__()
        self._shadowPath = shadowPath
        self._thumbPath = thumbPath
        self._client = client
        self._module = module
        self._thumbList = Queue.Queue() #thread safe
        self._fileList = Queue.Queue() #thread safe
        self._progress = DropboxBackgroundProgress("DialogExtendedProgressBar.xml", ADDON_PATH)
        self._progress.setHeading(LANGUAGE_STRING(30035))

    def run(self):
        #check if need to quit
        log_debug("FileLoader started for: %s"%self._module)
        if self._itemsTotal > 0:
            self._progress.show()
        while not self._stop and not self.ready():
            #First get all the thumbnails(priority), then all the original files
            thumb2Retrieve = None
            file2Retrieve = None
            if not self._thumbList.empty():
                thumb2Retrieve = self._thumbList.get()
            elif not self._fileList.empty():
                file2Retrieve = self._fileList.get()
            self._progress.update(self._itemsHandled, self._itemsTotal)
            if thumb2Retrieve:
                location = self._getThumbLocation(thumb2Retrieve)
                #Check if thumb already exists
                # TODO: use database checking for this!
                if not xbmcvfs.exists(location.encode("utf-8")):
                    #Doesn't exist so download it.
                    self._getThumbnail(thumb2Retrieve)
                else:
                    log_debug("Thumbnail already downloaded: %s"%location)
                self._itemsHandled += 1
            elif file2Retrieve:
                location = self._getShadowLocation(file2Retrieve)
                #Check if thumb already exists
                #TODO: use database checking for this!
                if not xbmcvfs.exists(location.encode("utf-8")):
                    #Doesn't exist so download it.
                    self._getFile(file2Retrieve)
                else:
                    log_debug("Original file already downloaded: %s"%location)
                self._itemsHandled += 1
            time.sleep(0.100)
        if self._itemsTotal > 0:
            self._progress.update(self._itemsHandled, self._itemsTotal)
            self._progress.close()
        if self._stop:
            log_debug("FileLoader stopped (as requested) for: %s"%self._module)
        else:
            log_debug("FileLoader finished for: %s"%self._module)
        del self._progress
        
    def stop(self):
        self._stop = True
        
    def ready(self):
        if self.stopWhenFinished and ( self._thumbList.empty() and self._fileList.empty() ):
            return True
        else:
            return False
        
    def getThumbnail(self, path, metadata):
        if metadata['thumb_exists']:
            self._thumbList.put(path)
            self._itemsTotal += 1
            return self._getThumbLocation(path)
        else:
            return None

    def getFile(self, path):
        self._fileList.put(path)
        self._itemsTotal += 1
        return self._getShadowLocation(path)
    
    def _getThumbLocation(self, path):
        #jpeg (default) or png. For images that are photos, jpeg should be preferred, while png is better for screenshots and digital art.
        location = replaceFileExtension(path, 'jpg')
        location = self._thumbPath + location
        location = os.path.normpath(location)
        return location

    def _getThumbnail(self, path):
        location = self._getThumbLocation(path)
        self._client.saveThumbnail(path, location)
        return location

    def _getShadowLocation(self, path):
        location = self._shadowPath + path
        location = os.path.normpath(location)
        return location
    
    def _getFile(self, path):
        location = self._getShadowLocation(path)
        self._client.saveFile(path, location)
        return location
