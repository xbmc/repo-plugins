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
import xbmcvfs

import time

from resources.lib.utils import *
from resources.lib.dropboxclient import XBMCDropBoxClient, Downloader
from resources.lib.dropboxfilebrowser import DropboxFileBrowser
from resources.lib.notifysync import NotifySyncClient

def addDir(name, module, contentType, iconImage=''):
    url = sys.argv[0]
    url += '?content_type=' + contentType
    url += "&module=" + module
    if iconImage == '':
        if contentType == 'audio':
            iconImage = 'DefaultAddonMusic.png'
        elif contentType == 'video':
            iconImage = 'DefaultAddonVideo.png'
        elif contentType == 'image':
            iconImage = 'DefaultAddonPicture.png'
    listItem = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True)

def unlock():
    unlocked = True
    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    if (ADDON.getSetting('passcode') != ''):
        unlockTimeout = float( ADDON.getSetting('passcodetimeout') ) * 60 # to minutes
        try:
            unlockedTime = float( win.getProperty('Unlocked') )
        except ValueError:
            unlockedTime = 0.0
        #unlocked = True when timeout not expired
        unlocked = (time.time() < (unlockedTime + unlockTimeout) )
        if not unlocked:
            log('Unlock with passcode required...')
            keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30013))
            keyboard.setHiddenInput(True)
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText() == ADDON.getSetting('passcode'):
                unlocked = True
            else:
                #Wrong passcode
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30014) )
    return unlocked

