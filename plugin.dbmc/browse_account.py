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
import shutil
import os

from resources.lib.utils import *
from resources.lib.dropboxclient import *
from resources.lib.accountsettings import AccountSettings
from resources.lib.sync.notifysync import NotifySyncClient
import resources.lib.login as login

class AccountBrowser(object):
    '''
    Shows the list of account to the user and implements all the account features:
    - Showing the current accounts
    - Converting old addon settings to new account settings
    - add/remove/rename accounts
    ''' 

    def __init__( self, params ):
        self._content_type = params.get('content_type', 'executable')
        #check if the accounts directory is present, create otherwise
        # keep dataPath "utf-8" encoded
        dataPath = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode("utf-8")
        self._accounts_dir = dataPath + u'/accounts/'
        if not xbmcvfs.exists( self._accounts_dir.encode("utf-8") ):
            xbmcvfs.mkdirs( self._accounts_dir.encode("utf-8") )
        #Check if we need to get previous account settings from old addon settings
        if ADDON.getSetting('access_token').decode("utf-8") != u'':
            #Old access_token present so convert old settings!
            log('Converting old account settings and saving it')
            account_name = u'Account1'
            access_token = ADDON.getSetting('access_token').decode("utf-8")
            client = XBMCDropBoxClient(access_token=access_token)
            account_info = client.getAccountInfo()
            if 'display_name' in account_info:
                account_name = path_from(account_info['display_name'])
            new_account = AccountSettings(account_name)
            new_account.access_token = ADDON.getSetting('access_token').decode("utf-8")
            new_account.passcode = ADDON.getSetting('passcode')
            passcodetimeout = ADDON.getSetting('passcodetimeout')
            if passcodetimeout != '':
                new_account.passcodetimeout = int( passcodetimeout )
            #new_account.session_id = tmp_dict.session_id
            new_account.synchronisation = ('true' == ADDON.getSetting('synchronisation').lower())
            syncfreq = ADDON.getSetting('syncfreq')
            if syncfreq != '':
                new_account.syncfreq = int( syncfreq )
            new_account.syncpath = ADDON.getSetting('syncpath').decode("utf-8")
            new_account.remotepath = ADDON.getSetting('remotepath').decode("utf-8")
            new_account.save()
            #Now clear all old settings
            ADDON.setSetting('access_token', '')
            ADDON.setSetting('passcode', '')
            ADDON.setSetting('passcodetimeout', '')
            ADDON.setSetting('synchronisation', 'false')
            ADDON.setSetting('syncpath', '')
            ADDON.setSetting('remotepath', '')
            #cleanup old cache and shadow dirs
            #keep cache_path "utf-8" encoded
            cache_path = ADDON.getSetting('cachepath')
            #Use user defined location?
            if cache_path == '' or os.path.normpath(cache_path) == '':
                #get the default path 
                cache_path = xbmc.translatePath( ADDON.getAddonInfo('profile') )
            shadowPath = os.path.normpath(cache_path + '/shadow/')
            thumbPath = os.path.normpath(cache_path + '/thumb/')
            if xbmcvfs.exists(shadowPath.encode("utf-8")):
                shutil.rmtree(shadowPath)
            if xbmcvfs.exists(thumbPath.encode("utf-8")):
                shutil.rmtree(thumbPath)
            #Notify the DropboxSynchronizer of the new account
            NotifySyncClient().account_added_removed()


    def buildList(self):
        #get the present accounts (in unicode!)
        names = os.listdir(self._accounts_dir.decode("utf-8"))
        for name in names:
            self.add_account(name)
        #add the account action items
        sessionId = ADDON.getSetting('session_id').decode("utf-8")
        if sessionId == '':
            #add new account
            self.add_action(LANGUAGE_STRING(30042), 'add')
        else:
            #finish adding account
            self.add_action(LANGUAGE_STRING(30043), 'add')

    def show(self):
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def add_account(self, name):
        iconImage = 'DefaultFile.png'
        if self._content_type == 'audio':
            iconImage = 'DefaultAddonMusic.png'
        elif self._content_type == 'video':
            iconImage = 'DefaultAddonVideo.png'
        elif self._content_type == 'image':
            iconImage = 'DefaultAddonPicture.png'
        listItem = xbmcgui.ListItem(name.encode("utf-8"), iconImage=iconImage, thumbnailImage=iconImage)
        #Create the url
        url = sys.argv[0]
        url += '?content_type=' + self._content_type
        url += "&module=" + 'browse_folder'
        url +="&account=" + urllib.quote(name.encode("utf-8"))
        #Add a context menu item
        contextMenuItems = []
        contextMenuItems.append( (LANGUAGE_STRING(30044), self.getContextUrl('remove', name) ) )
        contextMenuItems.append( (LANGUAGE_STRING(30012), self.getContextUrl('change_passcode', name) ) )
        contextMenuItems.append( (LANGUAGE_STRING(30100), self.getContextUrl('change_synchronization', name) ) )
        listItem.addContextMenuItems(contextMenuItems, replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True)

    def add_action(self, name, action):
        iconImage='DefaultAddSource.png'
        listItem = xbmcgui.ListItem(name, iconImage=iconImage, thumbnailImage=iconImage)
        #Create the url
        url = sys.argv[0]
        url += '?content_type=' + self._content_type
        url += "&module=" + 'browse_account'
        url +="&action=" + 'add'
        contextMenuItems = []
        listItem.addContextMenuItems(contextMenuItems, replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listItem, isFolder=True)

    def getContextUrl(self, action, account_name):
        url = 'XBMC.RunPlugin(plugin://plugin.dbmc/?'
        url += 'action=%s' %( action )
        url += "&module=" + 'browse_account'
        url += '&account=' + urllib.quote(account_name.encode("utf-8"))
        url += ')'
        return url

