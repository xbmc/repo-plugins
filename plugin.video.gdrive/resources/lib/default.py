'''
    CloudService XBMC Plugin
    Copyright (C) 2013-2014 ddurdle

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

import re
import sys
import os
import urllib, urllib2

KODI = True
if re.search(re.compile('.py', re.IGNORECASE), sys.argv[0]) is not None:
    KODI = False

if KODI:

    # cloudservice - standard XBMC modules
    import xbmc, xbmcgui, xbmcplugin, xbmcvfs
else:
    from resources.libgui import xbmcgui
    from resources.libgui import xbmcplugin
    from resources.libgui import xbmcvfs
    from resources.libgui import xbmc


from resources.lib import settings



def decode(data):
        return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
        for k, v in data.items():
            if type(v) is str or type(v) is unicode:
                data[k] = decode(v)
        return data

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


class contentengine(object):

    plugin_handle = None
    PLUGIN_URL = ''

    ##
    # load eclipse debugger
    #   parameters: none
    ##
    def debugger(self):
        try:

            remote_debugger = settings.getSetting('remote_debugger')
            remote_debugger_host = settings.getSetting('remote_debugger_host')

            # append pydev remote debugger
            if remote_debugger == 'true':
                # Make pydev debugger works for auto reload.
                # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
                import pysrc.pydevd as pydevd
                # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
                pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
        except ImportError:
            xbmc.log(self.addon.getLocalizedString(30016), xbmc.LOGERROR)
            sys.exit(1)
        except :
            return




    ##
    # add a menu to a directory screen
    #   parameters: url to resolve, title to display, optional: icon, fanart, total_items, instance name
    ##
    def addMenu(self, url, title, img='', fanart='', total_items=0, instanceName=''):
            #    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
            listitem = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            if not fanart and KODI:
                fanart = self.addon.getAddonInfo('path') + '/fanart.jpg'
            listitem.setProperty('fanart_image', fanart)

            # disallow play controls on menus
            listitem.setProperty('IsPlayable', 'false')


            if instanceName != '':
                cm=[]

                cm.append(( self.addon.getLocalizedString(30159), 'XBMC.RunPlugin('+self.PLUGIN_URL+ '?mode=delete&instance='+instanceName+')' ))

                listitem.addContextMenuItems(cm, True)



            xbmcplugin.addDirectoryItem(self.plugin_handle, url, listitem,
                                    isFolder=True, totalItems=total_items)



    ##
    # Providing a context type, return what content to display based on user's preferences
    #   parameters: current context type plugin was invoked in (audio, video, photos)
    ##
    def getContentType(self,contextType,encfs):

        #contentType
        #video context
        # 0 video
        # 1 video and music
        # 2 everything
        # 9 encrypted video
        #
        #music context
        # 3 music
        # 4 everything
        # 10 encrypted video
        #
        #photo context
        # 5 photo
        # 6 music and photos
        # 7 everything
        # 11 encrypted photo


          contentType = 0

          if contextType == 'video':

            if encfs:
                contentTypeDecider =  int(settings.getSettingInt('context_evideo',0))

                if contentTypeDecider == 1:
                    contentType = 8
                else:
                    contentType = 9

            else:
                contentTypeDecider = int(settings.getSettingInt('context_video',0))

                if contentTypeDecider == 2:
                    contentType = 2
                elif contentTypeDecider == 1:
                    contentType = 1
                else:
                    contentType = 0
            if KODI:
                # cloudservice - sorting options
                xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
                xbmcplugin.setContent(int(sys.argv[1]), 'movies')

          elif contextType == 'audio':
            if encfs:
                contentTypeDecider =  int(settings.getSettingInt('context_emusic',0))
                if contentTypeDecider == 1:
                    contentType = 8
                else:
                    contentType = 10
            else:

                contentTypeDecider = int(settings.getSettingInt('context_music', 0))

                if contentTypeDecider == 1:
                    contentType = 4
                else:
                    contentType = 3
            if KODI:
                # cloudservice - sorting options
                xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TRACKNUM)

          elif contextType == 'image':
            if encfs:
                contentTypeDecider =  int(settings.getSettingInt('context_ephoto',0))
                if contentTypeDecider == 1:
                    contentType = 8
                else:
                    contentType = 11
            else:
                contentTypeDecider = int(settings.getSettingInt('context_photo', 0))

                if contentTypeDecider == 2:
                    contentType = 7
                elif contentTypeDecider == 1:
                    contentType = 6
                else:
                    contentType = 5

          # show all (for encfs)
          elif contextType == 'all':
                contentType = 8


          return contentType



    ##
    #  get a list of offline files
    ##
    def getOfflineFileList(self,cachePath):

        localFiles = []


        #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
        if xbmcvfs.exists(cachePath) or os.path.exists(cachePath):
            dirs,files = xbmcvfs.listdir(cachePath)
            for dir in dirs:
                subdir,subfiles = xbmcvfs.listdir(str(cachePath) + '/' + str(dir))
                for file in subfiles:
                    if bool(re.search('\.stream\.mp4', file)):
                        try:
                            nameFile = xbmcvfs.File(str(cachePath) + '/' + str(dir) + '/' + str(dir) + '.name')
                            filename = nameFile.read()
                            nameFile.close()
                        except:
                            filename = file
                        try:
                            nameFile = xbmcvfs.File(str(cachePath) + '/' + str(dir) + '/' + str(os.path.splitext(file)[0]) + '.resolution')
                            resolution = nameFile.read()
                            nameFile.close()
                        except:
                            resolution = file
                        offlineFile = offlinefile.offlinefile(filename, str(cachePath) + '/' + str(dir) +'.jpg', resolution.rstrip(), str(cachePath) + '/' + str(dir) + '/' + str(os.path.splitext(file)[0]) + '.mp4')
                        localFiles.append(offlineFile)

        return localFiles


    ##
    # Add a media file to a directory listing screen
    #   parameters: package, context type, whether file is encfs, encfs:decryption path, encfs:encryption path
    ##
    def addOfflineMediaFile(self,offlinefile):
        listitem = xbmcgui.ListItem(offlinefile.title, iconImage=offlinefile.thumbnail,
                                thumbnailImage=offlinefile.thumbnail)

        if  offlinefile.resolution == 'original':
            infolabels = decode_dict({ 'title' : offlinefile.title})
        else:
            infolabels = decode_dict({ 'title' : offlinefile.title + ' - ' + offlinefile.resolution })
        listitem.setInfo('Video', infolabels)
        listitem.setProperty('IsPlayable', 'true')


        xbmcplugin.addDirectoryItem(self.plugin_handle, offlinefile.playbackpath, listitem,
                                isFolder=False, totalItems=0)
        return offlinefile.playbackpath



    ##
    # Calculate the number of accounts defined in settings
    #   parameters: the account type (usually plugin name)
    ##
    def numberOfAccounts(self,accountType):

        return 9




    ##
    # Delete an account, enroll an account or refresh the current listings
    #   parameters: mode
    ##
    def accountActions(self, addon, mode, instanceName, numberOfAccounts):

        if mode == 'dummy':
            xbmc.executebuiltin("XBMC.Container.Refresh")

        # delete the configuration for the specified account
        elif mode == 'delete':

            #*** old - needs to be re-written
            if instanceName != '':

                try:
                    # gdrive specific ***
                    addon.setSetting(instanceName + '_username', '')
                    addon.setSetting(instanceName + '_code', '')
                    addon.setSetting(instanceName + '_client_id', '')
                    addon.setSetting(instanceName + '_client_secret', '')
                    addon.setSetting(instanceName + '_url', '')
                    addon.setSetting(instanceName + '_password', '')
                    addon.setSetting(instanceName + '_passcode', '')
                    addon.setSetting(instanceName + '_auth_access_token', '')
                    addon.setSetting(instanceName + '_auth_refresh_token', '')
                    addon.setSetting(instanceName + '_spreadsheetname', '')
                    addon.setSetting(instanceName + '_spreadsheetname', '')
                    addon.setSetting(instanceName + '_spreadsheet', '')
                    # ***
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30158))
                except:
                    #error: instance doesn't exist
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30158))
            xbmc.executebuiltin("XBMC.Container.Refresh")


        # enroll a new account
        elif mode == 'enroll':


            if KODI:
                from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
                from resources.lib import enroll_proxy

                import threading

                server = enroll_proxy.MyHTTPServer(('',  9999), enroll_proxy.enrollBrowser)
                server.handle_request()
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30210), '')

                while server.ready:
                    server.handle_request()
                server.socket.close()



    ##
    # Delete an account, enroll an account or refresh the current listings
    #   parameters: addon, plugin name, mode, instance name, user provided username, number of accounts, current context
    #   returns: selected instance name
    ##
    def getInstanceName(self,addon, mode, instanceName, invokedUsername, numberOfAccounts, contextType):

        # show list of services
        if mode == 'delete' or mode == 'dummy':
                    count = 1

        elif numberOfAccounts > 1 and instanceName == '' and invokedUsername == '' and mode == 'main':

                if KODI:
                    self.addMenu(self.PLUGIN_URL+'?mode=enroll&content_type='+str(contextType),'['+str(addon.getLocalizedString(30207))+']')
                else:
                    self.addMenu(self.PLUGIN_URL+'?mode=enroll&content_type='+str(contextType),'['+str(addon.getLocalizedString(30207))+']')
#                    self.addMenu(self.PLUGIN_URL+'?mode=enroll','['+str(addon.getLocalizedString(30207))+']')

                if contextType != 'image':
                    path = settings.getSetting('cache_folder')
                    if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                        self.addMenu(self.PLUGIN_URL+'?mode=offline&content_type='+str(contextType),'<'+str(addon.getLocalizedString(30208))+'>')

                if contextType == 'image':
                    path = settings.getSetting('photo_folder')
                    if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                        self.addMenu(path,'<offline photos>')

                path = settings.getSetting('encfs_target')
                if path != '' and  (xbmcvfs.exists(path) or os.path.exists(path)):
                    self.addMenu(path,'<offline encfs>')


                mode = ''
                count = 1
                while True:
                    instanceName = self.PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
                        if username != '':
                            self.addMenu(self.PLUGIN_URL+'?mode=main&content_type='+str(contextType)+'&instance='+str(instanceName),username, instanceName=instanceName)

                    except:
                        username = ''
                    if count == numberOfAccounts:
                        break
                    count = count + 1
                return None

        #        spreadshetModule = getSetting('library', False)
        #        libraryAccount = getSetting('library_account')

         #       if spreadshetModule:
         #           addMenu(PLUGIN_URL+'?mode=kiosk&content_type='+str(contextType)+'&instance='+PLUGIN_NAME+str(libraryAccount),'[kiosk mode]')

        elif instanceName == '' and invokedUsername == '' and numberOfAccounts == 1:

                count = 1
                options = []
                accounts = []

                for count in range (1, numberOfAccounts+1):
                    instanceName = self.PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
                        if username != '':
                            options.append(username)
                            accounts.append(instanceName)

                        if username != '':

                            return instanceName
                    except:
                        return instanceName

                #fallback on first defined account
                return accounts[0]

        # no accounts defined and url provided; assume public
        elif numberOfAccounts == 0 and mode=='streamurl':
            return None

        # offline mode
        elif mode=='offline':
            return None
            # no accounts defined
        elif numberOfAccounts == 0:

                #legacy account conversion
                try:
                    username = settings.getSetting('username')

                    if username != '':
                        addon.setSetting(self.PLUGIN_NAME+'1_username', username)
                        addon.setSetting(self.PLUGIN_NAME+'1_password', settings,getSetting('password'))
                        addon.setSetting(self.PLUGIN_NAME+'1_auth_writely', settings.getSetting('auth_writely'))
                        addon.setSetting(self.PLUGIN_NAME+'1_auth_wise', settings.getSetting('auth_wise'))
                        addon.setSetting('username', '')
                        addon.setSetting('password', '')
                        addon.setSetting('auth_writely', '')
                        addon.setSetting('auth_wise', '')
                    else:
                        xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                        xbmcplugin.endOfDirectory(self.plugin_handle)
                except :
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                    xbmcplugin.endOfDirectory(self.plugin_handle)

                return instanceName

        # show entries of a single account (such as folder)
        elif instanceName != '':

            return instanceName



        elif invokedUsername != '':

                options = []
                accounts = []
                for count in range (1, numberOfAccounts+1):
                    instanceName = self.PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username')
                        if username != '':
                            options.append(username)
                            accounts.append(instanceName)

                        if username == invokedUsername:
                            return instanceName

                    except:
                        return instanceName


                #fallback on first defined account
                return accounts[0]

        #prompt before playback
        else:

                options = []
                accounts = []

                # url provided; provide public option
                if mode=='streamurl':
                    options.append('*public')
                    accounts.append('public')

                for count in range (1, numberOfAccounts+1):
                    instanceName = self.PLUGIN_NAME+str(count)
                    try:
                        username = settings.getSetting(instanceName+'_username',10)
                        if username != '':
                            options.append(username)
                            accounts.append(instanceName)
                    except:
                        break

                # url provided; provide public option
                if mode=='streamurl':
                    options.append('public')
                    accounts.append('public')

                ret = xbmcgui.Dialog().select(addon.getLocalizedString(30120), options)

                if KODI:
                    #fallback on first defined account
                    if accounts[ret] == 'public':
                        return None
                    else:
                        return accounts[ret]
                else:
                    return None



    def run(self,writer=None, query=None,DBM=None, addon=None):
        #return
#class run():
        # cloudservice - required python modules

        KODI = True
        if re.search(re.compile('.py', re.IGNORECASE), sys.argv[0]) is not None:
            KODI = False

        if KODI:
            # cloudservice - standard XBMC modules
#            import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
            # global variables
            import constants
            addon = constants.addon
            self.addon = addon
            self.PLUGIN_URL = constants.PLUGIN_NAME

        else:
 #           from resources.libgui import xbmcaddon
 #           from resources.libgui import xbmcgui
 #           from resources.libgui import xbmcplugin
 #           from resources.libgui import xbmc
            # global variables
            import constants
            #addon = constants.addon
            self.addon = addon
            self.PLUGIN_URL = 'default.py'
        self.PLUGIN_NAME = constants.PLUGIN_NAME


        cloudservice2 = constants.cloudservice2


        #*** testing - gdrive
        #if constants.CONST.tvwindow:
        #    from resources.lib import tvWindow
        from resources.lib import gSpreadsheets
        #from resources.lib import gSheets_api4

        ##**

        # cloudservice - standard modules
        from resources.lib import folder
        #from resources.lib import teamdrive
        from resources.lib import file
        from resources.lib import package
        from resources.lib import mediaurl
        from resources.lib import gPlayer
        from resources.lib import settings

        from resources.lib import cache
#        if constants.CONST.tmdb:
#            from resources.lib import TMDB



        if KODI:
            #global variables
            self.PLUGIN_URL = sys.argv[0]
            self.plugin_handle = int(sys.argv[1])
            plugin_queries = settings.parse_query(sys.argv[2][1:])

        else:
            self.PLUGIN_URL = 'default.py'
            self.plugin_handle = writer
            plugin_queries = ''

            plugin_queries = settings.parse_query(query)
            settings.plugin_queries = plugin_queries


        self.debugger()


        # cloudservice - create settings module
        settings = settings.settings(addon)

        # retrieve settings
        user_agent = settings.getSetting('user_agent')
        #obsolete, replace, revents audio from streaming
        #if user_agent == 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)':
        #    addon.setSetting('user_agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0')



        mode = settings.getParameter('mode','main')

        # make mode case-insensitive
        mode = mode.lower()


        instanceName = ''
        try:
            instanceName = (plugin_queries['instance']).lower()
        except:
            instanceName = ''
        # cloudservice - content type
        contextType = settings.getParameter('content_type')

        #support encfs?
        encfs = settings.getParameter('encfs', False)

        contentType = self.getContentType(contextType,encfs)


        if KODI:
            xbmcplugin.addSortMethod(self.plugin_handle, xbmcplugin.SORT_METHOD_LABEL)
            #    xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_TRACKNUM)
            xbmcplugin.addSortMethod(self.plugin_handle, xbmcplugin.SORT_METHOD_SIZE)

        numberOfAccounts = self.numberOfAccounts(constants.PLUGIN_NAME)
        invokedUsername = settings.getParameter('username')


        # cloudservice - utilities
        ###

        if mode == 'dummy' or mode == 'delete' or mode == 'enroll':

            self.accountActions(addon, mode, instanceName, numberOfAccounts)
            mode = 'main'
            instanceName = ''
        #create strm files
        elif mode == 'buildstrm':

            silent = settings.getParameter('silent', settings.getSetting('strm_silent',0))
            if silent == '':
                silent = 0

            try:
                path = settings.getSetting('strm_path')
            except:
                path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
                addon.setSetting('strm_path', path)

            if path == '':
                path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
                addon.setSetting('strm_path', path)

            if path != '':
                returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30027) + '\n'+path +  '?')


            if path != '' and returnPrompt:

                if silent != 2:
                    try:
                        pDialog = xbmcgui.DialogProgressBG()
                        pDialog.create(addon.getLocalizedString(30000), 'Building STRMs...')
                    except:
                        pDialog = None

                url = settings.getParameter('streamurl')
                url = re.sub('---', '&', url)
                title = settings.getParameter('title')
                type = int(settings.getParameterInt('type', 0))

                if url != '':

                        filename = path + '/' + title+'.strm'
                        strmFile = xbmcvfs.File(filename, "w")

                        strmFile.write(url+'\n')
                        strmFile.close()
                else:

                    folderID = settings.getParameter('folder')
                    filename = settings.getParameter('filename')
                    title = settings.getParameter('title')
                    invokedUsername = settings.getParameter('username')
                    encfs = settings.getParameter('encfs', False)

                    encryptedPath = settings.getParameter('epath', '')
                    dencryptedPath = settings.getParameter('dpath', '')

                    if folderID != '':

                        count = 1
                        loop = True
                        while loop:
                            instanceName = constants.PLUGIN_NAME+str(count)
                            try:
                                username = settings.getSetting(instanceName+'_username')
                                if username == invokedUsername:

                                    #let's log in
                                    #if ( settings.getSettingInt(instanceName+'_type',0)==0):
                                        #service = cloudservice1(PLUGIN_URL,addon,instanceName, user_agent, settings, DBM=DBM)
                                    #else:
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,instanceName, user_agent, settings,DBM=DBM)

                                    loop = False
                            except:
                                #service = cloudservice1(self.PLUGIN_URL,addon,instanceName, user_agent)
                                break

                            if count == numberOfAccounts:
                                try:
                                    service
                                except NameError:
                                    #fallback on first defined account
                                    #if ( settings.getSettingInt(instanceName+'_type',0)==0):
                                    #    service = cloudservice1(self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings,DBM=DBM)
                                    #else:
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings,DBM=DBM)
                                break
                            count = count + 1

                        # encfs -- extract filename
                        if encfs:
                            extrapulatedFolderName = re.compile('([^/]+)/$')

                            titleDecrypted = extrapulatedFolderName.match(dencryptedPath)

                            if titleDecrypted is not None:
                                title = titleDecrypted.group(1)


                        if constants.CONST.spreadsheet and service.cloudResume == '2':
                            spreadsheetFile = xbmcvfs.File(path + '/spreadsheet.tab', "w")
                            service.buildSTRM(path + '/'+title,folderID, contentType=contentType, pDialog=pDialog, epath=encryptedPath, dpath=dencryptedPath, encfs=encfs, spreadsheetFile=spreadsheetFile)
                            spreadsheetFile.close()
                        else:
                            service.buildSTRM(path + '/'+title,folderID, contentType=contentType, pDialog=pDialog, epath=encryptedPath, dpath=dencryptedPath, encfs=encfs)

                    elif filename != '':
                                    if encfs:
                                        values = {'title': title, 'encfs': 'True', 'epath': encryptedPath, 'dpath': dencryptedPath, 'filename': filename, 'username': invokedUsername}
                                        # encfs -- extract filename
                                        extrapulatedFileName = re.compile('.*?/([^/]+)$')

                                        titleDecrypted = extrapulatedFileName.match(dencryptedPath)

                                        if titleDecrypted is not None:
                                            title = titleDecrypted.group(1)

                                    else:
                                        values = {'title': title, 'filename': filename, 'username': invokedUsername}
                                    if type == 1:
                                        url = self.PLUGIN_URL+'?mode=audio&'+urllib.urlencode(values)
                                    else:
                                        url = self.PLUGIN_URL+'?mode=video&'+urllib.urlencode(values)

                                    filename = path + '/' + title+'.strm'
                                    strmFile = xbmcvfs.File(filename, "w")
                                    strmFile.write(url+'\n')
                                    strmFile.close()

                    else:

                        count = 1
                        while True:
                            instanceName = constants.PLUGIN_NAME+str(count)
                            username = settings.getSetting(instanceName+'_username')

                            if username != '' and username == invokedUsername:
                                #if ( settings.getSettingInt(instanceName+'_type',0)==0):
                                #        service = cloudservice1(self.PLUGIN_URL,addon,instanceName, user_agent, settings)
                                #else:
                                service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,instanceName, user_agent, settings,DBM=DBM)

                                service.buildSTRM(path + '/'+username, contentType=contentType, pDialog=pDialog,  epath=encryptedPath, dpath=dencryptedPath, encfs=encfs)

                            if count == numberOfAccounts:
                                #fallback on first defined account
                                try:
                                    service
                                except NameError:
                                    #fallback on first defined account
                                    #if ( settings.getSettingInt(instanceName+'_type',0)==0):
                                    #        service = cloudservice1(self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings)
                                    #else:
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings,DBM=DBM)
                                break
                            count = count + 1

                if silent != 2:
                    try:
                        pDialog.update(100)
                        pDialog.close()
                    except:
                        pDialog = None
                if silent == 0:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30028))
            xbmcplugin.endOfDirectory(self.plugin_handle)
            return
        #create strm files
        elif mode == 'buildstrm2':

            silent = settings.getParameter('silent', settings.getSetting('strm_silent',0))
            if silent == '':
                silent = 0

            try:
                path = settings.getSetting('strm_path')
            except:
                path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
                addon.setSetting('strm_path', path)

            if path == '':
                path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30026), 'files','',False,False,'')
                addon.setSetting('strm_path', path)

            if path != '':
                returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30027) + '\n'+path +  '?')


            if path != '' and returnPrompt:

                if silent != 2:
                    try:
                        pDialog = xbmcgui.DialogProgressBG()
                        pDialog.create(addon.getLocalizedString(30000), 'Building STRMs...')
                    except:
                        pDialog = None

                url = settings.getParameter('streamurl')
                url = re.sub('---', '&', url)
                title = settings.getParameter('title')
                type = int(settings.getParameterInt('type', 0))

                if url != '':

                        filename = path + '/' + title+'.strm'
                        strmFile = xbmcvfs.File(filename, "w")

                        strmFile.write(url+'\n')
                        strmFile.close()
                else:

                    folderID = settings.getParameter('folder')
                    filename = settings.getParameter('filename')
                    title = settings.getParameter('title')
                    invokedUsername = settings.getParameter('username')
                    encfs = settings.getParameter('encfs', False)

                    encryptedPath = settings.getParameter('epath', '')
                    dencryptedPath = settings.getParameter('dpath', '')

                    if folderID != '':

                        count = 1
                        loop = True
                        while loop:
                            instanceName = constants.PLUGIN_NAME+str(count)
                            try:
                                username = settings.getSetting(instanceName+'_username')
                                if username == invokedUsername:

                                    #let's log in
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,instanceName, user_agent, settings,DBM=DBM)

                                    loop = False
                            except:

                                break

                            if count == numberOfAccounts:
                                try:
                                    service
                                except NameError:
                                    #fallback on first defined account
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings,DBM=DBM)
                                break
                            count = count + 1

                        # encfs -- extract filename
                        if encfs:
                            extrapulatedFolderName = re.compile('([^/]+)/$')

                            titleDecrypted = extrapulatedFolderName.match(dencryptedPath)

                            if titleDecrypted is not None:
                                title = titleDecrypted.group(1)


                        if constants.CONST.spreadsheet and service.cloudResume == '2':
                            spreadsheetFile = xbmcvfs.File(path + '/spreadsheet.tab', "w")
                            service.buildSTRM(path,folderID, contentType=contentType, pDialog=pDialog, epath=encryptedPath, dpath=dencryptedPath, encfs=encfs, spreadsheetFile=spreadsheetFile, catalog=True)
                            spreadsheetFile.close()
                        else:
                            service.buildSTRM(path,folderID, contentType=contentType, pDialog=pDialog, epath=encryptedPath, dpath=dencryptedPath, encfs=encfs, catalog=True)

                    elif filename != '':
                                    if encfs:
                                        values = {'title': title, 'encfs': 'True', 'epath': encryptedPath, 'dpath': dencryptedPath, 'filename': filename, 'username': invokedUsername}
                                        # encfs -- extract filename
                                        extrapulatedFileName = re.compile('.*?/([^/]+)$')

                                        titleDecrypted = extrapulatedFileName.match(dencryptedPath)

                                        if titleDecrypted is not None:
                                            title = titleDecrypted.group(1)

                                    else:
                                        values = {'title': title, 'filename': filename, 'username': invokedUsername}
                                    if type == 1:
                                        url = self.PLUGIN_URL+'?mode=audio&'+urllib.urlencode(values)
                                    else:
                                        url = self.PLUGIN_URL+'?mode=video&'+urllib.urlencode(values)

                                    filename = path + '/' + title+'.strm'
                                    strmFile = xbmcvfs.File(filename, "w")
                                    strmFile.write(url+'\n')
                                    strmFile.close()

                    else:

                        count = 1
                        while True:
                            instanceName = constants.PLUGIN_NAME+str(count)
                            username = settings.getSetting(instanceName+'_username')

                            if username != '' and username == invokedUsername:
                                service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,instanceName, user_agent, settings,DBM=DBM)

                                service.buildSTRM(path + '/'+username, contentType=contentType, pDialog=pDialog,  epath=encryptedPath, dpath=dencryptedPath, encfs=encfs, catalog=True)

                            if count == numberOfAccounts:
                                #fallback on first defined account
                                try:
                                    service
                                except NameError:
                                    #fallback on first defined account
                                    service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,constants.PLUGIN_NAME+'1', user_agent, settings,DBM=DBM)
                                break
                            count = count + 1

                if silent != 2:
                    try:
                        pDialog.update(100)
                        pDialog.close()
                    except:
                        pDialog = None
                if silent == 0:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30028))
            xbmcplugin.endOfDirectory(self.plugin_handle)
            return

        ###



        ###



        #STRM playback without instance name; use default
        if invokedUsername == '' and instanceName == '' and (mode == 'video' or mode == 'audio'):
            instanceName = constants.PLUGIN_NAME + str(settings.getSetting('account_default', 1))


        instanceName = self.getInstanceName(addon, mode, instanceName, invokedUsername, numberOfAccounts, contextType)

        service = None
        if instanceName is None and (mode == 'index' or mode == 'main' or mode == 'offline'):
            service = None
        elif instanceName is None:
            service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,'', user_agent, settings, authenticate=False,DBM=DBM)
        else:
            service = cloudservice2(self.plugin_handle,self.PLUGIN_URL,addon,instanceName, user_agent, settings,DBM=DBM)



                #create strm files
        if mode == 'buildf2':


            import time
            currentDate = time.strftime("%Y%m%d")


            try:
                path = settings.getSetting('strm_path')
            except:
                path = ''


            if path != '':

                try:
                    pDialog = xbmcgui.DialogProgressBG()
                    pDialog.create(addon.getLocalizedString(30000), 'Building STRMs...')
                except:
                    pDialog = None


                #service = gdrive_api2.gdrive(self.PLUGIN_URL,addon,instanceName, user_agent, settings)

        #        try:
                addon.setSetting(instanceName + '_changedate', currentDate)
                service.buildSTRM2(path, contentType=contentType, pDialog=pDialog)
        #        except:
        #            pass

                try:
                    pDialog.update(100)
                    pDialog.close()
                except:
                    pDialog = None

            xbmcplugin.endOfDirectory(self.plugin_handle)
            return



        # options menu
        #if mode == 'main':
        #    addMenu(self.PLUGIN_URL+'?mode=options','<< '+addon.getLocalizedString(30043)+' >>')

        if mode == 'offline':

            title = settings.getParameter('title')
            folderID = settings.getParameter('folder')
            folderName = settings.getParameter('foldername')


            mediaItems = self.getOfflineFileList(settings.getSetting('cache_folder'))


            if mediaItems:
                for offlinefile in mediaItems:

                    self.addOfflineMediaFile(offlinefile)



        elif service is None:

            xbmcplugin.endOfDirectory(self.plugin_handle)
            return


        #cloud_db actions
        elif mode == 'cloud_db':

            title = settings.getParameter('title')
            folderID = settings.getParameter('folder')
            folderName = settings.getParameter('foldername')
            filename = settings.getParameter('filename')

            action = settings.getParameter('action')

            mediaFile = file.file(filename, title, '', 0, '','')
            mediaFolder = folder.folder(folderID,folderName)
            package=package.package(mediaFile,mediaFolder)

                # TESTING
            if constants.CONST.spreadsheet and service.cloudResume == '2':
                if service.worksheetID == '':

                    try:
                        service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                        spreadsheets = service.gSpreadsheet.getSpreadsheetList()
                    except:
                        service.gSpreadsheet = None
                        spreadsheets = None

                    for title in spreadsheets.iterkeys():
                        if title == 'CLOUD_DB':
                            worksheets = service.gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                            for worksheet in worksheets.iterkeys():
                                if worksheet == 'db':
                                    service.worksheetID = worksheets[worksheet]
                                    addon.setSetting(instanceName + '_spreadsheet', service.worksheetID)
                                break
                        break

                # TESTING
            if constants.CONST.spreadsheet and service.cloudResume == '2':

                if service.gSpreadsheet is None:
                    service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
                if action == 'watch':
                    service.gSpreadsheet.setMediaStatus(service.worksheetID,package, watched=1)
                    xbmc.executebuiltin("XBMC.Container.Refresh")
                elif action == 'queue':
                    package.folder.id = 'QUEUED'
                    service.gSpreadsheet.setMediaStatus(service.worksheetID,package)
                elif action == 'recentwatched' or action == 'recentstarted' or action == 'library' or action == 'queued':

                    if constants.CONST.spreadsheet:
                        mediaItems = service.gSpreadsheet.updateMediaPackage(service.worksheetID, criteria=action)

                    #ensure that folder view playback
                    if contextType == '':
                        contextType = 'video'

                    if mediaItems:
                        for item in mediaItems:

                                if item.file is None:
                                    service.addDirectory(item.folder, contextType=contextType)
                                else:
                                    service.addMediaFile(item, contextType=contextType)

            service.updateAuthorization(addon)

        #cloud_db actions
        elif mode == 'cloud_dbtest':

            title = settings.getParameter('title')
            folderID = settings.getParameter('folder')
            folderName = settings.getParameter('foldername')
            filename = settings.getParameter('filename')

            action = settings.getParameter('action')


        #    s = gSheets_api4.gSheets_api4(service,addon, user_agent)
        #    s.createSpreadsheet()
        #    s.addRows()
            if action == 'library_menu':

                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_genre&content_type='+str(contextType),'Genre')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_year&content_type='+str(contextType),'Year')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_title&content_type='+str(contextType),'Title')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_country&content_type='+str(contextType),'Countries')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_director&content_type='+str(contextType),'Directors')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_studio&content_type='+str(contextType),'Studio')
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_resolution&content_type='+str(contextType),'Quality (Resolution)')

            else:

                mediaFile = file.file(filename, title, '', 0, '','')
                mediaFolder = folder.folder(folderID,folderName)
                package=package.package(mediaFile,mediaFolder)

                spreadsheet = None
                    # TESTING
                if constants.CONST.spreadsheet:

                        try:
                            service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                            spreadsheets = service.gSpreadsheet.getSpreadsheetList()
                        except:
                            service.gSpreadsheet = None
                            spreadsheets = None

                        for t in spreadsheets.iterkeys():
                            if t == 'Movie2':
                                worksheets = service.gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[t])

                                for worksheet in worksheets.iterkeys():
                                    if worksheet == 'db':
                                        spreadsheet = worksheets[worksheet]
                                        break
                                break

                    # TESTING
                if constants.CONST.spreadsheet:

                    if service.gSpreadsheet is None:
                        service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
                    if action == 'watch':
                        service.gSpreadsheet.setMediaStatus(service.worksheetID,package, watched=1)
                        xbmc.executebuiltin("XBMC.Container.Refresh")
                    elif action == 'queue':
                        package.folder.id = 'QUEUED'
                        service.gSpreadsheet.setMediaStatus(service.worksheetID,package)
                    elif action == 'genre' or action == 'year' or action == 'title' or action == 'country' or action == 'director' or action == 'studio' or action == 'recentstarted' or  'library' in action or action == 'queued':

                        if action == 'genre':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, genre=title)
                        elif action == 'year':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, year=title)
                        elif action == 'title':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, title=title)
                        elif action == 'resolution':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, resolution=title)
                        elif action == 'country':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, country=title)
                        elif action == 'director':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, director=title)
                        elif action == 'studio':
                            mediaItems = service.gSpreadsheet.getMovies(spreadsheet, studio=title)
                        elif action == 'library_title':
                            mediaItems = service.gSpreadsheet.getTitle(spreadsheet)
                        elif action == 'library_genre':
                            mediaItems = service.gSpreadsheet.getGenre(spreadsheet)
                        elif action == 'library_year':
                            mediaItems = service.gSpreadsheet.getYear(spreadsheet)
                        elif action == 'library_country':
                            mediaItems = service.gSpreadsheet.getCountries(spreadsheet)
                        elif action == 'library_director':
                            mediaItems = service.gSpreadsheet.getDirector(spreadsheet)
                        elif action == 'library_studio':
                            mediaItems = service.gSpreadsheet.getStudio(spreadsheet)
                        elif action == 'library_resolution':
                            mediaItems = service.gSpreadsheet.getResolution(spreadsheet)

                        #ensure that folder view playback
                        if contextType == '':
                            contextType = 'video'

                        #if constants.CONST.tmdb:
                        #    tmdb= TMDB.TMDB(service,addon, user_agent)

                        if mediaItems:
                            for item in mediaItems:

                                    if item.file is None:
                                        service.addDirectory(item.folder, contextType=contextType)
                                    else:
                                       # movieID = tmdb.movieSearch(item.file.title,item.file.year)
                                       # tmdb.movieDetails(movieID)
                                        service.addMediaFile(item, contextType=contextType)

                service.updateAuthorization(addon)

        #dump a list of videos available to play
        elif mode == 'main' or mode == 'index':

            folderID = settings.getParameter('folder', False)
            folderName = settings.getParameter('foldername', False)

            #ensure that folder view playback
            if contextType == '':
                contextType = 'video'

            # display option for all Videos/Music/Photos, across gdrive
            #** gdrive specific
            if mode == 'main':

                #self.addMenu(self.PLUGIN_URL+'?mode=index&instance='+str(service.instanceName)+'&content_type=image','[switch to photo view]')

                if ('gdrive' in constants.PLUGIN_NAME):

                    if contentType in (2,4,7):
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=ALL&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30030)+']')
                    elif contentType == 1:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=VIDEOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30031)+']')
                    elif contentType == 0:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=VIDEO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30025)+']')
                    elif contentType == 3:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=MUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30094)+']')
                    elif contentType == 5:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=PHOTO&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30034)+']')
                    elif contentType == 6:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder=PHOTOMUSIC&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+' '+addon.getLocalizedString(30032)+']')
                folderID = 'root'

                if ('gdrive' in constants.PLUGIN_NAME):

        #        if (service.protocol != 2):
        #            self.addMenu(self.PLUGIN_URL+'?mode=index&folder=STARRED-FILES&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+ ' '+addon.getLocalizedString(30095)+']')
        #            self.addMenu(self.PLUGIN_URL+'?mode=index&folder=STARRED-FOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30096)+']')
                    self.addMenu(self.PLUGIN_URL+'?mode=index&folder=SHARED&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30098)+']')
                    self.addMenu(self.PLUGIN_URL+'?mode=index&folder=STARRED-FILESFOLDERS&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30018)+  ' '+addon.getLocalizedString(30097)+']')

                    teamdrives = service.getTeamDrives();
                    for drive in teamdrives:
                        self.addMenu(self.PLUGIN_URL+'?mode=index&folder='+str(drive.id)+'&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30200) + ' - ' + str(drive.title)+']')



                self.addMenu(self.PLUGIN_URL+'?mode=search&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30111)+']')
                self.addMenu(self.PLUGIN_URL+'?mode=buildstrm2&instance='+str(service.instanceName)+'&content_type='+str(contextType),'<'+addon.getLocalizedString(30211)+'>')
                if constants.CONST.testing_features:
                    self.addMenu(self.PLUGIN_URL+'?mode=cloud_dbtest&instance='+str(service.instanceName)+'&action=library_menu&content_type='+str(contextType),'['+addon.getLocalizedString(30212)+']')


                #CLOUD_DB
                if 'gdrive' in constants.PLUGIN_NAME and service.gSpreadsheet is not None:
                        self.addMenu(self.PLUGIN_URL+'?mode=cloud_db&action=recentstarted&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30177)+' '+addon.getLocalizedString(30213)+']')
                        self.addMenu(self.PLUGIN_URL+'?mode=cloud_db&action=recentwatched&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30177)+' '+addon.getLocalizedString(30214)+']')
                        self.addMenu(self.PLUGIN_URL+'?mode=cloud_db&action=library&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30177)+' '+addon.getLocalizedString(30215)+']')
                        self.addMenu(self.PLUGIN_URL+'?mode=cloud_db&action=queued&instance='+str(service.instanceName)+'&content_type='+contextType,'['+addon.getLocalizedString(30177)+' '+addon.getLocalizedString(30216)+']')
            ##**



            # cloudservice - validate service
            try:
                service
            except NameError:
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
                xbmc.log(addon.getLocalizedString(30050)+ constants.PLUGIN_NAME+'-login', xbmc.LOGERROR)
                xbmcplugin.endOfDirectory(self.plugin_handle)
                return

            #if encrypted, get everything(as encrypted files will be of type application/ostream)
            if encfs:

                #temporarly force crypto with encfs
                settings.setCryptoParameters()
                if settings.cryptoPassword != "":

                    mediaItems = service.getMediaList(folderID,contentType=8)


                    if mediaItems:

                        from resources.lib import  encryption
                        encrypt = encryption.encryption(settings.cryptoSalt,settings.cryptoPassword)

                        if contentType == 9:
                            mediaList = ['.mp4', '.flv', '.mov', '.webm', '.avi', '.ogg', '.mkv']
                        elif contentType == 10:
                            mediaList = ['.mp3', '.flac']
                        else:# contentType == 11:
                            mediaList = ['.jpg', '.png']
                        media_re = re.compile("|".join(mediaList), re.I)

                        #sort encrypted items by title:
                        sortedMediaItems = {}
                        for item in mediaItems:
                            if item.file is None:
                                try:
                                    item.folder.displaytitle =  encrypt.decryptString(str(item.folder.title))
                                    sortedMediaItems[str(item.folder.displaytitle) + '_' + str(item.folder.title)] = item
                                except:
                                    item.folder.displaytitle = item.folder.title

                            else:
                                try:
                                    item.file.displaytitle = encrypt.decryptString(str(item.file.title))
                                    sortedMediaItems[str(item.file.displaytitle) + '_' + str(item.file.title)] = item
                                except:
                                    item.file.displaytitle = item.file.title

                        #create the files and folders for decrypting file/folder names
                        for item in sorted (sortedMediaItems):
                            item = sortedMediaItems[item]

                            if item.file is None:
                                try:
                                    item.folder.displaytitle =  encrypt.decryptString(str(item.folder.title))
                                    service.addDirectory(item.folder, contextType=contextType, encfs=True )
                                except:
                                    item.folder.displaytitle = str(item.folder.title)
                            else:
                                try:
                                    item.file.displaytitle = encrypt.decryptString(str(item.file.title))
                                    item.file.title =  item.file.displaytitle
                                    if contentType < 9 or media_re.search(str(item.file.title)):
                                        service.addMediaFile(item, contextType=contextType,  encfs=True)
                                except:
                                    item.file.displaytitle = str(item.file.title)

                else:


                    settings.setEncfsParameters()

                    encryptedPath = settings.getParameter('epath', '')
                    dencryptedPath = settings.getParameter('dpath', '')

                    encfs_source = settings.encfsSource
                    encfs_target = settings.encfsTarget
                    encfs_inode = settings.encfsInode

                    mediaItems = service.getMediaList(folderID,contentType=8)

                    if mediaItems:
                        dirListINodes = {}
                        fileListINodes = {}

                        #create the files and folders for decrypting file/folder names
                        for item in mediaItems:

                                if item.file is None:
                                    xbmcvfs.mkdir(encfs_source + str(encryptedPath))
                                    xbmcvfs.mkdir(encfs_source + str(encryptedPath) + str(item.folder.title) + '/' )

                                    if encfs_inode == 0:
                                        dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(item.folder.title)).st_ino()))] = item.folder
                                    else:
                                        dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(item.folder.title)).st_ctime()))] = item.folder
                                    #service.addDirectory(item.folder, contextType=contextType,  encfs=True)
                                else:
                                    xbmcvfs.mkdir(encfs_source +  str(encryptedPath))
                                    xbmcvfs.mkdir(encfs_source +  str(encryptedPath) + str(item.file.title))
                                    if encfs_inode == 0:
                                        fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath)+ str(item.file.title)).st_ino()))] = item
                                    else:
                                        fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath) + str(item.file.title)).st_ctime()))] = item
                                    #service.addMediaFile(item, contextType=contextType)
                                if KODI and encfs_inode > 0:
                                        xbmc.sleep(1000)


                        if contentType == 9:
                            mediaList = ['.mp4', '.flv', '.mov', '.webm', '.avi', '.ogg', '.mkv']
                        elif contentType == 10:
                            mediaList = ['.mp3', '.flac']
                        else:# contentType == 11:
                            mediaList = ['.jpg', '.png']
                        media_re = re.compile("|".join(mediaList), re.I)


                        #examine the decrypted file/folder names for files for playback and dirs for navigation
                        dirs, files = xbmcvfs.listdir(encfs_target + str(dencryptedPath) )
                        for dir in dirs:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + dir).st_ctime())

                            #we found a directory
                            if index in dirListINodes.keys():
                                xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
            #                    dirTitle = dir + ' [' +dirListINodes[index].title+ ']'
                                encryptedDir = dirListINodes[index].title
                                dirListINodes[index].displaytitle = dir + ' [' +dirListINodes[index].title+ ']'
                                service.addDirectory(dirListINodes[index], contextType=contextType,  encfs=True, dpath=str(dencryptedPath) + str(dir) + '/', epath=str(encryptedPath) + str(encryptedDir) + '/' )
                            #we found a file
                            elif index in fileListINodes.keys():
                                xbmcvfs.rmdir(encfs_target + str(dencryptedPath) + dir)
                                fileListINodes[index].file.decryptedTitle = dir
                                if contentType < 9 or media_re.search(str(dir)):
                                    service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(dir), epath=str(encryptedPath) )


                        # file is already downloaded
                        for file in files:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + file).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPath) + file).st_ctime())
                            if index in fileListINodes.keys():
                                fileListINodes[index].file.decryptedTitle = file
                                if contentType < 9 or media_re.search(str(file)):
                                    service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(file), epath=str(encryptedPath) )

                    #xbmc.executebuiltin("XBMC.Container.Refresh")


            else:
                path = settings.getParameter('epath', '')

                # real folder
                if folderID != '':
                    mediaItems = service.getMediaList(folderID,contentType=contentType)
                    if constants.CONST.spreadsheet and service.cloudResume == '2':

                        if service.gSpreadsheet is None:
                            service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                        if service.worksheetID != '':
                            service.gSpreadsheet.updateMediaPackageList(service.worksheetID, folderID, mediaItems)

                    if mediaItems:
                        for item in sorted(mediaItems):

                                if item.file is None:
                                    service.addDirectory(item.folder, contextType=contextType, epath=str(path)+ '/' + str(item.folder.title) + '/')
                                else:
                                    service.addMediaFile(item, contextType=contextType)

                # virtual folder; exists in spreadsheet only
                # not in use
                #elif folderName != '':


            service.updateAuthorization(addon)

        # NOT IN USE
        #** testing - gdrive
        elif mode == 'kiosk':

            spreadshetModule = settings.getSetting('library', False)


            if spreadshetModule:
                    gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
                    service.gSpreadsheet = gSpreadsheet
                    spreadsheets = service.getSpreadsheetList()


                    #channels = []
                    #for title in spreadsheets.iterkeys():
                    #    if title == 'TVShows':
                    #      worksheets = gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                          #if 0:
                          #  import time
                          #  hour = time.strftime("%H")
                          #  minute = time.strftime("%M")
                          #  weekDay = time.strftime("%w")
                          #  month = time.strftime("%m")
                          #  day = time.strftime("%d")


                          #  for worksheet in worksheets.iterkeys():
                          #       if worksheet == 'schedule':
                          #           channels = gSpreadsheet.getChannels(worksheets[worksheet])
                          #           ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), channels)
                          #           shows = gSpreadsheet.getShows(worksheets[worksheet] ,channels[ret])
                          #           showList = []
                          #           for show in shows:
                          #               showList.append(shows[show][6])
                          #           ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), showList)

                          #  for worksheet in worksheets.iterkeys():
                          #      if worksheet == 'data':
                          #          episodes = gSpreadsheet.getVideo(worksheets[worksheet] ,showList[ret])
                          #          #player = gPlayer.gPlayer()
                          #          #player.setService(service)
                          #          player.setContent(episodes)
                          #          player.setWorksheet(worksheets['data'])
                          #          player.next()
                          #          while KODI and not player.isExit:
                          #              xbmc.sleep(5000)
                          #else:
                          #  for worksheet in worksheets.iterkeys():
                          #      if worksheet == 'db':
                          #          episodes = gSpreadsheet.getMedia(worksheets[worksheet], service.getRootID())
                          #          #player = gPlayer.gPlayer()
                          #          #player.setService(service)
        #                 #           player.setContent(episodes)
                          #          player.setWorksheet(worksheets['db'])
                          #          player.PlayStream('plugin://plugin.video.'+constants.PLUGIN_NAME+'-testing/?mode=video&instance='+str(service.instanceName)+'&title='+episodes[0][3], None,episodes[0][7],episodes[0][2])
                          #          #player.next()
                          #          while KODI and not player.isExit:
                          #              player.saveTime()
                          #              xbmc.sleep(5000)

        ##** not in use
        elif mode == 'photo':

            title = settings.getParameter('title',0)
            title = re.sub('/', '_', title) #remap / from titles (google photos)

            docid = settings.getParameter('filename')
            folder = settings.getParameter('folder',0)

            encfs = settings.getParameter('encfs', False)

            if encfs:

                settings.setEncfsParameters()

                encryptedPath = settings.getParameter('epath', '')
                dencryptedPath = settings.getParameter('dpath', '')

                encfs_source = settings.encfsSource
                encfs_target = settings.encfsTarget
                encfs_inode = settings.encfsInode


                # don't redownload if present already
                if (not xbmcvfs.exists(str(encfs_source) + str(encryptedPath) +str(title))):
                    url = service.getDownloadURL(docid)
                    service.downloadGeneralFile(url, str(encfs_source) + str(encryptedPath) +str(title))

                xbmc.executebuiltin("XBMC.ShowPicture(\""+str(encfs_target) + str(dencryptedPath)+"\")")
                #item = xbmcgui.ListItem(path=str(encfs_target) + str(dencryptedPath))
                #xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)

            else:
                path = settings.getSetting('photo_folder')

                #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
                if not xbmcvfs.exists(path) and not os.path.exists(path):
                    path = ''

                while path == '':
                    path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
                    #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
                    if not xbmcvfs.exists(path) and not os.path.exists(path):
                        path = ''
                    else:
                        addon.setSetting('photo_folder', path)

                if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
                    xbmcvfs.mkdir(str(path) + '/'+str(folder))
                    #    try:
                    #        xbmcvfs.rmdir(str(path) + '/'+str(folder)+'/'+str(title))
                    #    except:
                    #        pass

                # don't redownload if present already
                if (not xbmcvfs.exists(str(path) + '/'+str(folder)+'/'+str(title))):
                    url = service.getDownloadURL(docid)
                    service.downloadPicture(url, str(path) + '/'+str(folder) + '/'+str(title))

                #xbmc.executebuiltin("XBMC.ShowPicture("+str(path) + '/'+str(folder) + '/'+str(title)+")")
                #item = xbmcgui.ListItem(path=str(path) + '/'+str(folder) + '/'+str(title))
                url = service.getDownloadURL(docid)
                item = xbmcgui.ListItem(path=url + '|' + service.getHeadersEncoded())
                xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)

        elif mode == 'downloadfolder':

            title = settings.getParameter('title')
            folderID = settings.getParameter('folder')
            folderName = settings.getParameter('foldername')
            encfs = settings.getParameter('encfs', False)

            try:
                service
            except NameError:
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
                xbmc.log(addon.getLocalizedString(30050)+ constants.PLUGIN_NAME + '-login',xbmc.LOGERROR)
                xbmcplugin.endOfDirectory(self.plugin_handle)
                return

            if encfs:

                settings.setEncfsParameters()

                encryptedPath = settings.getParameter('epath', '')
                dencryptedPath = settings.getParameter('dpath', '')

                encfs_source = settings.encfsSource
                encfs_target = settings.encfsTarget
                encfs_inode = settings.encfsInode
            else:
                path = settings.getParameter('epath', '/')

            if encfs:
                mediaItems = service.getMediaList(folderName=folderID, contentType=8)
                path = str(encfs_source) + str(encryptedPath)
            else:
                mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)
                path = str(settings.getSetting('photo_folder')) + str(path)

            if mediaItems:
                progress = xbmcgui.DialogProgressBG()
                progressBar = len(mediaItems)
                progress.create(addon.getLocalizedString(30092), '')
                count=0


                if not xbmcvfs.exists(path) and not os.path.exists(path):
                    xbmcvfs.mkdirs(path)

                for item in mediaItems:
                    count = count + 1
                    if item.file is not None:
                        progress.update((int)(float(count)/len(mediaItems)*100),addon.getLocalizedString(30092),  str(item.file.title))
                        service.downloadGeneralFile(item.getMediaURL(),str(path) + str(item.file.title) )
        #            elif item.folder is not None:
        #                # create path if doesn't exist
        #                if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
        #                    xbmcvfs.mkdir(str(path) + '/'+str(folder))
                progress.close()




        elif mode == 'slideshow':

            folder = settings.getParameter('folder',0)
            title = settings.getParameter('title',0)


            encfs = settings.getParameter('encfs', False)

            if encfs:

                settings.setEncfsParameters()

                encfs_source = settings.encfsSource
                encfs_target = settings.encfsTarget
                encfs_inode = settings.encfsInode

                if (not xbmcvfs.exists(str(encfs_target) + '/'+str(folder) + '/')):
                    xbmcvfs.mkdir(str(encfs_target) + '/'+str(folder))

                folderINode = ''
                if encfs_inode == 0:
                    folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ino())
                else:
                    folderINode = str(xbmcvfs.Stat(encfs_target + '/' + str(folder)).st_ctime())

                mediaItems = service.getMediaList(folderName=folder, contentType=8)

                if mediaItems:

                    dirs, filesx = xbmcvfs.listdir(encfs_source)
                    for dir in dirs:
                        index = ''
                        if encfs_inode == 0:
                            index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ino())
                        else:
                            index = str(xbmcvfs.Stat(encfs_source + '/' + dir).st_ctime())

                        if index == folderINode:

                            progress = xbmcgui.DialogProgressBG()
                            progress.create(addon.getLocalizedString(30035), 'Preparing list...')
                            count=0
                            for item in mediaItems:
                                if item.file is not None:
                                    count = count + 1;
                                    progress.update((int)(float(count)/len(mediaItems)*100),addon.getLocalizedString(30035), item.file.title)
                                    if (not xbmcvfs.exists(str(encfs_source) + '/'+str(dir)+'/'+str(item.file.title))):
                                        service.downloadGeneralFile(item.mediaurl.url,str(encfs_source) + '/'+str(dir)+ '/'+str(item.file.title))
                                        if KODI and encfs_inode > 0:
                                            xbmc.sleep(100)


                            progress.close()
                            xbmc.executebuiltin("XBMC.SlideShow(\""+str(encfs_target) + '/'+str(folder)+"/\")")

            elif 0:
                path = settings.getSetting('photo_folder')

                #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
                if not xbmcvfs.exists(path) and not os.path.exists(path):
                    path = ''


                while path == '':
                    path = xbmcgui.Dialog().browse(0,addon.getLocalizedString(30038), 'files','',False,False,'')
                    #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
                    if not xbmcvfs.exists(path) and not os.path.exists(path):
                        path = ''
                    else:
                        addon.setSetting('photo_folder', path)

                # create path if doesn't exist
                if (not xbmcvfs.exists(str(path) + '/'+str(folder) + '/')):
                    xbmcvfs.mkdir(str(path) + '/'+str(folder))

                mediaItems = service.getMediaList(folderName=folder, contentType=5)


                if mediaItems:
                    progress = xbmcgui.DialogProgressBG()
                    progress.create(addon.getLocalizedString(30035), 'Preparing list...')
                    count=0
                    for item in mediaItems:
                        if item.file is not None:
                            count = count + 1;
                            progress.update((int)(float(count)/len(mediaItems)*100),addon.getLocalizedString(30035), item.file.title)
                            service.downloadGeneralFile(item.mediaurl.url,str(path) + '/'+str(folder)+ '/'+item.file.title)
                            #xbmc.executebuiltin("XBMC.SlideShow("+str(path) + '/'+str(folder)+"/)")
                    progress.close()
                    xbmc.executebuiltin("XBMC.SlideShow(\""+str(path) + '/'+str(folder)+"/\")")

            #else:
             #   xbmc.executebuiltin("XBMC.SlideShow("+str(path) + '/'+str(folder)+"/)")


        ###
        # for video files
        # force stream - play a video given its url
        ###
        elif mode == 'streamurl':

            url = settings.getParameter('url',0)
            title = settings.getParameter('title')


            promptQuality = settings.getSetting('prompt_quality', True)

            mediaURLs = service.getPublicStream(url)
            options = []

            if mediaURLs:
                mediaURLs = sorted(mediaURLs)
                for mediaURL in mediaURLs:
                    options.append(mediaURL.qualityDesc)

                if promptQuality:
                    ret = xbmcgui.Dialog().select(addon.getLocalizedString(30033), options)
                else:
                    ret = 0

                playbackURL = mediaURLs[ret].url

                if (playbackURL == ''):
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
                    xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)
                else:
                    # if invoked in .strm or as a direct-video (don't prompt for quality)
                    item = xbmcgui.ListItem(path=playbackURL+ '|' + service.getHeadersEncoded())
                    item.setInfo( type="Video", infoLabels={ "Title": mediaURLs[ret].title , "Plot" : mediaURLs[ret].title } )
                    xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)


            else:
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30020),addon.getLocalizedString(30021))
                    xbmc.log(addon.getAddonInfo('name') + ': ' + addon.getLocalizedString(20021), xbmc.LOGERROR)



        ###
        # for video files - playback of video
        # force stream - play a video given its url
        ###
        #
        # legacy (depreicated) - memorycachevideo [given title]
        # legacy (depreicated) - play [given title]
        # legacy (depreicated) - playvideo [given title]
        # legacy (depreicated) - streamvideo [given title]
        elif mode == 'audio' or mode == 'video' or mode == 'search' or mode == 'play' or mode == 'memorycachevideo' or mode == 'playvideo' or mode == 'streamvideo':

            title = settings.getParameter('title') #file title
            filename = settings.getParameter('filename') #file ID
            folderID = settings.getParameter('folder') #folder ID


            spreadsheetSTRM = settings.getParameter('spreadsheet')
            sheetSTRM = settings.getParameter('sheet')

            year = settings.getParameter('year')

            if sheetSTRM != None and sheetSTRM != '':


                if service.gSpreadsheet is None:
                    service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                try:
                    service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                    spreadsheets = service.gSpreadsheet.getSpreadsheetList()
                except:
                    service.gSpreadsheet = None
                    spreadsheets = None

                spreadsheet = None
                for t in spreadsheets.iterkeys():
                    if t == 'Movies':
                        worksheets = service.gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[t])

                        for worksheet in worksheets.iterkeys():
                            if worksheet == 'db':
                                spreadsheet = worksheets[worksheet]
                                break
                        break

                if spreadsheet != None:
                    filename = service.gSpreadsheet.getSTRMplaybackMovie(spreadsheet, title, year)
                else:
                    filename = service.gSpreadsheet.getSTRMplaybackMovie('https://spreadsheets.google.com/feeds/list/'+spreadsheetSTRM+'/'+sheetSTRM+'/private/full', title, year)

            if folderID == 'False':
                    folderID = 'SEARCH'

            if mode != 'audio':
                settings.setVideoParameters()

            seek = 0
            if settings.seek:
                dialog = xbmcgui.Dialog()
                seek = dialog.numeric(2, 'Time to seek to', '00:00')
                for r in re.finditer('(\d+)\:(\d+)' ,seek, re.DOTALL):
                    seekHours, seekMins = r.groups()
                    seek = int(seekMins) + (int(seekHours)*60)

            try:
                service
            except NameError:
                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30051), addon.getLocalizedString(30052))
                xbmc.log(addon.getLocalizedString(30050)+ constants.PLUGIN_NAME + '-login', xbmc.LOGERROR)
                xbmcplugin.endOfDirectory(self.plugin_handle)
                return

            #settings.setCacheParameters()

            if mode == 'memorycachevideo':
                settings.play = True
                settings.download = True
            elif mode == 'playvideo':
                settings.play = False
                settings.download = False
                settings.playOriginal = True

            if settings.cache:
                settings.download = False
                settings.play = False


            encfs = settings.getParameter('encfs', False)

            #testing
            player = gPlayer.gPlayer()
            player.setService(service)
            resolvedPlayback = True
            startPlayback = False
            #package = None

            if encfs:



                #temporarly force crypto with encfs
                settings.setCryptoParameters()
                if settings.cryptoPassword != "":

                    mediaFile = file.file(filename, title, '', 0, '','')
                    mediaFolder = folder.folder(folderID,'')
                    (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder), title=title, contentType=8)
                    #override title
                    package.file.title = title
                    #(mediaURLs,package) = service.getPlaybackCall(None,title=title)
                    mediaURL = mediaURLs[0]
                    #mediaURL.url =  mediaURL.url +'|' + service.getHeadersEncoded()

                    # use streamer if defined
                    useStreamer = False
                    if not KODI:
                        item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                        thumbnailImage=package.file.thumbnail, path=mediaURL.url+'|' + service.getHeadersEncoded())
                        item.setPath(mediaURL.url+'|' + service.getHeadersEncoded())
                        xbmcplugin.setResolvedUrl(self.plugin_handle, True, item, encrypted=True)
                    elif KODI and service is not None and service.settings.streamer:
                        # test streamer
                        from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
                        from resources.lib import streamer
                        import urllib, urllib2
                        from SocketServer import ThreadingMixIn
                        import threading
                        try:
                            server = streamer.MyHTTPServer(('',  service.settings.streamPort), streamer.myStreamer)
                            server.setAccount(service, '')
                            #if we make it here, streamer was not already running as a service, so we need to abort and playback using normal method, otherwise we will lock

                        except:
                            useStreamer = True

                        if useStreamer:

                            url = 'http://localhost:' + str(service.settings.streamPort) + '/crypto_playurl'
                            req = urllib2.Request(url, 'url=' + mediaURL.url)
                            try:
                                response = urllib2.urlopen(req)
                                response.close()
                            except urllib2.URLError, e:
                                xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)


                            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                            thumbnailImage=package.file.thumbnail, path='http://localhost:' + str(service.settings.streamPort) + '/play')

                            item.setPath('http://localhost:' + str(service.settings.streamPort) + '/play')
                            xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)


                            ## contribution by dabinn
                            # handle situation where playback is skipped to next file, wait for new source to load
                            if KODI and player.isPlaying():
                                xbmc.sleep(100)

                            startPlayback = False
                            # need to seek?
                            if seek > 0:
                                player.PlayStream(mediaURL.url, item, seek, startPlayback=startPlayback, package=package)
                            elif float(package.file.cloudResume) > 0:
                                player.PlayStream(mediaURL.url, item, package.file.cloudResume, startPlayback=startPlayback, package=package)
                            elif float(package.file.resume) > 0:
                                player.PlayStream(mediaURL.url, item, package.file.resume, startPlayback=startPlayback, package=package)
                            else:
                                player.PlayStream(mediaURL.url, item, 0, startPlayback=startPlayback, package=package)



                            # must occur after playback started (resolve or startPlayback in player)
                            # load captions
                            if 0 and (settings.srt or settings.cc) and (service.protocol == 2 or service.protocol == 3):
                                while not (KODI and player.isPlaying()):
                                    xbmc.sleep(1000)

                                files = cache.getSRT(service)
                                for file in files:
                                    if file != '':
                                        try:
                                            #file = file.decode('unicode-escape')
                                            file = file.encode('utf-8')
                                        except:
                                            file = str(file)
                                        player.setSubtitles(file)

                            if KODI:
                                xbmc.sleep(100)

                            # we need to keep the plugin alive for as long as there is playback from the plugin, or the player object closes
                            while KODI and not player.isExit:
                                player.saveTime()
                                xbmc.sleep(5000)

                else:

                    settings.setEncfsParameters()

                    encryptedPath = settings.getParameter('epath', '')
                    dencryptedPath = settings.getParameter('dpath', '')

                    encfs_source = settings.encfsSource
                    encfs_target = settings.encfsTarget
                    encfs_inode = settings.encfsInode
                    mediaFile = file.file(filename, title, '', 0, '','')
                    mediaFolder = folder.folder(folderID,'')
                    (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder), title=title, contentType=8)
                    #(mediaURLs,package) = service.getPlaybackCall(None,title=title)
                    mediaURL = mediaURLs[0]

                    playbackTarget = encfs_target + dencryptedPath


                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                        thumbnailImage=package.file.thumbnail, path=playbackTarget)
                    #item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )

                    # right-click or integrated player (no opening stream dialog...)
                    if contextType == '':
                        # for STRM (force resolve) -- resolve-only
                        if settings.username != '':
                            resolvedPlayback = True
                            startPlayback = False
                        else:
                            startPlayback = True
                    # resolve for an opening stream dialog
                    else:
                        resolvedPlayback=True


                    # download if not already cached
            #        if (not xbmcvfs.exists(str(encfs_source) + encryptedPath +str(title))):
                    url = service.getDownloadURL(filename)

                    ## check for SRT
                    # use folderID, look for files with srt/sub
                    mediaItems = service.getMediaList(folderID,contentType=8)
                    encfsSubTitles = []

                    if mediaItems:
                        dirListINodes = {}
                        fileListINodes = {}

                        #create the files and folders for decrypting file/folder names
                        for itemx in mediaItems:

                                if itemx.file is None:
                                    xbmcvfs.mkdir(encfs_source + str(encryptedPath))
                                    xbmcvfs.mkdir(encfs_source + str(encryptedPath) + str(itemx.folder.title) + '/' )

                                    if encfs_inode == 0:
                                        dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(itemx.folder.title)).st_ino()))] = itemx.folder
                                    else:
                                        dirListINodes[(str(xbmcvfs.Stat(encfs_source + str(encryptedPath) + str(itemx.folder.title)).st_ctime()))] = itemx.folder
                                    #service.addDirectory(item.folder, contextType=contextType,  encfs=True)
                                else:
                                    xbmcvfs.mkdir(encfs_source +  str(encryptedPath))
                                    xbmcvfs.mkdir(encfs_source +  str(encryptedPath) + str(itemx.file.title))
                                    if encfs_inode == 0:
                                        fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath)+ str(itemx.file.title)).st_ino()))] = itemx
                                    else:
                                        fileListINodes[(str(xbmcvfs.Stat(encfs_source +  str(encryptedPath) + str(itemx.file.title)).st_ctime()))] = itemx
                                    #service.addMediaFile(itemx, contextType=contextType)
                                if KODI and encfs_inode > 0:
                                        xbmc.sleep(1000)



                        mediaList = ['.sub', '.srt']
                        media_re = re.compile("|".join(mediaList), re.I)


                        # encfs -- extract path
                        extrapulatedPath = re.compile('(.*?)/[^/]+$')

                        dencryptedPathWithoutFilename = extrapulatedPath.match(dencryptedPath)

                        if dencryptedPathWithoutFilename is None:
                            dencryptedPathWithoutFilename = ''
                        else:
                            dencryptedPathWithoutFilename = dencryptedPathWithoutFilename.group(1) +  '/'


                        #examine the decrypted file/folder names for files for playback and dirs for navigation
                        dirs, files = xbmcvfs.listdir(encfs_target + str(dencryptedPathWithoutFilename) )
                        for dir in dirs:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPathWithoutFilename) + dir).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPathWithoutFilename) + dir).st_ctime())

                            #we found a file
                            if index in fileListINodes.keys():
                                xbmcvfs.rmdir(encfs_target + str(dencryptedPathWithoutFilename) + dir)
                                fileListINodes[index].file.decryptedTitle = dir
                                if media_re.search(str(dir)):
                                    #we found a subtitle
                                    service.downloadGeneralFile(fileListINodes[index].mediaurl.url, str(encfs_source) + str(encryptedPath) +str(fileListINodes[index].file.title))
                                    # str(encfs_target) +  str(dencryptedPathWithoutFilename) + str(fileListINodes[index].file.decryptedTitle)
                                    encfsSubTitles.append(str(encfs_target) +  str(dencryptedPathWithoutFilename) + str(fileListINodes[index].file.decryptedTitle))

                        # file is already downloaded
                        for file in files:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPathWithoutFilename) + file).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_target + str(dencryptedPathWithoutFilename) + file).st_ctime())
                            if index in fileListINodes.keys():
                                fileListINodes[index].file.decryptedTitle = file
                                if media_re.search(str(file)):
                                    #we found a subtitle
            #                        service.addMediaFile(fileListINodes[index], contextType=contextType, encfs=True,  dpath=str(dencryptedPath) + str(file), epath=str(encryptedPath) )
            #                        service.downloadGeneralFile(fileListINodes[index], package, playbackURL=playbackTarget, folderName=str(encfs_source) + encryptedPath + str(fileListINodes[index].file.title))
            #                        service.downloadGeneralFile(fileListINodes[index].mediaurl.url, str(encfs_source) + str(encryptedPath) +str(title))
                                    encfsSubTitles.append(str(encfs_target) +  str(dencryptedPathWithoutFilename) + str(fileListINodes[index].file.decryptedTitle))


                    if  settings.encfsStream or settings.encfsCacheSingle:
                        ## calculate the decrypted name of the file cache.mp4
                        #creating a cache.mp4 file
                        fileListINodes = {}
                        #workaround for this issue: https://github.com/xbmc/xbmc/pull/8531
                        if not xbmcvfs.exists(encfs_target + 'encfs.mp4') and not os.path.exists(encfs_target + 'encfs.mp4'):
                            xbmcvfs.mkdir(encfs_target + 'encfs.mp4')
                        if encfs_inode == 0:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_target +  'encfs.mp4').st_ino()))] = item
                        else:
                            fileListINodes[(str(xbmcvfs.Stat(encfs_target +  'encfs.mp4').st_ctime()))] = item
                        if KODI and encfs_inode > 0:
                            xbmc.sleep(1000)

                        dirs, files = xbmcvfs.listdir(encfs_source)
                        for dir in dirs:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_source + str(dir)).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_source + str(dir)).st_ctime())
                            #we found a file
                            if index in fileListINodes.keys():
                                xbmcvfs.rmdir(encfs_source + str(dir))
                                addon.setSetting('encfs_last', str(encryptedPath) +str(title))

                                if settings.encfsExp:
                                    service.downloadEncfsFile2(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', folderName=str(encfs_source) + str(dir), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)
                                else:
                                    service.downloadEncfsFile(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', folderName=str(encfs_source) + str(dir), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)

                        #already downloaded (partial or full)
                        for file in files:
                            index = ''
                            if encfs_inode == 0:
                                index = str(xbmcvfs.Stat(encfs_source + str(file)).st_ino())
                            else:
                                index = str(xbmcvfs.Stat(encfs_source + str(file)).st_ctime())
                            #we found a file
                            if index in fileListINodes.keys():
                                #resume
                                if settings.encfsLast == str(encryptedPath) +str(title):
                                    if settings.encfsExp:
                                        service.downloadEncfsFile2(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', force=False,folderName=str(encfs_source) + str(file), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)
                                    else:
                                        service.downloadEncfsFile(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', force=False,folderName=str(encfs_source) + str(file), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)
                                #new file
                                else:
                                    addon.setSetting('encfs_last', str(encryptedPath) +str(title))

                                    if settings.encfsExp:
                                        service.downloadEncfsFile2(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', force=True, folderName=str(encfs_source) + str(file), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)
                                    else:
                                        service.downloadEncfsFile(mediaURL, package, playbackURL=encfs_target + 'encfs.mp4', force=True, folderName=str(encfs_source) + str(file), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)


                    else:
                        #service.downloadEncfsFile2(mediaURL, package, playbackURL=playbackTarget, folderName=str(encfs_source) + encryptedPath +str(title), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)
                        service.downloadEncfsFile(mediaURL, package, playbackURL=playbackTarget, folderName=str(encfs_source) + encryptedPath +str(title), playback=resolvedPlayback,item=item, player=player, srt=encfsSubTitles)


                        #should already be playing by this point, so don't restart it
                    startPlayback = False
                    #exists; resolve for an opening stream dialog
            #        elif resolvedPlayback:
            #            xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)

                    # need to seek?
                    #if seek > 0:
                    #    player.PlayStream(playbackTarget, item, seek, startPlayback=startPlayback, package=package)
                    #elif float(package.file.resume) > 0:
                    #    player.PlayStream(playbackTarget, item, package.file.resume, startPlayback=startPlayback, package=package)
                    #else:
                    #    player.PlayStream(playbackTarget, item, 0, startPlayback=startPlayback, package=package)


                    #loop until finished
                    while KODI and not player.isExit:
                        player.saveTime()
                        xbmc.sleep(5000)

            elif mode == 'search' and contextType != '':

                    if title == '':

                        try:
                            dialog = xbmcgui.Dialog()
                            title = dialog.input(addon.getLocalizedString(30110), type=xbmcgui.INPUT_ALPHANUM)
                        except:
                            xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30100))
                            title = 'test'

                    mediaItems = service.getMediaList(title=title, contentType=contentType)
                    resolvedPlayback = False
                    startPlayback = False

                    options = []
                    urls = []

                    if mediaItems:
                        for item in mediaItems:
                            if item.file is None:
                                service.addDirectory( item.folder, contextType=contextType)
                            else:
                                service.addMediaFile(item, contextType=contextType)

            # non-encfs
            else:



                # file ID provided
                #if we don't have the docid, search for the video for playback
                if (filename != '' and mode == 'audio'):
                    mediaFile = file.file(filename, title, '', service.MEDIA_TYPE_MUSIC, '','')
                    mediaFolder = folder.folder(folderID,'')
                    (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
                elif filename != '':
                    mediaFile = file.file(filename, title, '', 0, '','')
                    mediaFolder = folder.folder(folderID,'')
                    (mediaURLs,package) = service.getPlaybackCall(package=package.package(mediaFile,mediaFolder))
                # search
                elif mode == 'search' and contextType == '':

                        if title == '':

                            try:
                                dialog = xbmcgui.Dialog()
                                title = dialog.input(addon.getLocalizedString(30110), type=xbmcgui.INPUT_ALPHANUM)
                            except:
                                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30100))
                                title = 'test'

                        mediaItems = service.getMediaList(title=title, contentType=contentType)
                        resolvedPlayback = False
                        startPlayback = False

                        options = []
                        urls = []

                        if mediaItems:
                            for item in mediaItems:
                                if item.file is None:
                                    service.addDirectory( item.folder, contextType=contextType)
                                else:
                                    options.append(item.file.title)
                                    urls.append(service.addMediaFile(item, contextType=contextType))

                        #search from STRM
                        if contextType == '':

                            ret = xbmcgui.Dialog().select(addon.getLocalizedString(30112), options)
                            playbackPath = urls[ret]

                            item = xbmcgui.ListItem(path=playbackPath+'|' + service.getHeadersEncoded())
                            item.setInfo( type="Video", infoLabels={ "Title": options[ret] , "Plot" : options[ret] } )
                            xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)

                # playback of entire folder?
                # folder only
                elif folderID != '' and title == '':
                    mediaItems = service.getMediaList(folderName=folderID, contentType=contentType)
                    if mediaItems:
                            player.setMedia(mediaItems)
                            player.playList(service)
                            resolvedPlayback = False

                # title provided
                else:
                    (mediaURLs,package) = service.getPlaybackCall(None,title=title)

                #ensure there is something play
                if package is not None:

                    # right-click - download (download only + force)
                    if not seek > 0 and not (settings.download and not settings.play):
                            # TESTING
                        if constants.CONST.spreadsheet and service.cloudResume == '2':
                            if service.worksheetID == '':

                                try:
                                    service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                                    spreadsheets = service.gSpreadsheet.getSpreadsheetList()
                                except:
                                    service.gSpreadsheet = None
                                    spreadsheets = None

                                for title in spreadsheets.iterkeys():
                                    if title == 'CLOUD_DB':
                                        worksheets = service.gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                                        for worksheet in worksheets.iterkeys():
                                            if worksheet == 'db':
                                                service.worksheetID = worksheets[worksheet]
                                                addon.setSetting(instanceName + '_spreadsheet', service.worksheetID)
                                            break
                                    break

                            # TESTING
                        if constants.CONST.spreadsheet and service.cloudResume == '2':

                            if service.gSpreadsheet is None:
                                service.gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)

                            media = service.gSpreadsheet.updateMediaPackage(service.worksheetID, package)


                    if package.file.commands != '':
                        exp = re.compile('([^\|]+):([^\|]+)\|?', re.IGNORECASE)
                        for cmd in exp.finditer(package.file.commands):
                            if cmd.group(1) == 'seek':
                                seek =  cmd.group(2)
                            elif cmd.group(1) == 'title':
                                package.file.title =  cmd.group(2)
                            elif cmd.group(1) == 'resume':
                                package.file.resume =  cmd.group(2)
                            elif cmd.group(1) == 'original':
                                if  cmd.group(2).lower() == 'true':
                                    settings.playOriginal =  True
                                else:
                                    settings.playOriginal =  False
                            elif cmd.group(1) == 'promptquality':
                                if  cmd.group(2).lower() == 'true':
                                    settings.promptQuality =  True
                                else:
                                    settings.promptQuality =  False

                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                thumbnailImage=package.file.thumbnail)

                    item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )



                    if mode != 'audio':
                        cache = cache.cache(package)
                        service.cache = cache
                        package.file.thumbnail = cache.setThumbnail(service)

                        if settings.srt and  (service.protocol == 2 or service.protocol == 3):
                            cache.setSRT(service)

                        # download closed-captions
                        if settings.cc and  (service.protocol == 2 or service.protocol == 3):
                            cache.setCC(service)


                        mediaURL = service.getMediaSelection(mediaURLs, folderID, filename)
                        #mediaURL.url = mediaURL.url +'|' + service.getHeadersEncoded()

        #                if not seek > 0  and package.file.resume > 0 and not settings.cloudResumePrompt:
        #                    returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30176), str(int(float(package.file.resume)/360)) + ':'+ str(int(float(package.file.resume)/60)) + ':' + str(int(float(package.file.resume)%60)))
        #                    if not returnPrompt:
        #                        package.file.resume = 0


                        ###
                        #right-menu context OR STRM
                        ##
                        if contextType == '':

                            # right-click - download (download only + force)
                            if not mediaURL.offline and settings.download and not settings.play:
                #                service.downloadMediaFile('',playbackPath, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize, force=True)
                                service.downloadMediaFile(mediaURL, item, package, force=True, playback=service.PLAYBACK_NONE)
                                resolvedPlayback = False
                                startPlayback = False

                            # right-click - play + cache (download and play)
                            elif not mediaURL.offline and settings.download and settings.play:
                    #            service.downloadMediaFile(self.plugin_handle, playbackPath, str(title)+'.'+ str(playbackQuality), folderID, filename, fileSize)
                                service.downloadMediaFile(mediaURL, item, package, playback=service.PLAYBACK_PLAYER, player=player)
                                resolvedPlayback = False

                            # STRM (force resolve) -- resolve-only
                            elif settings.username != '' or settings.strm:
                                startPlayback = False
                                resolvedPlayback = True

                                if not seek > 0  and package.file.cloudResume > 0 and not settings.cloudResumePrompt:
                                    returnPrompt = xbmcgui.Dialog().yesno(addon.getLocalizedString(30000), addon.getLocalizedString(30176), str(int(float(package.file.cloudResume)/360)) + ':'+ str(int(float(package.file.cloudResume)/60)) + ':' + str(int(float(package.file.cloudResume)%60)))
                                    if not returnPrompt:
                                        package.file.resume = 0
                                    else:
                                        package.file.resume = package.file.cloudResume
                                        item.setProperty('isResumable', '1')
                                        item.setProperty('ResumeTime', str(package.file.resume))
                                        item.setProperty('TotalTime', str(package.file.duration))


                            # right-click - play original / SRT / CC / Start At
                            elif settings.playOriginal or settings.srt or settings.cc or settings.seek:
                                startPlayback = True
                                resolvedPlayback = False


                            #### not in use
                            elif 0 and settings.resume:

                                spreadshetModule = settings.getSetting('library', False)
                                spreadshetName = settings.getSetting('library_filename', 'TVShows')

                                media = {}
                                if spreadshetModule:
                                    try:
                                        gSpreadsheet = gSpreadsheets.gSpreadsheets(service,addon, user_agent)
                                        service.gSpreadsheet = gSpreadsheet
                                        spreadsheets = gSpreadsheet.getSpreadsheetList()
                                    except:
                                        spreadshetModule = False

                                    if spreadshetModule:
                                      for title in spreadsheets.iterkeys():
                                        if title == spreadshetName:
                                            worksheets = gSpreadsheet.getSpreadsheetWorksheets(spreadsheets[title])

                                            for worksheet in worksheets.iterkeys():
                                                if worksheet == 'db':
                                                    media = gSpreadsheet.getMedia(worksheets[worksheet], fileID=package.file.id)
                                                    item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                                                            thumbnailImage=package.file.thumbnail)

                                                    item.setInfo( type="Video", infoLabels={ "Title": package.file.title , "Plot" : package.file.title } )
                                                    player.setWorksheet(worksheets['db'])
                                                    if len(media) == 0:
                                                        player.PlayStream(mediaURL.url, item, 0, package)
                                                    else:
                                                        player.PlayStream(mediaURL.url, item,media[0][7],package)
                                                    while KODI and not player.isExit:
                                                        player.saveTime()
                                                        xbmc.sleep(5000)

                            #offline
                            elif mediaURL.offline:
                                resolvedPlayback = True

                        # left-click - always cache (download and play)
                        elif not mediaURL.offline and settings.download and settings.play:
                            service.downloadMediaFile(mediaURL, item, package, player=player)
                            resolvedPlayback = False
                        else:
                            resolvedPlayback = True

                    else:
                        cache = cache.cache(package)
                        service.cache = cache

                        if constants.CONST.CACHE:
                            (localResolutions,localFiles) = service.cache.getFiles(service)
                        if constants.CONST.CACHE and len(localFiles) > 0:
                            mediaURL = mediaurl.mediaurl(str(localFiles[0]), 'offline', 0, 0)
                            mediaURL.offline = True
                        else:
                            mediaURL = mediaURLs[0]
                            if not settings.download:
                                mediaURL.url =  mediaURL.url +'|' + service.getHeadersEncoded()

                        resolvedPlayback = True

                        ###
                        #right-menu context or STRM
                        ##
                        if contextType == '':

                            #download - only, no playback
                            if  not mediaURL.offline and settings.download and not settings.play:
                                service.downloadMediaFile(mediaURL, item, package, force=True, playback=service.PLAYBACK_NONE)
                                resolvedPlayback = False

                            # for STRM (force resolve) -- resolve-only
                            elif settings.username != '':
                                startPlayback = False

                            #download & playback
                            elif not mediaURL.offline and settings.download and settings.play:
                                service.downloadMediaFile(mediaURL, item, package,  playback=service.PLAYBACK_PLAYER, player=player)
                                resolvedPlayback = False

                            else:
                                startPlayback = True


                        # from within pictures mode, music won't be playable, force
                        #direct playback from within plugin
                        elif contextType == 'image' and settings.cache:
                                item = xbmcgui.ListItem(path=str(playbackPath))
                                # local, not remote. "Music" is ok
                                item.setInfo( type="Music", infoLabels={ "Title": title } )
                                player.play(mediaURL.url, item)
                                resolvedPlayback = False

                        # from within pictures mode, music won't be playable, force
                        #direct playback from within plugin
                        elif contextType == 'image':
                            item = xbmcgui.ListItem(package.file.displayTitle(), iconImage=package.file.thumbnail,
                                                thumbnailImage=package.file.thumbnail, path=mediaURL.url)
                            # for unknown reasons, for remote music, if Music is tagged as Music, it errors-out when playing back from "Music", doesn't happen when labeled "Video"
                            item.setInfo( type="Video", infoLabels={ "Title": title } )

                            player.play(mediaURL.url, item)
                            resolvedPlayback = False
                        #download and play
                        elif settings.download and settings.play:
                            service.downloadMediaFile(mediaURL, item, package, player=player)
                            resolvedPlayback = False

                    if float(package.file.cloudResume) > 0 or  float(package.file.resume) > 0:
                        options = []
                        options.append('Resume from ' + str(int(float(package.file.resume))/60).zfill(2) +':' + str(int(float(package.file.resume))%60).zfill(2) )
                        options.append('Start from begining')

                        ret = xbmcgui.Dialog().select(addon.getLocalizedString(30176), options)
                        if ret == 1:
                            package.file.resume = 0

                    if resolvedPlayback:

                            # use streamer if defined
                            # streamer
                            useStreamer = False
                            if KODI and service is not None and service.settings.streamer:
                                # test streamer
                                from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
                                from resources.lib import streamer
                                import urllib, urllib2
                                from SocketServer import ThreadingMixIn
                                import threading
                                try:
                                    server = streamer.MyHTTPServer(('',  service.settings.streamPort), streamer.myStreamer)
                                    server.setAccount(service, '')
                                    #if we make it here, streamer was not already running as a service, so we need to abort and playback using normal method, otherwise we will lock

                                except:
                                    useStreamer = True

                            if KODI and useStreamer and service is not None and service.settings.streamer:


                                url = 'http://localhost:' + str(service.settings.streamPort) + '/playurl'
                                req = urllib2.Request(url, 'url=' + mediaURL.url)

                                try:
                                    response = urllib2.urlopen(req)
                                    response.read()
                                    response.close()
                                except urllib2.URLError, e:
                                    xbmc.log(self.addon.getAddonInfo('name') + ': ' + str(e), xbmc.LOGERROR)


                                item.setPath('http://localhost:' + str(service.settings.streamPort) + '/play')
                                xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)


                            else:
                                # regular playback
                                item.setPath(mediaURL.url)
                                xbmcplugin.setResolvedUrl(self.plugin_handle, True, item)


                    ## contribution by dabinn
                    # handle situation where playback is skipped to next file, wait for new source to load
                    if KODI and player.isPlaying():
                        xbmc.sleep(100)


                    # need to seek?
                    if seek > 0:
                        player.PlayStream(mediaURL.url, item, seek, startPlayback=startPlayback, package=package)
                    elif float(package.file.cloudResume) > 0:
                        player.PlayStream(mediaURL.url, item, package.file.cloudResume, startPlayback=startPlayback, package=package)
                    elif float(package.file.resume) > 0:
                        player.PlayStream(mediaURL.url, item, package.file.resume, startPlayback=startPlayback, package=package)
                    else:
                        player.PlayStream(mediaURL.url, item, 0, startPlayback=startPlayback, package=package)

                    # must occur after playback started (resolve or startPlayback in player)
                    # load captions
                    if  (settings.srt or settings.cc) and  (service.protocol == 2 or service.protocol == 3):
                        while KODI and not player.isPlaying():
                            xbmc.sleep(1000)

                        files = cache.getSRT(service)
                        for file in files:
                            if file != '':
                                try:
                                    #file = file.decode('unicode-escape')
                                    file = file.encode('utf-8')
                                except:
                                    file = str(file)
                                player.setSubtitles(file)

                    if KODI:
                        xbmc.sleep(100)

                    # we need to keep the plugin alive for as long as there is playback from the plugin, or the player object closes
                    while KODI and not player.isExit:
                        player.saveTime()
                        xbmc.sleep(5000)

        xbmcplugin.endOfDirectory(self.plugin_handle)
        return