if ( __name__ == "__main__" ):
    log_debug('Argument List: %s' % str(sys.argv))
    runAsScript, params = parse_argv()
    if not runAsScript:
        gotToken = False
        if ADDON.getSetting('access_token').decode("utf-8") == '':
            import resources.lib.login as login
            if login.getAccessToken():
                #reload the addon
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30004))
                gotToken = True
        else:
            gotToken = True
        if gotToken:
            if int(sys.argv[1]) < 0:
                #handle action of a file (or a "Show me more..." item)
                if 'media_items' in params:
                    #Loading more media items requested...
                    path = sys.argv[0] + sys.argv[2]
                    #xbmc.executebuiltin('container.update(%s, replace)'%path) # don't use replace because that removes the content_type from the path...
                    xbmc.executebuiltin('container.update(%s)'%path)
                elif 'module' in params: # plugin (module) to run
                    path = sys.argv[0] + sys.argv[2]
                    xbmc.executebuiltin('container.update(%s)'%path)
            else:
                if unlock():
                    #update the unlock time
                    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
                    win.setProperty('Unlocked', '%s'%time.time() )
                    if 'module' in params: # Module chosen, load and execute module
                        module = params['module']
                        __import__(module)
                        current_module = sys.modules[module]
                        current_module.run(params)
                    elif 'action' in params and params['action'] == 'play':
                        client = XBMCDropBoxClient()
                        item = urllib.unquote( urllib.unquote( params['path'] ) )
                        url = client.getMediaUrl(item)
                        log_debug('MediaUrl: %s'%url)
                        listItem = xbmcgui.ListItem(item)
                        listItem.select(True)
                        listItem.setPath(url)
                        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listItem)
                    else: # No module chosen
                        if False: #list modules, creates an extra menu for dropbox addon, but for now, do not use...
                            contentType = params.get('content_type', 'all')
                            addDir(LANGUAGE_STRING(30016), 'browse_folder', contentType)
                            addDir(LANGUAGE_STRING(30017), 'search_dropbox', contentType, iconImage='DefaultAddonProgram.png')
                            # Add extra modules here, using addDir(name, module)
                            xbmcplugin.endOfDirectory(int(sys.argv[1]))
                        else:
                            #Run the browse_folder module
                            module = 'browse_folder'
                            params['module'] = module
                            __import__(module)
                            current_module = sys.modules[module]
                            current_module.run(params)
                else:
                    xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
        else:
            xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
    else: # run as script
        action = params.get('action', '')
        if action == 'clear_token':
            ADDON.setSetting('access_token', '')
        elif action == 'change_passcode':
            if unlock():
                keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30034))
                keyboard.setHiddenInput(True)
                keyboard.doModal()
                if keyboard.isConfirmed():
                    ADDON.setSetting('passcode', keyboard.getText())
        elif action == 'delete':
            if 'path' in params:
                path = urllib.unquote( params['path'] )
                dialog = xbmcgui.Dialog()
                if dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30023), path ) == True:
                    client = XBMCDropBoxClient()
                    success = client.delete(path)
                    if success:
                        log('File removed: %s' % path)
                        NotifySyncClient().notify(path)
                    else:
                        log_error('File removed Failed: %s' % path)
                    xbmc.executebuiltin('container.Refresh()')
        elif action == 'copy':
            if 'path' in params:
                path = urllib.unquote( params['path'] )
                dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
                dialog.setHeading(LANGUAGE_STRING(30025) + LANGUAGE_STRING(30026))
                dialog.doModal()
                if dialog.selectedFolder:
                    client = XBMCDropBoxClient()
                    #dropbox path -> don't use os.path.join()!
                    toPath = dialog.selectedFolder
                    if dialog.selectedFolder[-1:] != DROPBOX_SEP: toPath += DROPBOX_SEP
                    toPath += os.path.basename(path)
                    success = client.copy(path, toPath)
                    if success:
                        log('File copied: %s to %s' % (path, toPath) ) 
                        NotifySyncClient().notify(toPath)
                    else:
                        log_error('File copy Failed: %s to %s' % (path, toPath) )
                del dialog
        elif action == 'move':
            if 'path' in params:
                path = urllib.unquote( params['path'] )
                dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
                dialog.setHeading(LANGUAGE_STRING(30025) + LANGUAGE_STRING(30028))
                dialog.doModal()
                if dialog.selectedFolder:
                    client = XBMCDropBoxClient()
                    #dropbox path -> don't use os.path.join()!
                    toPath = dialog.selectedFolder
                    if dialog.selectedFolder[-1:] != DROPBOX_SEP: toPath += DROPBOX_SEP
                    toPath += os.path.basename(path)
                    success = client.move(path, toPath)
                    if success:
                        log('File moved: from %s to %s' % (path, toPath) ) 
                        xbmc.executebuiltin('container.Refresh()')
                        NotifySyncClient().notify(toPath)
                    else:
                        log_error('File move Failed: from %s to %s' % (path, toPath) )
                del dialog
        elif action == 'create_folder':
            if 'path' in params:
                path = urllib.unquote( params['path'] ).decode("utf-8")
                keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30030))
                keyboard.doModal()
                if keyboard.isConfirmed():
                    client = XBMCDropBoxClient()
                    newFolder = path
                    if path[-1:] != DROPBOX_SEP: newFolder += DROPBOX_SEP
                    newFolder += unicode(keyboard.getText(), "utf-8")
                    success = client.createFolder(newFolder)
                    if success:
                        log('New folder created: %s' % newFolder)
                        xbmc.executebuiltin('container.Refresh()')
                        NotifySyncClient().notify(newFolder)
                    else:
                        log_error('Creating new folder Failed: %s' % newFolder)
        elif action == 'upload':
            if 'to_path' in params:
                toPath = urllib.unquote( params['to_path'] )
                dialog = xbmcgui.Dialog()
                fileName = dialog.browse(1, LANGUAGE_STRING(30032), 'files')
                if fileName:
                    client = XBMCDropBoxClient()
                    success = client.upload(fileName, toPath, dialog=True)
                    if success:
                        log('File uploaded: %s to %s' % (fileName, toPath) )
                        xbmc.executebuiltin('container.Refresh()')
                        NotifySyncClient().notify(toPath)
                    else:
                        log_error('File uploading Failed: %s to %s' % (fileName, toPath))
        elif action == 'download':
            if 'path' in params:
                path = urllib.unquote( params['path'] )
                isDir = ('true' == params['isDir'].lower())
                dialog = xbmcgui.Dialog()
                location = dialog.browse(3, LANGUAGE_STRING(30025) + LANGUAGE_STRING(30038), 'files')
                if location:
                    success = True
                    client = XBMCDropBoxClient()
                    downloader = Downloader(client, path, location, isDir)
                    downloader.start()
                    #now wait for the FileLoader
                    downloader.stopWhenFinished = True
                    while downloader.isAlive():
                        xbmc.sleep(100)
                    #Wait for the thread
                    downloader.join()
                    if downloader.canceled:
                        log('Downloading canceled')
                    else:
                        log('Downloading finished')
                        dialog = xbmcgui.Dialog()
                        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30040), location)
        elif action == 'set_remote_sync_path':
            dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
            dialog.setHeading(LANGUAGE_STRING(30109))
            dialog.doModal()
            if dialog.selectedFolder:
                ADDON.setSetting('remotepath', dialog.selectedFolder)
            del dialog
            #open the Settings dialog again
            ADDON.openSettings()
        elif action == 'sync_now':
            path = urllib.unquote( params['path'] )
            NotifySyncClient().notify(path)