def change_passcode(account_settings):
    log_debug('Changing passcode for account: %s' % (account_settings.account_name))
    enable_passcode = False
    #enable/disable passcode?
    dialog = xbmcgui.Dialog()
    if dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30011), account_settings.account_name + '?' ) == True:
         enable_passcode = True
    log_debug('Passcode enabled: %s' % (enable_passcode))
    #Change the code
    if enable_passcode:
        keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30034))
        keyboard.setHiddenInput(True)
        keyboard.doModal()
        if keyboard.isConfirmed():
            account_settings.passcode = keyboard.getText()
            log_debug('Passcode set')
            login.clear_unlock(account_settings)
            #set the timeout time
            valid_timeout = False
            dialog = xbmcgui.Dialog()
            while not valid_timeout:
                #0 = ShowAndGetNumber
                timeout_str = dialog.numeric(0, LANGUAGE_STRING(30015), str(account_settings.passcodetimeout) )
                try:
                    #check for a vaild timeout
                    timeout = int(timeout_str)
                except ValueError:
                    timeout = -1
                if 1 <= timeout <= 120:
                    account_settings.passcodetimeout = timeout
                    log_debug('Passcode timeout set: %s' % (timeout))
                    valid_timeout = True
                else:
                    log_debug('Wrong timeout value')
                    #Wrong timeout
                    dialog = xbmcgui.Dialog()
                    dialog.ok(ADDON_NAME, LANGUAGE_STRING(30207))
            account_settings.save()
    else:
        account_settings.passcode = ''
        account_settings.save()
        login.clear_unlock(account_settings)

