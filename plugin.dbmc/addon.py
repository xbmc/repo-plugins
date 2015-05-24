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

import time

from resources.lib.utils import *
from resources.lib.dropboxclient import XBMCDropBoxClient, Downloader
from resources.lib.dropboxfilebrowser import DropboxFileBrowser
from resources.lib.sync.notifysync import NotifySyncClient
import resources.lib.login as login

if ( __name__ == "__main__" ):
    log_debug('Argument List: %s' % str(sys.argv))
    runAsScript, params = parse_argv()
    if not runAsScript:
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
            if 'module' in params: # Module chosen, load and execute module
                module = params['module']
                __import__(module)
                current_module = sys.modules[module]
                current_module.run(params)
            elif 'action' in params and params['action'] == 'play':
                account_name = urllib.unquote( params.get('account', '') ).decode("utf-8")
                account_settings = login.get_account(account_name) 
                if account_settings:
                    client = XBMCDropBoxClient(access_token=account_settings.access_token)
                    item = urllib.unquote( urllib.unquote( params['path'] ) ).decode("utf-8")
                    url = client.getMediaUrl(item)
                    log_debug('MediaUrl: %s'%url)
                    listItem = xbmcgui.ListItem(item)
                    listItem.select(True)
                    listItem.setPath(url)
                    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listItem)
                else:
                    log_error("Action play: no account name provided!")
                    xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
            else: # No module chosen
                #Run the browse_folder module
                module = 'browse_account'
                params['module'] = module
                __import__(module)
                current_module = sys.modules[module]
                current_module.run(params)
    else: # run as script
        account_name = urllib.unquote( params.get('account', '') ).decode("utf-8")
        account_settings = login.get_account(account_name) 
        if account_settings:
            #All actions below require an XBMCDropBoxClient
            client = XBMCDropBoxClient(access_token=account_settings.access_token)
            action = params.get('action', '')
            if action == 'delete':
                if 'path' in params:
                    path = urllib.unquote( params['path'] ).decode("utf-8")
                    dialog = xbmcgui.Dialog()
                    if dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30023), path ) == True:
                        success = client.delete(path)
                        if success:
                            log('File removed: %s' % path)
                            NotifySyncClient().sync_path(account_settings, path)
                        else:
                            log_error('File removed Failed: %s' % path)
                        xbmc.executebuiltin('container.Refresh()')
            elif action == 'copy':
                if 'path' in params:
                    path = urllib.unquote( params['path'] ).decode("utf-8")
                    dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
                    dialog.setDBClient(client)
                    dialog.setHeading(LANGUAGE_STRING(30025) + LANGUAGE_STRING(30026))
                    dialog.doModal()
                    if dialog.selectedFolder:
                        #dropbox path -> don't use os.path.join()!
                        toPath = dialog.selectedFolder
                        if dialog.selectedFolder[-1:] != DROPBOX_SEP: toPath += DROPBOX_SEP
                        toPath += os.path.basename(path)
                        success = client.copy(path, toPath)
                        if success:
                            log('File copied: %s to %s' % (path, toPath) ) 
                            NotifySyncClient().sync_path(account_settings, toPath)
                        else:
                            log_error('File copy Failed: %s to %s' % (path, toPath) )
                    del dialog
            elif action == 'move':
                if 'path' in params:
                    path = urllib.unquote( params['path'] ).decode("utf-8")
                    dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
                    dialog.setDBClient(client)
                    dialog.setHeading(LANGUAGE_STRING(30025) + LANGUAGE_STRING(30028))
                    dialog.doModal()
                    if dialog.selectedFolder:
                        #dropbox path -> don't use os.path.join()!
                        toPath = dialog.selectedFolder
                        if dialog.selectedFolder[-1:] != DROPBOX_SEP: toPath += DROPBOX_SEP
                        toPath += os.path.basename(path)
                        success = client.move(path, toPath)
                        if success:
                            log('File moved: from %s to %s' % (path, toPath) ) 
                            xbmc.executebuiltin('container.Refresh()')
                            NotifySyncClient().sync_path(account_settings, path)
                            NotifySyncClient().sync_path(account_settings, toPath)
                        else:
                            log_error('File move Failed: from %s to %s' % (path, toPath) )
                    del dialog
            elif action == 'create_folder':
                if 'path' in params:
                    path = urllib.unquote( params['path'] ).decode("utf-8")
                    keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30030))
                    keyboard.doModal()
                    if keyboard.isConfirmed():
                        newFolder = path
                        if path[-1:] != DROPBOX_SEP: newFolder += DROPBOX_SEP
                        newFolder += unicode(keyboard.getText(), "utf-8")
                        success = client.createFolder(newFolder)
                        if success:
                            log('New folder created: %s' % newFolder)
                            xbmc.executebuiltin('container.Refresh()')
                            NotifySyncClient().sync_path(account_settings, newFolder)
                        else:
                            log_error('Creating new folder Failed: %s' % newFolder)
            elif action == 'upload':
                if 'to_path' in params:
                    toPath = urllib.unquote( params['to_path'] ).decode("utf-8")
                    dialog = xbmcgui.Dialog()
                    fileName = dialog.browse(1, LANGUAGE_STRING(30032), 'files').decode("utf-8")
                    if fileName:
                        success = client.upload(fileName, toPath, dialog=True)
                        if success:
                            log('File uploaded: %s to %s' % (fileName, toPath) )
                            xbmc.executebuiltin('container.Refresh()')
                            NotifySyncClient().sync_path(account_settings, toPath)
                        else:
                            log_error('File uploading Failed: %s to %s' % (fileName, toPath))
            elif action == 'download':
                if 'path' in params:
                    path = urllib.unquote( params['path'] ).decode("utf-8")
                    isDir = ('true' == params['isDir'].lower())
                    dialog = xbmcgui.Dialog()
                    location = dialog.browse(3, LANGUAGE_STRING(30025) + LANGUAGE_STRING(30038), 'files').decode("utf-8")
                    if location:
                        success = True
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
            elif action == 'sync_now':
                path = urllib.unquote( params['path'] ).decode("utf-8")
                NotifySyncClient().sync_path(account_settings, path)
            else:
                log_error('Unknown action received: %s' % (action))
        else:
            log_error("Run as script: no account name provided!")
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30203))
            #script So sys.argv[1] id not a handle... Don't execute the next!
            #xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)