def change_synchronization(account_settings):
    log_debug('Changing synchronization for account: %s' % (account_settings.account_name))
    account_settings.synchronisation = False
    sync_settings_valid = False
    #Enable synchronization?
    dialog = xbmcgui.Dialog()
    if dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30101), account_settings.account_name + '?' ) == True:
         account_settings.synchronisation = True
    log_debug('Synchronization enabled: %s' % (account_settings.synchronisation) )
    if account_settings.synchronisation:
        #select the local folder
        dialog = xbmcgui.Dialog()
        # 3= ShowAndGetWriteableDirectory, 
        selected_folder = dialog.browse(3, LANGUAGE_STRING(30102), 'files', mask='', treatAsFolder=True, defaultt=account_settings.syncpath)
        selected_folder = selected_folder.decode("utf-8")
        log_debug('Selected local folder: %s' % (selected_folder) )
        if selected_folder != u'':
            account_settings.syncpath = selected_folder
            from resources.lib.dropboxfilebrowser import DropboxFileBrowser
            #select the remote folder
            dialog = DropboxFileBrowser("FileBrowser.xml", ADDON_PATH)
            client = XBMCDropBoxClient(access_token=account_settings.access_token)
            dialog.setDBClient(client)
            dialog.setHeading(LANGUAGE_STRING(30109), account_settings.remotepath)
            dialog.doModal()
            log_debug('Selected remote folder: %s' % (dialog.selectedFolder) )
            if dialog.selectedFolder:
                account_settings.remotepath = dialog.selectedFolder
                #set synchronization frequency
                dialog = xbmcgui.Dialog()
                valid_freq = False
                while not valid_freq:
                    #0 = ShowAndGetNumber
                    freq_str = dialog.numeric(0, LANGUAGE_STRING(30105), str(account_settings.syncfreq) )
                    try:
                        #check for a vaild freq
                        freq = int(freq_str)
                    except ValueError:
                        freq = -1
                    if 5 <= freq <= 1440:
                        account_settings.syncfreq = freq
                        log_debug('Synchronization frequency set: %s' % (freq))
                        valid_freq = True
                    else:
                        log_debug('Wrong frequency value')
                        #Wrong timeout
                        dialog = xbmcgui.Dialog()
                        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30208))
                #done
                sync_settings_valid = True
    else:
        sync_settings_valid = True
    if sync_settings_valid:
        account_settings.save()
        #Notify the DropboxSynchronizer
        NotifySyncClient().account_settings_changed(account_settings)


def run(params): # This is the entrypoint
    action = params.get('action', '')
    if action == 'add':
        #add an account
        access_token = login.getAccessToken()
        if access_token:
            #save the new account
            account_name = 'Account1'
            client = XBMCDropBoxClient(access_token=access_token)
            account_info = client.getAccountInfo()
            if 'display_name' in account_info:
                account_name = path_from(account_info['display_name'])
            new_account = AccountSettings(account_name)
            new_account.access_token = access_token
            new_account.save()
            #Notify the DropboxSynchronizer
            NotifySyncClient().account_added_removed()
            #notify the user the account is added
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30004), account_name)
        #return to where we were and refresh
        xbmc.executebuiltin('container.Refresh()')
    elif action == 'remove':
        #remove the selected account
        account_name = urllib.unquote( params.get('account', '') )
        account_settings = login.get_account(account_name) 
        if account_settings:
            dialog = xbmcgui.Dialog()
            #'are you sure' dialog
            if dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30045), account_name ) == True:
                try:
                    account_settings.remove()
                except Exception as exc:
                    log_error("Failed to remove the account: %s" % (str(exc)) )
                else:
                    #Notify the DropboxSynchronizer
                    NotifySyncClient().account_added_removed()
        else:
            log_error("Failed to remove the account!")
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30203))
        #return to where we were and refresh
        xbmc.executebuiltin('container.Refresh()')
    elif action == 'change_passcode':
        account_name = urllib.unquote( params.get('account', '') )
        account_settings = login.get_account(account_name)
        if account_settings:
            change_passcode(account_settings)
        #return to where we were
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
    elif action == 'change_synchronization':
        account_name = urllib.unquote( params.get('account', '') )
        account_settings = login.get_account(account_name)
        if account_settings:
            change_synchronization(account_settings)
        #return to where we were
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
    else:
        browser = AccountBrowser(params)
        browser.buildList()
        browser.show()
