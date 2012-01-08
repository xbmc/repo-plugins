# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


"""
    Plugin for Launching an applications
"""

# -*- coding: UTF-8 -*-
# main imports
import sys
import os
import fnmatch
import xbmc
import xbmcgui
import xbmcplugin

import time
import re
import urllib
import subprocess_hack
import xml.dom.minidom

import random
from traceback import print_exc

import shutil
from file_item import Thumbnails
thumbnails = Thumbnails()

import md5

from xbmcaddon import Addon
PLUGIN_DATA_PATH = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.advanced.launcher") )
__settings__ = Addon( id="plugin.program.advanced.launcher" )
__lang__ = __settings__.getLocalizedString

def __language__(string):
    return __lang__(string).encode('utf-8','ignore')

# source path for launchers data
BASE_PATH = xbmc.translatePath( os.path.join( "special://" , "profile" ) )
BASE_CURRENT_SOURCE_PATH = os.path.join( PLUGIN_DATA_PATH , "launchers.xml" )
TEMP_CURRENT_SOURCE_PATH = os.path.join( PLUGIN_DATA_PATH , "launchers.tmp" )
SHORTCUT_FILE = os.path.join( PLUGIN_DATA_PATH , "shortcut.cut" )

REMOVE_COMMAND = "%%REMOVE%%"
ADD_COMMAND = "%%ADD%%"
EDIT_COMMAND = "%%EDIT%%"
COMMAND_ARGS_SEPARATOR = "^^"
GET_INFO = "%%GET_INFO%%"
GET_THUMB = "%%GET_THUMB%%"
GET_FANART = "%%GET_FANART%%"
SEARCH_COMMAND = "%%SEARCH%%"
SEARCH_DATE_COMMAND = "%%SEARCH_DATE%%"
SEARCH_PLATFORM_COMMAND = "%%SEARCH_PLATFORM%%"
SEARCH_STUDIO_COMMAND = "%%SEARCH_STUDIO%%"
SEARCH_GENRE_COMMAND = "%%SEARCH_GENRE%%"

class Main:
    BASE_CACHE_PATH = xbmc.translatePath(os.path.join( "special://profile/Thumbnails", "Pictures" ))
    launchers = {}

    ''' initializes plugin and run the requiered action
        arguments:
            argv[0] - the path of the plugin (supplied by XBMC)
            argv[1] - the handle of the plugin (supplied by XBMC)
            argv[2] - one of the following (__language__( 30000 ) and 'rom' can be any launcher name or rom name created with the plugin) :
                /launcher - open the specific launcher (if exists) and browse its roms
                            if the launcher is standalone - run it.
                /launcher/rom - run the specifiec rom using it's launcher.
                                ignore command if doesn't exists.
                /launcher/%%REMOVE%% - remove the launcher
                /launcher/%%ADD%% - add a new rom (open wizard)
                /launcher/rom/%%REMOVE%% - remove the rom
                /%%ADD%% - add a new launcher (open wizard)
                /launcher/%%GET_INFO%% - get launcher info from configured scraper
                /launcher/%%GET_THUMB%% - get launcher thumb from configured scraper
                /launcher/%%GET_FANART%% - get launcher fanart from configured scraper
                /launcher/rom/%%GET_INFO%% - get rom info from configured scraper
                /launcher/rom/%%GET_THUMB%% - get rom thumb from configured scraper
                /launcher/rom/%%GET_FANART%% - get rom fanart from configured scraper

                (blank)     - open a list of the available launchers. if no launcher exists - open the launcher creation wizard.
    '''

    def __init__( self ):
        # store an handle pointer
        self._handle = int(sys.argv[ 1 ])

        self._path = sys.argv[ 0 ]

        # get users preference
        self._get_settings()
        self._load_launchers(self.get_xml_source())

        # get users scrapers preference
        self._get_scrapers()

        # get emulators preference
        exec "import resources.lib.emulators as _emulators_data"
        self._get_program_arguments = _emulators_data._get_program_arguments
        self._get_program_extensions = _emulators_data._get_program_extensions
        self._get_mame_title = _emulators_data._get_mame_title
        self._test_bios_file = _emulators_data._test_bios_file

        # if a commmand is passed as parameter
        param = sys.argv[ 2 ]
        if param:
            param = param[1:]
            command = param.split(COMMAND_ARGS_SEPARATOR)
            dirname = os.path.dirname(command[0])
            basename = os.path.basename(command[0])
            # check the action needed
            if (dirname):
                launcher = dirname
                rom = basename
                if (rom == REMOVE_COMMAND):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._remove_launcher(launcher)
                    else:
                        self._remove_rom(os.path.dirname(launcher), os.path.basename(launcher))
                if (rom == EDIT_COMMAND):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._edit_launcher(launcher)
                    else:
                        self._edit_rom(os.path.dirname(launcher), os.path.basename(launcher))
                if (rom == GET_INFO):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._scrap_launcher(launcher)
                    else:
                        self._scrap_rom(os.path.dirname(launcher), os.path.basename(launcher))
                if (rom == GET_THUMB):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._scrap_thumb_launcher(launcher)
                    else:
                        self._scrap_thumb_rom(os.path.dirname(launcher), os.path.basename(launcher))
                if (rom == GET_FANART):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._scrap_fanart_launcher(launcher)
                    else:
                        self._scrap_fanart_rom(os.path.dirname(launcher), os.path.basename(launcher))
                elif (rom == ADD_COMMAND):
                    self._add_roms(launcher)
                elif (rom == SEARCH_COMMAND):
                    self._find_add_roms(launcher)
                elif (rom == SEARCH_DATE_COMMAND):
                    self._find_date_add_roms(launcher)
                elif (rom == SEARCH_PLATFORM_COMMAND):
                    self._find_platform_add_roms(launcher)
                elif (rom == SEARCH_STUDIO_COMMAND):
                    self._find_studio_add_roms(launcher)
                elif (rom == SEARCH_GENRE_COMMAND):
                    self._find_genre_add_roms(launcher)
                else:
                    self._run_rom(launcher, rom)
            else:
                launcher = basename

                if (launcher == SEARCH_COMMAND):#search
                    # check if we need to get user input or search the rom list
                    self._find_roms()

                # if it's an add command
                elif (launcher == ADD_COMMAND):
                    self._add_new_launcher()
                else:
                    # if there is no rompath (a standalone launcher)
                    if (self.launchers[launcher]["rompath"] == ""):
                        # launch it
                        self._run_launcher(launcher)
                    else:
                        # otherwise, list the roms
                        self._get_roms(launcher)
        else:
            # otherwise get the list of the programs in the current folder
            if (not self._get_launchers()):
                # if no launcher found - attempt to add a new one
                if (self._add_new_launcher()):
                    self._get_launchers()
                else:
                    xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=False , cacheToDisc=False)

    def _remove_rom(self, launcherID, rom):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % self.launchers[launcherID]["roms"][rom]["name"])
        if (ret):
            self.launchers[launcherID]["roms"].pop(rom)
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcherID))

    def _empty_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30133 ) % self.launchers[launcherID]["name"])
        if (ret):
            self.launchers[launcherID]["roms"].clear()
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
    def _remove_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % self.launchers[launcherID]["name"])
        if (ret):
            self.launchers.pop(launcherID)
            self._save_launchers()
            if ( len(self.launchers) == 0 ):
                xbmc.executebuiltin("ReplaceWindow(Home)")
            else:
                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))


    def _edit_rom(self, launcher, rom):
        dialog = xbmcgui.Dialog()
        title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"])
        type = dialog.select(__language__( 30300 ) % title, [__language__( 30301 ),__language__( 30302 ),__language__( 30303 ), __language__( 30331 ) % self.launchers[launcher]["roms"][rom]["extrafanart"],__language__( 30304 )])
        if (type == 0 ):
            dialog = xbmcgui.Dialog()

            type2 = dialog.select(__language__( 30305 ), [__language__( 30311 ) % self.settings[ "datas_scraper" ],__language__( 30333 ),__language__( 30306 ) % self.launchers[launcher]["roms"][rom]["name"],__language__( 30307 ) % self.launchers[launcher]["roms"][rom]["gamesys"],__language__( 30308 ) % self.launchers[launcher]["roms"][rom]["release"],__language__( 30309 ) % self.launchers[launcher]["roms"][rom]["studio"],__language__( 30310 ) % self.launchers[launcher]["roms"][rom]["genre"],__language__( 30328 ) % self.launchers[launcher]["roms"][rom]["plot"][0:20],__language__( 30316 )])
                # Scrap rom Infos
            if (type2 == 0 ):
                self._scrap_rom(launcher,rom)
            if (type2 == 1 ):
                self._import_rom_nfo(launcher,rom)
            if (type2 == 2 ):
                # Edition of the rom title
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30037 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = self.launchers[launcher]["roms"][rom]["name"]
                    self.launchers[launcher]["roms"][rom]["name"] = title.replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
                    self._save_launchers()
            if (type2 == 3 ):
                # Selection of the rom game system
                dialog = xbmcgui.Dialog()
                platforms = _get_game_system_list()
                gamesystem = dialog.select(__language__( 30077 ), platforms)
                if (not gamesystem == -1 ):
                    self.launchers[launcher]["roms"][rom]["gamesys"] = platforms[gamesystem]
                    self._save_launchers()
            if (type2 == 4 ):
                # Edition of the rom release date
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["release"], __language__( 30038 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["release"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 5 ):
                # Edition of the rom studio name
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["studio"], __language__( 30039 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["studio"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 6 ):
                # Edition of the rom game genre
                keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["genre"], __language__( 30040 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcher]["roms"][rom]["genre"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 7 ):
                # Import of the rom game plot
                text_file = xbmcgui.Dialog().browse(1,__language__( 30080 ),"files",".txt|.dat", False, False)
                if (os.path.isfile(text_file)):
                    text_plot = open(text_file)
                    string_plot = text_plot.read()
                    text_plot.close()
                    self.launchers[launcher]["roms"][rom]["plot"] = string_plot.replace('&quot;','"')
                    self._save_launchers()
            if (type2 == 8 ):
                self._export_rom_nfo(launcher,rom)

        if (type == 1 ):
            dialog = xbmcgui.Dialog()
            thumb_diag = __language__( 30312 ) % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = __language__( 30321 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = __language__( 30322 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30302 ), [thumb_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_thumb_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom thumbnail image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["thumbpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        filename = self.launchers[launcher]["roms"][rom]["filename"]
                        if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                            file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_thumb.jpg')))
                        else:
                            file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '.jpg')))
                        if ( image != file_path ):
                            shutil.copy2( image.decode(sys.getfilesystemencoding(),'ignore') , file_path.decode(sys.getfilesystemencoding(),'ignore') )
                            self.launchers[launcher]["roms"][rom]["thumb"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))

            if (type2 == 2 ):
                # Link to a rom thumbnail image
                if (self.launchers[launcher]["roms"][rom]["thumb"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["thumb"]
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        self.launchers[launcher]["roms"][rom]["thumb"] = image
                        self._save_launchers()
                        _update_cache(image)
                        xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))

        if (type == 2 ):
            dialog = xbmcgui.Dialog()
            fanart_diag = __language__( 30312 ) % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = __language__( 30322 ) % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30303 ), [fanart_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_fanart_rom(launcher,rom)
            if (type2 == 1 ):
                # Import a rom fanart image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcher]["fanartpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        filename = self.launchers[launcher]["roms"][rom]["filename"]
                        if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                            file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_fanart.jpg')))
                        else:
                            file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '.jpg')))
                        if ( image != file_path ):
                            shutil.copy2( image.decode(sys.getfilesystemencoding(),'ignore') , file_path.decode(sys.getfilesystemencoding(),'ignore') )
                            self.launchers[launcher]["roms"][rom]["fanart"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))
            if (type2 == 2 ):
                # Link to a rom fanart image
                if (self.launchers[launcher]["roms"][rom]["fanart"] == ""):
                    imagepath = self.launchers[launcher]["roms"][rom]["filename"]
                else:
                    imagepath = self.launchers[launcher]["roms"][rom]["fanart"]
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        self.launchers[launcher]["roms"][rom]["fanart"] = image
                        self._save_launchers()
                        _update_cache(image)
                        xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))
        if (type == 3 ):
            # Selection of the rom extrafanarts path
            extrafanart = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, self.launchers[launcher]["roms"][rom]["extrafanart"])
            self.launchers[launcher]["roms"][rom]["extrafanart"] = extrafanart
            self._save_launchers()

        if (type == 4 ):
            self._remove_rom(launcher,rom)

        # Return to the launcher directory
        xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))


    def _scrap_thumb_rom(self, launcher, rom):
	if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'MAMEWorld' ):
            title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30065 ) % (self.launchers[launcher]["roms"][rom]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore'))))
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            covers = self._get_thumbnails_list(self.launchers[launcher]["roms"][rom]["gamesys"],keyboard.getText(),self.settings["game_region"],self.settings[ "thumb_image_size" ])
            if covers:
                nb_images = len(covers)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30066 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"])))
                covers.insert(0,(self.launchers[launcher]["roms"][rom]["thumb"],self.launchers[launcher]["roms"][rom]["thumb"],__language__( 30068 )))
                self.image_url = MyDialog(covers)
                if ( self.image_url ):
                    if (not self.image_url == self.launchers[launcher]["roms"][rom]["thumb"]):
                        img_url = self._get_thumbnail(self.image_url)
                        if ( img_url != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["thumbpath"] == self.launchers[launcher]["fanartpath"] ):
                                file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_thumb.jpg')))
                            else:
                                file_path = os.path.join(os.path.dirname(self.launchers[launcher]["thumbpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '.jpg')))
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30069 )))
                            h = urllib.urlretrieve(img_url,file_path)
                            self.launchers[launcher]["roms"][rom]["thumb"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))
                        else:
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"])))
            else:
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcher]["roms"][rom]["name"])))
        xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))

    def _scrap_thumb_launcher(self, launcherID):
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30065 ) % (self.launchers[launcherID]["name"],(self.settings[ "thumbs_scraper" ]).encode('utf-8','ignore'))))
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            covers = self._get_thumbnails_list(self.launchers[launcherID]["gamesys"],keyboard.getText(),self.settings["game_region"],self.settings[ "thumb_image_size" ])
            if covers:
                nb_images = len(covers)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30066 ) % (nb_images,self.launchers[launcherID]["name"])))
                covers.insert(0,(self.launchers[launcherID]["thumb"],self.launchers[launcherID]["thumb"],__language__( 30068 )))
                self.image_url = MyDialog(covers)
                if ( self.image_url ):
                    if (not self.image_url == self.launchers[launcherID]["thumb"]):
                        img_url = self._get_thumbnail(self.image_url)
                        if ( img_url != '' ):
                            file_path = os.path.join(self.launchers[launcherID]["thumbpath"],os.path.basename(self.launchers[launcherID]["application"])+'_thumb.jpg')
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30069 )))
                            h = urllib.urlretrieve(img_url,file_path)
                            self.launchers[launcherID]["thumb"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))
                        else:
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcherID]["name"])))
            else:
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30067 ) % (self.launchers[launcherID]["name"])))
        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _scrap_fanart_rom(self, launcher, rom):
	if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "fanarts_scraper" ] == 'MAMEWorld' ):
            title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30071 ) % (self.launchers[launcher]["roms"][rom]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore'))))
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            full_fanarts = self._get_fanarts_list(self.launchers[launcher]["roms"][rom]["gamesys"],keyboard.getText(),self.settings[ "fanart_image_size" ])
            if full_fanarts:
                nb_images = len(full_fanarts)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30072 ) % (nb_images,self.launchers[launcher]["roms"][rom]["name"])))
                full_fanarts.insert(0,(self.launchers[launcher]["roms"][rom]["fanart"],self.launchers[launcher]["roms"][rom]["fanart"],__language__( 30068 )))
                self.image_url = MyDialog(full_fanarts)
                if ( self.image_url ):
                    if (not self.image_url == self.launchers[launcher]["roms"][rom]["fanart"]):
                        img_url = self._get_fanart(self.image_url)
                        if ( img_url != '' ):
                            filename = self.launchers[launcher]["roms"][rom]["filename"]
                            if (self.launchers[launcher]["fanartpath"] == self.launchers[launcher]["thumbpath"] ):
                                file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '_fanart.jpg')))
                            else:
                                file_path = os.path.join(os.path.dirname(self.launchers[launcher]["fanartpath"]),os.path.basename(filename.replace("."+filename.split(".")[-1], '.jpg')))
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30074 )))
                            h = urllib.urlretrieve(img_url,file_path)
                            self.launchers[launcher]["roms"][rom]["fanart"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))
                        else:
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"])))
            else:
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcher]["roms"][rom]["name"])))
        xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))

    def _scrap_fanart_launcher(self, launcherID):
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30071 ) % (self.launchers[launcherID]["name"],(self.settings[ "fanarts_scraper" ]).encode('utf-8','ignore'))))
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            covers = self._get_fanarts_list(self.launchers[launcherID]["gamesys"],keyboard.getText(),self.settings[ "fanart_image_size" ])
            if covers:
                nb_images = len(covers)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30072 ) % (nb_images,self.launchers[launcherID]["name"])))
                covers.insert(0,(self.launchers[launcherID]["fanart"],self.launchers[launcherID]["fanart"],__language__( 30068 )))
                self.image_url = MyDialog(covers)
                if ( self.image_url ):
                    if (not self.image_url == self.launchers[launcherID]["fanart"]):
                        img_url = self._get_fanart(self.image_url)
                        if ( img_url != '' ):
                            filename = self.launchers[launcherID]["application"]
                            file_path = os.path.join(self.launchers[launcherID]["fanartpath"],os.path.basename(self.launchers[launcherID]["application"])+'_fanart.jpg')
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30074 )))
                            h = urllib.urlretrieve(img_url,file_path)
                            self.launchers[launcherID]["fanart"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))
                        else:
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcherID]["name"])))
            else:
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30073 ) % (self.launchers[launcherID]["name"])))
        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _scrap_rom(self, launcher, rom):
        # Edition of the rom name
        title=os.path.basename(self.launchers[launcher]["roms"][rom]["filename"]).split(".")[0]
        if ( self.launchers[launcher]["application"].lower().find('mame') > 0 ) or ( self.settings[ "datas_scraper" ] == 'MAMEWorld' ):
            keyboard = xbmc.Keyboard(title, __language__( 30079 ))
        else:
            keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            # Search game title
            results,display = self._get_games_list(keyboard.getText())
            if display:
                # Display corresponding game list found
                dialog = xbmcgui.Dialog()
                # Game selection
                selectgame = dialog.select(__language__( 30078 ) % ( self.settings[ "datas_scraper" ] ), display)
                if (not selectgame == -1):
                    if ( self.settings[ "ignore_title" ] ):
                        self.launchers[launcher]["roms"][rom]["name"] = title_format(self,title)
                    else:
                        print results[selectgame]["title"]
                        self.launchers[launcher]["roms"][rom]["name"] = title_format(self,results[selectgame]["title"])
                    gamedata = self._get_game_data(results[selectgame]["id"])
                    self.launchers[launcher]["roms"][rom]["genre"] = gamedata["genre"]
                    self.launchers[launcher]["roms"][rom]["release"] = gamedata["release"]
                    self.launchers[launcher]["roms"][rom]["studio"] = gamedata["studio"]
                    self.launchers[launcher]["roms"][rom]["plot"] = gamedata["plot"]
            else:
            	xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30076 )))
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))

    def _import_rom_nfo(self, launcher, rom):
        # Edition of the rom name
        nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"])[0]+".nfo"
        if (os.path.isfile(nfo_file)):
            f = open(nfo_file, 'r')
            item_nfo = f.read().replace('\r','').replace('\n','')
            item_title = re.findall( "<title>(.*?)</title>", item_nfo )
            item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
            item_year = re.findall( "<year>(.*?)</year>", item_nfo )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
            item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
            item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
            if len(item_title) > 0 : self.launchers[launcher]["roms"][rom]["name"] = item_title[0].replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
            self.launchers[launcher]["roms"][rom]["gamesys"] = self.launchers[launcher]["gamesys"]
            if len(item_year) > 0 :  self.launchers[launcher]["roms"][rom]["release"] = item_year[0]
            if len(item_publisher) > 0 : self.launchers[launcher]["roms"][rom]["studio"] = item_publisher[0]
            if len(item_genre) > 0 : self.launchers[launcher]["roms"][rom]["genre"] = item_genre[0]
            if len(item_plot) > 0 : self.launchers[launcher]["roms"][rom]["plot"] = item_plot[0].replace('&quot;','"')
            self._save_launchers()
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30083 ) % os.path.basename(nfo_file)))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30082 ) % os.path.basename(nfo_file)))

    def _export_rom_nfo(self, launcher, rom):
        nfo_file=os.path.splitext(self.launchers[launcher]["roms"][rom]["filename"].decode(sys.getfilesystemencoding()))[0]+".nfo"
        if (os.path.isfile(nfo_file)):
            shutil.move( nfo_file, nfo_file+".tmp" )
            destination= open( nfo_file, "w" )
            source= open( nfo_file+".tmp", "r" )
            first_genre=0
            for line in source:
                item_title = re.findall( "<title>(.*?)</title>", line )
                item_platform = re.findall( "<platform>(.*?)</platform>", line )
                item_year = re.findall( "<year>(.*?)</year>", line )
                item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
                item_genre = re.findall( "<genre>(.*?)</genre>", line )
                item_plot = re.findall( "<plot>(.*?)</plot>", line )
                if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcher]["roms"][rom]["name"].replace("‚",",")+"</title>\n"
                if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n"
                if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n"
                if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n"
                if len(item_genre) > 0 :
					if first_genre == 0 :
						line = "\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n"
						first_genre = 1
                if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n"
                destination.write( line )
            source.close()
            destination.close()
            os.remove(nfo_file+".tmp")
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30087 ) % os.path.basename(nfo_file)))
        else:
            usock = open( nfo_file, 'w' )
            usock.write("<game>\n")
            usock.write("\t<title>"+self.launchers[launcher]["roms"][rom]["name"].replace("‚",",")+"</title>\n")
            usock.write("\t<platform>"+self.launchers[launcher]["roms"][rom]["gamesys"]+"</platform>\n")
            usock.write("\t<year>"+self.launchers[launcher]["roms"][rom]["release"]+"</year>\n")
            usock.write("\t<publisher>"+self.launchers[launcher]["roms"][rom]["studio"]+"</publisher>\n")
            usock.write("\t<genre>"+self.launchers[launcher]["roms"][rom]["genre"]+"</genre>\n")
            usock.write("\t<plot>"+self.launchers[launcher]["roms"][rom]["plot"]+"</plot>\n")
            usock.write("</game>\n")
            usock.close()
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30086 ) % os.path.basename(nfo_file)))

    def _add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30106 ), [__language__( 30105 ),__language__( 30320 )])
        if (type == 0 ):
            self._import_roms(launcher)
        if (type == 1 ):
            self._add_new_rom(launcher)

        # Return to the launcher directory
        xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))


    def _edit_launcher(self, launcherID):
        dialog = xbmcgui.Dialog()
        title=os.path.basename(self.launchers[launcherID]["application"])
        if ( self.launchers[launcherID]["rompath"] == "" ):
            type = dialog.select(__language__( 30300 ) % title, [__language__( 30301 ),__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30302 ),__language__( 30303 ),__language__( 30323 ),__language__( 30304 )])
        else:
            type = dialog.select(__language__( 30300 ) % title, [__language__( 30301 ),__language__( 30315 ) % self.launchers[launcherID]["args"],__language__( 30317 ) % self.launchers[launcherID]["romext"],__language__( 30302 ),__language__( 30303 ),__language__( 30334 ),__language__( 30323 ),__language__( 30304 )])
	type_nb = 0

        # Edition of the launcher infos
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            type2 = dialog.select(__language__( 30319 ), [__language__( 30311 ) % self.settings[ "datas_scraper" ],__language__( 30333 ),__language__( 30306 ) % self.launchers[launcherID]["name"],__language__( 30307 ) % self.launchers[launcherID]["gamesys"],__language__( 30308 ) % self.launchers[launcherID]["release"],__language__( 30309 ) % self.launchers[launcherID]["studio"],__language__( 30310 ) % self.launchers[launcherID]["genre"],__language__( 30328 ) % self.launchers[launcherID]["plot"][0:20],__language__( 30316 )])
            if (type2 == 0 ):
                # Edition of the launcher name
                self._scrap_launcher(launcherID)
            if (type2 == 1 ):
                # Edition of the launcher name
                self._import_launcher_nfo(launcherID)
            if (type2 == 2 ):
                # Edition of the launcher name
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30037 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()
                    if ( title == "" ):
                        title = self.launchers[launcherID]["name"]
                    self.launchers[launcherID]["name"] = title.replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
                    self._save_launchers()
            if (type2 == 3 ):
                # Selection of the launcher game system
                dialog = xbmcgui.Dialog()
                platforms = _get_game_system_list()
                gamesystem = dialog.select(__language__( 30077 ), platforms)
                if (not gamesystem == -1 ):
                    self.launchers[launcherID]["gamesys"] = platforms[gamesystem]
                    self._save_launchers()
            if (type2 == 4 ):
                # Edition of the launcher release date
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["release"], __language__( 30038 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["release"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 5 ):
                # Edition of the launcher studio name
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["studio"], __language__( 30039 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["studio"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 6 ):
                # Edition of the launcher genre
                keyboard = xbmc.Keyboard(self.launchers[launcherID]["genre"], __language__( 30040 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    self.launchers[launcherID]["genre"] = keyboard.getText()
                    self._save_launchers()
            if (type2 == 7 ):
                # Import of the launcher plot
                text_file = xbmcgui.Dialog().browse(1,__language__( 30080 ),"files",".txt|.dat", False, False, self.launchers[launcherID]["application"])
                if ( os.path.isfile(text_file) == True ):
                    text_plot = open(text_file, 'r')
                    self.launchers[launcherID]["plot"] = text_plot.read()
                    text_plot.close()
                    self._save_launchers()
            if (type2 == 8 ):
                # Edition of the launcher name
                self._export_launcher_nfo(launcherID)

        # Edition of the launcher arguments
        type_nb = type_nb +1
        if (type == type_nb ):
            keyboard = xbmc.Keyboard(self.launchers[launcherID]["args"], __language__( 30052 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                self.launchers[launcherID]["args"] = keyboard.getText()
                self._save_launchers()

        # Edition of the launcher rom extensions (only for emulator launcher)
        if ( self.launchers[launcherID]["rompath"] != "" ):
            type_nb = type_nb +1
            if (type == type_nb ):
                if (not self.launchers[launcherID]["rompath"] == ""):
                    keyboard = xbmc.Keyboard(self.launchers[launcherID]["romext"], __language__( 30054 ))
                    keyboard.doModal()
                    if (keyboard.isConfirmed()):
                        self.launchers[launcherID]["romext"] = keyboard.getText()
                        self._save_launchers()

        # Launcher Thumbnail menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            thumb_diag = __language__( 30312 ) % ( self.settings[ "thumbs_scraper" ] )
            if ( self.settings[ "thumbs_scraper" ] == "GameFAQs" ) | ( self.settings[ "thumbs_scraper" ] == "MobyGames" ):
                thumb_diag = __language__( 30321 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "display_game_region" ])
            if ( self.settings[ "thumbs_scraper" ] == "Google" ):
                thumb_diag = __language__( 30322 ) % ( self.settings[ "thumbs_scraper" ],self.settings[ "thumb_image_size_display" ])
            type2 = dialog.select(__language__( 30302 ), [thumb_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_thumb_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher thumbnail image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["thumbpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        filename = self.launchers[launcherID]["application"]
                        file_path = os.path.join(self.launchers[launcherID]["thumbpath"],os.path.basename(self.launchers[launcherID]["application"])+'_thumb.jpg')
                        if ( image != file_path ):
                            shutil.copy2( image.decode(sys.getfilesystemencoding(),'ignore') , file_path.decode(sys.getfilesystemencoding(),'ignore') )
                            self.launchers[launcherID]["thumb"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))

            if (type2 == 2 ):
                # Link to a launcher thumbnail image
                if (self.launchers[launcherID]["thumb"] == ""):
                    imagepath = self.launchers[launcherID]["thumbpath"]
                else:
                    imagepath = self.launchers[launcherID]["thumb"]
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        self.launchers[launcherID]["thumb"] = image
                        self._save_launchers()
                        _update_cache(image)
                        xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30070 )))

        # Launcher Fanart menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            dialog = xbmcgui.Dialog()
            fanart_diag = __language__( 30312 ) % ( self.settings[ "fanarts_scraper" ] )
            if ( self.settings[ "fanarts_scraper" ] == "Google" ):
                fanart_diag = __language__( 30322 ) % ( self.settings[ "fanarts_scraper" ],self.settings[ "fanart_image_size_display" ].capitalize())
            type2 = dialog.select(__language__( 30303 ), [fanart_diag,__language__( 30332 ),__language__( 30313 )])
            if (type2 == 0 ):
                self._scrap_fanart_launcher(launcherID)
            if (type2 == 1 ):
                # Import a Launcher fanart image
                image = xbmcgui.Dialog().browse(2,__language__( 30041 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(self.launchers[launcherID]["fanartpath"]))
                if (image):
                    if (os.path.isfile(image)):
                        filename = self.launchers[launcherID]["application"]
                        file_path = os.path.join(self.launchers[launcherID]["fanartpath"],os.path.basename(self.launchers[launcherID]["application"])+'_fanart.jpg')
                        if ( image != file_path ):
                            shutil.copy2( image.decode(sys.getfilesystemencoding(),'ignore') , file_path.decode(sys.getfilesystemencoding(),'ignore') )
                            self.launchers[launcherID]["fanart"] = file_path
                            self._save_launchers()
                            _update_cache(file_path)
                            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))

            if (type2 == 2 ):
                # Link to a launcher fanart image
                if (self.launchers[launcherID]["fanart"] == ""):
                    imagepath = self.launchers[launcherID]["fanartpath"]
                else:
                    imagepath = self.launchers[launcherID]["fanart"]
                image = xbmcgui.Dialog().browse(2,__language__( 30042 ),"files",".jpg|.jpeg|.gif|.png", True, False, os.path.join(imagepath))
                if (image):
                    if (os.path.isfile(image)):
                        self.launchers[launcherID]["fanart"] = image
                        self._save_launchers()
                        _update_cache(image)
                        xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30075 )))

        # Launcher's Items List menu option
        if ( self.launchers[launcherID]["rompath"] != "" ):
            type_nb = type_nb+1
            if (type == type_nb ):
                dialog = xbmcgui.Dialog()
                type2 = dialog.select(__language__( 30334 ), [__language__( 30335 ),__language__( 30336 ),__language__( 30318 ),])
                # Import Items list form .nfo files
                if (type2 == 0 ):
                    self._import_items_list_nfo(launcherID)
                # Export Items list to .nfo files
                if (type2 == 1 ):
                    self._export_items_list_nfo(launcherID)
                # Empty Launcher menu option
                if (type2 == 2 ):
                    self._empty_launcher(launcherID)

        # Launcher Advanced menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            if self.launchers[launcherID]["minimize"] == "true":
		minimize_str = __language__( 30204 )
            else:
		minimize_str = __language__( 30205 )
            if self.launchers[launcherID]["lnk"] == "true":
		lnk_str = __language__( 30204 )
            else:
		lnk_str = __language__( 30205 )
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                filter = ".xbe|.cut"
            else:
                if (sys.platform == "win32"):
                    filter = ".bat|.exe|.cmd"
                else:
                    filter = ""
            if ( self.launchers[launcherID]["rompath"] != "" ):
                if (sys.platform == 'win32'):
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30331 ) % self.launchers[launcherID]["extrafanartpath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30324 ) % self.launchers[launcherID]["rompath"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30331 ) % self.launchers[launcherID]["extrafanartpath"],__language__( 30329 ) % minimize_str])
            else:
                if (sys.platform == 'win32'):
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30331 ) % self.launchers[launcherID]["extrafanartpath"],__language__( 30329 ) % minimize_str,__language__( 30330 ) % lnk_str])
                else:
                    type2 = dialog.select(__language__( 30323 ), [__language__( 30327 ) % self.launchers[launcherID]["application"],__language__( 30325 ) % self.launchers[launcherID]["thumbpath"], __language__( 30326 ) % self.launchers[launcherID]["fanartpath"], __language__( 30331 ) % self.launchers[launcherID]["extrafanartpath"],__language__( 30329 ) % minimize_str])

            # Launcher application path menu option
            type2_nb = 0
            if (type2 == type2_nb ):
                app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter, False, False, self.launchers[launcherID]["application"])
                self.launchers[launcherID]["application"] = app
            # Launcher roms path menu option
            if ( self.launchers[launcherID]["rompath"] != "" ):
                type2_nb = type2_nb + 1
                if (type2 == type2_nb ):
                    rom_path = xbmcgui.Dialog().browse(0,__language__( 30058 ),"files", "", False, False, self.launchers[launcherID]["rompath"])
                    self.launchers[launcherID]["rompath"] = rom_path
            # Launcher thumbnails path menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False, self.launchers[launcherID]["thumbpath"])
                self.launchers[launcherID]["thumbpath"] = thumb_path
            # Launcher fanarts path menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, self.launchers[launcherID]["fanartpath"])
                self.launchers[launcherID]["fanartpath"] = fanart_path
            # Launcher extrafanarts path menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, self.launchers[launcherID]["extrafanartpath"])
                self.launchers[launcherID]["extrafanartpath"] = fanart_path
            # Launcher minimize state menu option
            type2_nb = type2_nb + 1
            if (type2 == type2_nb ):
                dialog = xbmcgui.Dialog()
                type3 = dialog.select(__language__( 30203 ), ["%s (%s)" % (__language__( 30204 ),__language__( 30201 )), "%s (%s)" % (__language__( 30205 ),__language__( 30202 ))])
                if (type3 == 1 ):
                    self.launchers[launcherID]["minimize"] = "false"
                else:
                    self.launchers[launcherID]["minimize"] = "true"
            self._save_launchers()
            # Launcher internal lnk option
            if (sys.platform == 'win32'):
                type2_nb = type2_nb + 1
                if (type2 == type2_nb ):
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select(__language__( 30206 ), ["%s (%s)" % (__language__( 30204 ),__language__( 30201 )), "%s (%s)" % (__language__( 30205 ),__language__( 30202 ))])
                    if (type3 == 1 ):
                        self.launchers[launcherID]["lnk"] = "false"
                    else:
                        self.launchers[launcherID]["lnk"] = "true"
            self._save_launchers()

        # Remove Launcher menu option
        type_nb = type_nb+1
        if (type == type_nb ):
            self._remove_launcher(launcherID)

        if (type == -1 ):
            self._save_launchers()

        # Return to the launcher directory
        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _scrap_launcher(self, launcherID):
        # Edition of the launcher name
        keyboard = xbmc.Keyboard(self.launchers[launcherID]["name"], __language__( 30036 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            # Scrapping launcher name info
            results,display = self._get_games_list(keyboard.getText())
            if display:
                # Display corresponding game list found
                dialog = xbmcgui.Dialog()
                # Game selection
                selectgame = dialog.select(__language__( 30078 ), display)
                if (not selectgame == -1):
                    if ( self.settings[ "ignore_title" ] ):
                        self.launchers[launcherID]["name"] = title_format(self,self.launchers[launcherID]["name"])
                    else:
                        self.launchers[launcherID]["name"] = title_format(self,results[selectgame]["title"])
                    gamedata = self._get_game_data(results[selectgame]["id"])
                    self.launchers[launcherID]["genre"] = gamedata["genre"]
                    self.launchers[launcherID]["release"] = gamedata["release"]
                    self.launchers[launcherID]["studio"] = gamedata["studio"]
                    self.launchers[launcherID]["plot"] = gamedata["plot"]
            else:
            	xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30076 )))
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _import_launcher_nfo(self, launcherID):
        if ( len(self.launchers[launcherID]["rompath"]) > 0 ):
			nfo_file = os.path.join(self.launchers[launcherID]["rompath"],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        else:
            if ( len(self.settings[ "launcher_nfo_path" ]) > 0 ):
                nfo_file = os.path.join(self.settings[ "launcher_nfo_path" ],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
            else:
                nfo_file = xbmcgui.Dialog().browse(1,__language__( 30088 ),"files",".nfo", False, False)
        if (os.path.isfile(nfo_file)):
            f = open(nfo_file, 'r')
            item_nfo = f.read().replace('\r','').replace('\n','')
            item_title = re.findall( "<title>(.*?)</title>", item_nfo )
            item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
            item_year = re.findall( "<year>(.*?)</year>", item_nfo )
            item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
            item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
            item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
            self.launchers[launcherID]["name"] = item_title[0].replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
            self.launchers[launcherID]["gamesys"] = item_platform[0]
            self.launchers[launcherID]["release"] = item_year[0]
            self.launchers[launcherID]["studio"] = item_publisher[0]
            self.launchers[launcherID]["genre"] = item_genre[0]
            self.launchers[launcherID]["plot"] = item_plot[0].replace('&quot;','"')
            self._save_launchers()
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30083 ) % os.path.basename(nfo_file)))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30082 ) % os.path.basename(nfo_file)))

    def _export_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
		    self._export_rom_nfo(launcherID, rom)

    def _import_items_list_nfo(self, launcherID):
        for rom in self.launchers[launcherID]["roms"].iterkeys():
		    self._import_rom_nfo(launcherID, rom)

    def _export_launcher_nfo(self, launcherID):
        if ( len(self.launchers[launcherID]["rompath"]) > 0 ):
			nfo_file = os.path.join(self.launchers[launcherID]["rompath"],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        else:
            if ( len(self.settings[ "launcher_nfo_path" ]) > 0 ):
                nfo_file = os.path.join(self.settings[ "launcher_nfo_path" ],os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
            else:
                nfo_path = xbmcgui.Dialog().browse(0,__language__( 30089 ),"files",".nfo", False, False)
                nfo_file = os.path.join(nfo_path,os.path.basename(os.path.splitext(self.launchers[launcherID]["application"])[0]+".nfo"))
        if (os.path.isfile(nfo_file)):
            shutil.move( nfo_file, nfo_file+".tmp" )
            destination= open( nfo_file, "w" )
            source= open( nfo_file+".tmp", "r" )
            for line in source:
                item_title = re.findall( "<title>(.*?)</title>", line )
                item_platform = re.findall( "<platform>(.*?)</platform>", line )
                item_year = re.findall( "<year>(.*?)</year>", line )
                item_publisher = re.findall( "<publisher>(.*?)</publisher>", line )
                item_genre = re.findall( "<genre>(.*?)</genre>", line )
                item_plot = re.findall( "<plot>(.*?)</plot>", line )
                if len(item_title) > 0 : line = "\t<title>"+self.launchers[launcherID]["name"].replace("‚",",")+"</title>\n"
                if len(item_platform) > 0 : line = "\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n"
                if len(item_year) > 0 : line = "\t<year>"+self.launchers[launcherID]["release"]+"</year>\n"
                if len(item_publisher) > 0 : line = "\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n"
                if len(item_genre) > 0 : line = "\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n"
                if len(item_plot) > 0 : line = "\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n"
                destination.write( line )
            source.close()
            destination.close()
            os.remove(nfo_file+".tmp")
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30087 ) % os.path.basename(nfo_file)))
        else:
            usock = open( nfo_file, 'w' )
            usock.write("<game>\n")
            usock.write("\t<title>"+self.launchers[launcherID]["name"].replace("‚",",")+"</title>\n")
            usock.write("\t<platform>"+self.launchers[launcherID]["gamesys"]+"</platform>\n")
            usock.write("\t<year>"+self.launchers[launcherID]["release"]+"</year>\n")
            usock.write("\t<publisher>"+self.launchers[launcherID]["studio"]+"</publisher>\n")
            usock.write("\t<genre>"+self.launchers[launcherID]["genre"]+"</genre>\n")
            usock.write("\t<plot>"+self.launchers[launcherID]["plot"]+"</plot>\n")
            usock.write("</game>\n")
            usock.close()
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30086 ) % os.path.basename(nfo_file)))

    def _run_launcher(self, launcherID):
        if (self.launchers.has_key(launcherID)):
            launcher = self.launchers[launcherID]
            apppath = os.path.dirname(launcher["application"])
            arguments = launcher["args"].replace("%apppath%" , apppath)
            arguments = arguments.replace("%APPPATH%" , apppath)
            if ( os.path.basename(launcher["application"]).lower().replace(".exe" , "") == "xbmc" ):
                xbmc.executebuiltin('XBMC.' + launcher["args"])
            else:
                if ( xbmc.Player().isPlaying() ):
                    if ( self.settings[ "media_state" ] == "0" ):
                        xbmc.executebuiltin('PlayerControl(Stop)')
                    if ( self.settings[ "media_state" ] == "1" ):
                        xbmc.executebuiltin('PlayerControl(Play)')
                    xbmc.sleep( 1000 )
                if (launcher["minimize"] == "true"):
                    xbmc.executehttpapi("Action(199)")
                if ( self.settings[ "launcher_notification" ] ):
                    xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30034 ) % launcher["name"]))
                if (os.environ.get( "OS", "xbox" ) == "xbox"):
                    xbmc.executebuiltin('XBMC.Runxbe(' + launcher["application"] + ')')
                else:
                    if (sys.platform == 'win32'):
                        if ( launcher["application"].split(".")[-1] == "lnk" ):
                            os.system("start \"\" \"%s\"" % (launcher["application"]))
                        else:
                            if ( launcher["application"].split(".")[-1] == "bat" ):
                                info = subprocess_hack.STARTUPINFO()
                                info.dwFlags = 1
                                if ( self.settings[ "show_batch" ] ):
                                    info.wShowWindow = 5
                                else:
                                    info.wShowWindow = 0
                            else:
                                info = 'None'
                            subprocess_hack.Popen(r'%s %s' % (launcher["application"], arguments), cwd=apppath, startupinfo=info)
                    elif (sys.platform.startswith('linux')):
                        os.system("\"%s\" %s " % (launcher["application"], arguments))
                    elif (sys.platform.startswith('darwin')):
                        os.system("\"%s\" %s " % (launcher["application"], arguments))
                    else:
                        pass;
                if (launcher["minimize"] == "true"):
                    xbmc.executehttpapi("Action(199)")
                if ( self.settings[ "media_state" ] == "1" ):
                    xbmc.sleep( 1000 )
                    xbmc.executebuiltin('PlayerControl(Play)')

    def _get_settings( self ):
        # get the users preference settings
        self.settings = {}
        self.settings[ "datas_method" ] = __settings__.getSetting( "datas_method" )
        self.settings[ "thumbs_method" ] = __settings__.getSetting( "thumbs_method" )
        self.settings[ "fanarts_method" ] = __settings__.getSetting( "fanarts_method" )
        self.settings[ "scrap_info" ] = __settings__.getSetting( "scrap_info" )
        self.settings[ "scrap_thumbs" ] = __settings__.getSetting( "scrap_thumbs" )
        self.settings[ "scrap_fanarts" ] = __settings__.getSetting( "scrap_fanarts" )
        self.settings[ "select_fanarts" ] = __settings__.getSetting( "select_fanarts" )
        self.settings[ "overwrite_thumbs" ] = ( __settings__.getSetting( "overwrite_thumbs" ) == "true" )
        self.settings[ "overwrite_fanarts" ] = ( __settings__.getSetting( "overwrite_fanarts" ) == "true" )
        self.settings[ "clean_title" ] = ( __settings__.getSetting( "clean_title" ) == "true" )
        self.settings[ "ignore_bios" ] = ( __settings__.getSetting( "ignore_bios" ) == "true" )
        self.settings[ "ignore_title" ] = ( __settings__.getSetting( "ignore_title" ) == "true" )
        self.settings[ "title_formating" ] = ( __settings__.getSetting( "title_formating" ) == "true" )
        self.settings[ "datas_scraper" ] = __settings__.getSetting( "datas_scraper" )
        self.settings[ "thumbs_scraper" ] = __settings__.getSetting( "thumbs_scraper" )
        self.settings[ "fanarts_scraper" ] = __settings__.getSetting( "fanarts_scraper" )
        self.settings[ "game_region" ] = ['All','EU','JP','US'][int(__settings__.getSetting('game_region'))]
        self.settings[ "display_game_region" ] = [__language__( 30136 ),__language__( 30144 ),__language__( 30145 ),__language__( 30146 )][int(__settings__.getSetting('game_region'))]
        self.settings[ "thumb_image_size" ] = ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(__settings__.getSetting('thumb_image_size'))]
        self.settings[ "thumb_image_size_display" ] = [__language__( 30136 ),__language__( 30137 ),__language__( 30138 ),__language__( 30139 ),__language__( 30140 ),__language__( 30141 ),__language__( 30142 ),__language__( 30143 )][int(__settings__.getSetting('thumb_image_size'))]
        self.settings[ "fanart_image_size" ] = ['','icon','small','medium','large','xlarge','xxlarge','huge'][int(__settings__.getSetting('fanart_image_size'))]
        self.settings[ "fanart_image_size_display" ] = [__language__( 30136 ),__language__( 30137 ),__language__( 30138 ),__language__( 30139 ),__language__( 30140 ),__language__( 30141 ),__language__( 30142 ),__language__( 30143 )][int(__settings__.getSetting('fanart_image_size'))]
        self.settings[ "launcher_thumb_path" ] = __settings__.getSetting( "launcher_thumb_path" )
        self.settings[ "launcher_fanart_path" ] = __settings__.getSetting( "launcher_fanart_path" )
        self.settings[ "launcher_nfo_path" ] = __settings__.getSetting( "launcher_nfo_path" )
        self.settings[ "media_state" ] = __settings__.getSetting( "media_state" )
        self.settings[ "show_batch" ] = ( __settings__.getSetting( "show_batch" ) == "true" )
        self.settings[ "recursive_scan" ] = ( __settings__.getSetting( "recursive_scan" ) == "true" )
        self.settings[ "launcher_notification" ] = ( __settings__.getSetting( "launcher_notification" ) == "true" )

    def _get_scrapers( self ):
        # get the users gamedata scrapers preference
        exec "import resources.scrapers.datas.%s.datas_scraper as _data_scraper" % ( self.settings[ "datas_scraper" ] )
        self._get_games_list = _data_scraper._get_games_list
        self._get_game_data = _data_scraper._get_game_data
        self._get_first_game = _data_scraper._get_first_game

        # get the users thumbs scrapers preference
        exec "import resources.scrapers.thumbs.%s.thumbs_scraper as _thumbs_scraper" % ( self.settings[ "thumbs_scraper" ] )
        self._get_thumbnails_list = _thumbs_scraper._get_thumbnails_list
        self._get_thumbnail = _thumbs_scraper._get_thumbnail

        # get the users fanarts scrapers preference
        exec "import resources.scrapers.fanarts.%s.fanarts_scraper as _fanarts_scraper" % ( self.settings[ "fanarts_scraper" ] )
        self._get_fanarts_list = _fanarts_scraper._get_fanarts_list
        self._get_fanart = _fanarts_scraper._get_fanart

    def _run_rom(self, launcherID, romName):
        if (self.launchers.has_key(launcherID)):
            launcher = self.launchers[launcherID]
            if (launcher["roms"].has_key(romName)):
                rom = self.launchers[launcherID]["roms"][romName]
                romfile = os.path.basename(rom["filename"])
                apppath = os.path.dirname(launcher["application"])
                rompath = os.path.dirname(rom["filename"])
                romname = os.path.splitext(romfile)[0]

                ext3s = ['.cd1', '-cd1', '_cd1', ' cd1']
                files = []
                filesnames = []
                for ext3 in ext3s:
                    if ( romname.lower().find(ext3) > -1 ):
                        temprompath = os.path.dirname(rom["filename"])
                        try:
                            filesnames = os.listdir(temprompath)
                        except:
                            pass
                        namestem = romname[:-len(ext3)]
                        for filesname in filesnames:
                            if filesname[0:len(namestem)] == namestem and filesname[len(namestem):len(namestem)+len(ext3) - 1]  == ext3[:-1]:
                                for romext in launcher["romext"].split("|"):
                                    if filesname[-len(romext):].lower() == romext.lower() :
                                        Discnum = filesname[(len(namestem)+len(ext3)-1):filesname.rfind(".")]
                                        try:
                                            int(Discnum)
                                            files.append([Discnum, filesname, rom["filename"][:-len(romfile)]+filesname])
                                        except:
                                            pass
                        if len(files) > 0:
                            files.sort(key=lambda x: int(x[0]))
                            discs = []
                            for file in files:
                                discs.append(xbmc.getLocalizedString(427)+" "+file[0])
                            dialog = xbmcgui.Dialog()
                            type3 = dialog.select("%s:" % __language__( 30035 ), discs)
                            if type3 > -1 :
                                myresult = files[type3]
                                rom["filename"] = myresult[2]
                                romfile = myresult[2]
                                romname = myresult[2].split(".")[0]
                            else:
                                return ""

                arguments = launcher["args"].replace("%rom%" , rom["filename"])
                arguments = arguments.replace("%romfile%" , romfile)
                arguments = arguments.replace("%romname%" , romname)
                arguments = arguments.replace("%apppath%" , apppath)
                arguments = arguments.replace("%rompath%" , rompath)
                arguments = arguments.replace("%romspath%" , launcher["rompath"])
                arguments = arguments.replace("%ROM%" , rom["filename"])
                arguments = arguments.replace("%ROMFILE%" , romfile)
                arguments = arguments.replace("%ROMNAME%" , romname)
                arguments = arguments.replace("%APPPATH%" , apppath)
                arguments = arguments.replace("%ROMPATH%" , rompath)
                arguments = arguments.replace("%ROMSPATH%" , launcher["rompath"])
                if ( os.path.basename(launcher["application"]).lower().replace(".exe" , "") == "xbmc" ):
                    xbmc.executebuiltin('XBMC.' + arguments)
                else:
                    if ( xbmc.Player().isPlaying() ):
                        if ( self.settings[ "media_state" ] == "0" ):
                            xbmc.executebuiltin('PlayerControl(Stop)')
                        if ( self.settings[ "media_state" ] == "1" ):
                            xbmc.executebuiltin('PlayerControl(Play)')
                        xbmc.sleep( 1000 )
                    if (launcher["minimize"] == "true"):
                        xbmc.executehttpapi("Action(199)")
                    if ( self.settings[ "launcher_notification" ] ):
                        xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30034 ) % rom["name"]))
                    if (os.environ.get( "OS", "xbox" ) == "xbox"):
                        f=open(SHORTCUT_FILE, "wb")
                        f.write("<shortcut>\n")
                        f.write("    <path>" + launcher["application"] + "</path>\n")
                        f.write("    <custom>\n")
                        f.write("       <game>" + rom["filename"] + "</game>\n")
                        f.write("    </custom>\n")
                        f.write("</shortcut>\n")
                        f.close()
                        xbmc.executebuiltin('XBMC.Runxbe(' + SHORTCUT_FILE + ')')
                    else:
                        if (sys.platform == 'win32'):
                            if ( launcher["lnk"] == "true" ) and ( launcher["romext"] == "lnk" ):
                                os.system("start \"\" \"%s\"" % (arguments))
                            else:
                                if ( launcher["application"].split(".")[-1] == "bat" ):
                                    info = subprocess_hack.STARTUPINFO()
                                    info.dwFlags = 1
                                    if ( self.settings[ "show_batch" ] ):
                                        info.wShowWindow = 5
                                    else:
                                        info.wShowWindow = 0
                                else:
                                    info = 'None'
                                subprocess_hack.Popen(r'%s %s' % (launcher["application"], arguments), cwd=apppath, startupinfo=info)
                        elif (sys.platform.startswith('linux')):
                            os.system("\"%s\" %s " % (launcher["application"], arguments))
                        elif (sys.platform.startswith('darwin')):
                            os.system("\"%s\" %s " % (launcher["application"], arguments))
                        else:
                            pass;
                    if (launcher["minimize"] == "true"):
                        xbmc.executehttpapi("Action(199)")
                    if ( self.settings[ "media_state" ] == "1" ):
                        xbmc.sleep( 1000 )
                        xbmc.executebuiltin('PlayerControl(Play)')

    ''' get an xml data from an xml file '''
    def get_xml_source( self ):
        try:
            usock = open( BASE_CURRENT_SOURCE_PATH, 'r' )
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        if ( ok ):
            # clean, save and return the xml string
            xmlSource = xmlSource.replace("&amp;", "&")
            xmlSource = xmlSource.replace("&", "&amp;")
            f = open(BASE_CURRENT_SOURCE_PATH, 'w')
            f.write(xmlSource)
            f.close()
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

    def _save_launchers (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(TEMP_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(TEMP_CURRENT_SOURCE_PATH));

        usock = open( TEMP_CURRENT_SOURCE_PATH, 'w' )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<launchers>\n")
        for launcherIndex in sorted(self.launchers, key= lambda x : self.launchers[x]["name"]):
            launcher = self.launchers[launcherIndex]
            usock.write("\t<launcher>\n")
            usock.write("\t\t<id>"+launcherIndex+"</id>\n")
            # replace low-9 quotation mark by comma
            usock.write("\t\t<name>"+launcher["name"].replace("‚",",")+"</name>\n")
            usock.write("\t\t<application>"+launcher["application"]+"</application>\n")
            usock.write("\t\t<args>"+launcher["args"]+"</args>\n")
            usock.write("\t\t<rompath>"+launcher["rompath"]+"</rompath>\n")
            usock.write("\t\t<thumbpath>"+launcher["thumbpath"]+"</thumbpath>\n")
            usock.write("\t\t<fanartpath>"+launcher["fanartpath"]+"</fanartpath>\n")
            usock.write("\t\t<extrafanartpath>"+launcher["extrafanartpath"]+"</extrafanartpath>\n")
            usock.write("\t\t<romext>"+launcher["romext"]+"</romext>\n")
            usock.write("\t\t<platform>"+launcher["gamesys"]+"</platform>\n")
            usock.write("\t\t<thumb>"+launcher["thumb"]+"</thumb>\n")
            usock.write("\t\t<fanart>"+launcher["fanart"]+"</fanart>\n")
            usock.write("\t\t<genre>"+launcher["genre"]+"</genre>\n")
            usock.write("\t\t<release>"+launcher["release"]+"</release>\n")
            usock.write("\t\t<publisher>"+launcher["studio"]+"</publisher>\n")
            usock.write("\t\t<launcherplot>"+launcher["plot"]+"</launcherplot>\n")
            usock.write("\t\t<minimize>"+launcher["minimize"]+"</minimize>\n")
            usock.write("\t\t<lnk>"+launcher["lnk"]+"</lnk>\n")
            usock.write("\t\t<roms>\n")
            for romIndex in sorted(launcher["roms"], key= lambda x : launcher["roms"][x]["name"]):
                romdata = launcher["roms"][romIndex]
                usock.write("\t\t\t<rom>\n")
                usock.write("\t\t\t\t<id>"+romIndex+"</id>\n")
                # replace low-9 quotation mark by comma
                usock.write("\t\t\t\t<name>"+romdata["name"].replace("‚",",")+"</name>\n")
                usock.write("\t\t\t\t<filename>"+romdata["filename"]+"</filename>\n")
                usock.write("\t\t\t\t<platform>"+romdata["gamesys"]+"</platform>\n")
                usock.write("\t\t\t\t<thumb>"+romdata["thumb"]+"</thumb>\n")
                usock.write("\t\t\t\t<fanart>"+romdata["fanart"]+"</fanart>\n")
                usock.write("\t\t\t\t<extrafanart>"+romdata["extrafanart"]+"</extrafanart>\n")
                usock.write("\t\t\t\t<genre>"+romdata["genre"]+"</genre>\n")
                usock.write("\t\t\t\t<release>"+romdata["release"]+"</release>\n")
                usock.write("\t\t\t\t<publisher>"+romdata["studio"]+"</publisher>\n")
                usock.write("\t\t\t\t<gameplot>"+romdata["plot"]+"</gameplot>\n")
                usock.write("\t\t\t</rom>\n")
            usock.write("\t\t</roms>\n")
            usock.write("\t</launcher>\n")
        usock.write("</launchers>")
        usock.close()
        shutil.copy2(TEMP_CURRENT_SOURCE_PATH, BASE_CURRENT_SOURCE_PATH)
        os.remove(TEMP_CURRENT_SOURCE_PATH)


    ''' read the list of launchers and roms from launchers.xml file '''
    def _load_launchers(self, xmlSource):
        need_update = 0
        # clean, save and return the xml string
        xmlSource = xmlSource.replace("&amp;", "&")
        launchers = re.findall( "<launcher>(.*?)</launcher>", xmlSource )
        print "Launcher: found %d launchers" % ( len(launchers) )
        for launcher in launchers:
            launcherid = re.findall( "<id>(.*?)</id>", launcher )
            name = re.findall( "<name>(.*?)</name>", launcher )
            application = re.findall( "<application>(.*?)</application>", launcher )
            args = re.findall( "<args>(.*?)</args>", launcher )
            rompath = re.findall( "<rompath>(.*?)</rompath>", launcher )
            thumbpath = re.findall( "<thumbpath>(.*?)</thumbpath>", launcher )
            fanartpath = re.findall( "<fanartpath>(.*?)</fanartpath>", launcher )
            extrafanartpath = re.findall( "<extrafanartpath>(.*?)</extrafanartpath>", launcher )
            romext = re.findall( "<romext>(.*?)</romext>", launcher )
            gamesys = re.findall( "<platform>(.*?)</platform>", launcher )
            thumb = re.findall( "<thumb>(.*?)</thumb>", launcher )
            fanart = re.findall( "<fanart>(.*?)</fanart>", launcher )
            genre = re.findall( "<genre>(.*?)</genre>", launcher )
            release = re.findall( "<release>(.*?)</release>", launcher )
            studio = re.findall( "<publisher>(.*?)</publisher>", launcher )
            plot = re.findall( "<launcherplot>(.*?)</launcherplot>", launcher )
            lnk = re.findall( "<lnk>(.*?)</lnk>", launcher )
            minimize = re.findall( "<minimize>(.*?)</minimize>", launcher )
            romsxml = re.findall( "<rom>(.*?)</rom>", launcher )

            if len(launcherid) > 0 : launcherid = launcherid[0]
            else:
                launcherid = _get_SID()
                need_update = 1
                print launcherid
            # replace comma by single low-9 quotation mark
            if len(name) > 0 : name = name[0].replace(",","‚")
            else: name = "unknown"
            if len(application) > 0 : application = application[0]
            else: application = ""
            if len(args) > 0 : args = args[0]
            else: args = ""
            if len(rompath) > 0 : rompath = rompath[0]
            else: rompath = ""
            if len(thumbpath) > 0 : thumbpath = thumbpath[0]
            else: thumbpath = ""
            if len(fanartpath) > 0 : fanartpath = fanartpath[0]
            else: fanartpath = ""
            if len(extrafanartpath) > 0 : extrafanartpath = extrafanartpath[0]
            else: extrafanartpath = ""
            if len(romext) > 0: romext = romext[0]
            else: romext = ""
            if len(gamesys) > 0: gamesys = gamesys[0]
            else: gamesys = ""
            if len(thumb) > 0: thumb = thumb[0]
            else: thumb = ""
            if len(fanart) > 0: fanart = fanart[0]
            else: fanart = ""
            if len(genre) > 0: genre = genre[0]
            else: genre = ""
            if len(release) > 0: release = release[0]
            else: release = ""
            if len(studio) > 0: studio = studio[0]
            else: studio = ""
            if len(plot) > 0: plot = plot[0]
            else: plot = ""
            if len(lnk) > 0: lnk = lnk[0]
            else:
                if (sys.platform == 'win32'):
                    lnk = "true"
                else:
                    lnk = ""
            if len(minimize) > 0: minimize = minimize[0]
            else: minimize = "true"

            roms = {}
            for rom in romsxml:
                romid = re.findall( "<id>(.*?)</id>", rom )
                romname = re.findall( "<name>(.*?)</name>", rom )
                romfilename = re.findall( "<filename>(.*?)</filename>", rom )
                romgamesys = re.findall( "<platform>(.*?)</platform>", rom )
                romthumb = re.findall( "<thumb>(.*?)</thumb>", rom )
                romfanart = re.findall( "<fanart>(.*?)</fanart>", rom )
                romextrafanart = re.findall( "<extrafanart>(.*?)</extrafanart>", rom )
                romgenre = re.findall( "<genre>(.*?)</genre>", rom )
                romrelease = re.findall( "<release>(.*?)</release>", rom )
                romstudio = re.findall( "<publisher>(.*?)</publisher>", rom )
                romplot = re.findall( "<gameplot>(.*?)</gameplot>", rom )

                if len(romid) > 0 : romid = romid[0]
                else:
                    romid = _get_SID()
                    need_update = 1
                    print romid
                # replace comma by single low-9 quotation mark
                if len(romname) > 0 : romname = romname[0].replace(",","‚")
                else: romname = "unknown"
                if len(romfilename) > 0 : romfilename = romfilename[0]
                else: romfilename = ""
                if len(romgamesys) > 0 : romgamesys = romgamesys[0]
                else: romgamesys = ""
                if len(romthumb) > 0 : romthumb = romthumb[0]
                else: romthumb = ""
                if len(romfanart) > 0 : romfanart = romfanart[0]
                else: romfanart = ""
                if len(romextrafanart) > 0 : romextrafanart = romextrafanart[0]
                else: romextrafanart = ""
                if len(romgenre) > 0 : romgenre = romgenre[0]
                else: romgenre = ""
                if len(romrelease) > 0 : romrelease = romrelease[0]
                else: romrelease = ""
                if len(romstudio) > 0 : romstudio = romstudio[0]
                else: romstudio = ""
                if len(romplot) > 0 : romplot = romplot[0]
                else: romplot = ""

                # prepare rom object data
                romdata = {}
                romdata["name"] = romname
                romdata["filename"] = romfilename
                romdata["gamesys"] = romgamesys
                romdata["thumb"] = romthumb
                romdata["fanart"] = romfanart
                romdata["extrafanart"] = romextrafanart
                romdata["genre"] = romgenre
                romdata["release"] = romrelease
                romdata["studio"] = romstudio
                romdata["plot"] = romplot

                # add rom to the roms list (using id as index)
                roms[romid] = romdata

            # prepare launcher object data
            launcherdata = {}
            launcherdata["name"] = name
            launcherdata["application"] = application
            launcherdata["args"] = args
            launcherdata["rompath"] = rompath
            launcherdata["thumbpath"] = thumbpath
            launcherdata["fanartpath"] = fanartpath
            launcherdata["extrafanartpath"] = extrafanartpath
            launcherdata["romext"] = romext
            launcherdata["gamesys"] = gamesys
            launcherdata["thumb"] = thumb
            launcherdata["fanart"] = fanart
            launcherdata["genre"] = genre
            launcherdata["release"] = release
            launcherdata["studio"] = studio
            launcherdata["plot"] = plot
            launcherdata["lnk"] = lnk
            launcherdata["minimize"] = minimize
            launcherdata["roms"] = roms

            # add launcher to the launchers list (using id as index)
            self.launchers[launcherid] = launcherdata

        if ( need_update == 1 ):
            self._save_launchers()

    def _get_launchers( self ):
        if (len(self.launchers) > 0):
            for key in sorted(self.launchers, key= lambda x : self.launchers[x]["name"]):
                self._add_launcher(self.launchers[key]["name"], self.launchers[key]["application"], self.launchers[key]["rompath"], self.launchers[key]["thumbpath"], self.launchers[key]["fanartpath"], self.launchers[key]["extrafanartpath"], self.launchers[key]["romext"], self.launchers[key]["gamesys"], self.launchers[key]["thumb"], self.launchers[key]["fanart"], self.launchers[key]["genre"], self.launchers[key]["release"], self.launchers[key]["studio"], self.launchers[key]["plot"], self.launchers[key]["lnk"], self.launchers[key]["minimize"], self.launchers[key]["roms"], len(self.launchers), key)
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True
        else:
            return False

    def _get_roms( self, launcherID ):
        if (self.launchers.has_key(launcherID)):
            selectedLauncher = self.launchers[launcherID]
            # error 
            roms = selectedLauncher["roms"]
            print "Launcher: %s : found %d roms " % (launcherID, len(roms))
            if (len(roms) > 0) :
                for key in sorted(roms, key= lambda x : roms[x]["name"]):
                    self._add_rom(launcherID, roms[key]["name"], roms[key]["filename"], roms[key]["gamesys"], roms[key]["thumb"], roms[key]["fanart"], roms[key]["extrafanart"], roms[key]["genre"], roms[key]["release"], roms[key]["studio"], roms[key]["plot"], len(roms), key)
		xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
                return True
            else:
                return False
        else:
            return False

    def _report_hook( self, count, blocksize, totalsize ):
         percent = int( float( count * blocksize * 100) / totalsize )
         msg1 = __language__( 30033 )  % ( os.path.split( self.url )[ 1 ], )
         pDialog.update( percent, msg1 )
         if ( pDialog.iscanceled() ): raise

    def _import_roms(self, launcherID, addRoms = False):
        dialog = xbmcgui.Dialog()
        romsCount = 0
        filesCount = 0
        skipCount = 0
        selectedLauncher = self.launchers[launcherID]
        pDialog = xbmcgui.DialogProgress()
        app = selectedLauncher["application"]
        path = selectedLauncher["rompath"]
        exts = selectedLauncher["romext"]
        roms = selectedLauncher["roms"]
        # Get game system, thumbnails and fanarts paths from launcher
        thumb_path = selectedLauncher["thumbpath"]
        fanart_path = selectedLauncher["fanartpath"]
        extrafanart_path = selectedLauncher["extrafanartpath"]
        gamesys = selectedLauncher["gamesys"]

        #remove dead entries
        if (len(roms) > 0):
            i = 0
            removedRoms = 0
            ret = pDialog.create(__language__( 30000 ), __language__( 30501 ) % (path));

            for key in sorted(roms.iterkeys()):
                pDialog.update(i * 100 / len(roms))
                i += 1
                if (not os.path.isfile(roms[key]["filename"])):
                    del roms[key]
                    removedRoms += 1
            pDialog.close()
            if not (removedRoms == 0):
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30502 ) % (removedRoms)))

        ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path));

        files = []
        if ( self.settings[ "recursive_scan" ] ):
            for root, dirs, filess in os.walk(path):
                for filename in fnmatch.filter(filess, '*.*'):
                    files.append(os.path.join(root, filename))
        else:
            filesname = os.listdir(path)
            for filename in filesname:
                files.append(os.path.join(path, filename))

        for fullname in files:
            f = os.path.basename(fullname)
            thumb = ""
            fanart = ""
            if ( self.settings[ "datas_method" ] == "0" ):
                pDialog.update(filesCount * 100 / len(files), __language__( 30062 ) % (f.replace("."+f.split(".")[-1],"")))
            if ( self.settings[ "datas_method" ] == "1" ):
                pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30167 )))
            if ( self.settings[ "datas_method" ] == "2" ):
                pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
            for ext in exts.split("|"):
                romadded = False
                if f.upper().endswith("." + ext.upper()):
                    foundromfile = False;
                    for g in roms:
                        if ( roms[g]["filename"] == fullname ):
                            foundromfile = True;
                    ext3s = ['.cd', '-cd', '_cd', ' cd']
                    for ext3 in ext3s:
                       for nums in range(2, 9):
                           if ( f.lower().find(ext3 + str(nums)) > 0 ):
                               foundromfile = True
                    # Ignore MAME bios roms
                    romname = f[:-len(ext)-1]
                    romname = romname.replace('.',' ')
                    if ( app.lower().find('mame') > 0 ):
                        if ( self.settings["ignore_bios"] ):
                            if ( self._test_bios_file(romname)):
                                foundromfile = True
                    if ( foundromfile == False ):
                        # prepare rom object data
                        romdata = {}
                        results = []
                        # Romname conversion if MAME
                        if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'MAMEWorld' ):
                            romname = self._get_mame_title(romname)
                        # Clean multi-cd Title Name
                        ext3s = ['.cd1', '-cd1', '_cd1', ' cd1']
                        for ext3 in ext3s:
                            if ( romname.lower().find(ext3) > 0 ):
                               romname = romname[:-len(ext3)]
                        romdata["filename"] = fullname
                        romdata["gamesys"] = gamesys
                        romdata["extrafanart"] = extrafanart_path
                        romdata["genre"] = ""
                        romdata["release"] = ""
                        romdata["studio"] = ""
                        romdata["plot"] = ""

                        # Search game title from scrapers
                        if ( self.settings[ "datas_method" ] == "1" ):
                            nfo_file=os.path.splitext(romdata["filename"])[0]+".nfo"
                            if (os.path.isfile(nfo_file)):
                                ff = open(nfo_file, 'r')
                                item_nfo = ff.read().replace('\r','').replace('\n','')
                                item_title = re.findall( "<title>(.*?)</title>", item_nfo )
                                item_platform = re.findall( "<platform>(.*?)</platform>", item_nfo )
                                item_year = re.findall( "<year>(.*?)</year>", item_nfo )
                                item_publisher = re.findall( "<publisher>(.*?)</publisher>", item_nfo )
                                item_genre = re.findall( "<genre>(.*?)</genre>", item_nfo )
                                item_plot = re.findall( "<plot>(.*?)</plot>", item_nfo )
                                if len(item_title) > 0 : romdata["name"] = item_title[0].replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
                                romdata["gamesys"] = romdata["gamesys"]
                                if len(item_year) > 0 :  romdata["release"] = item_year[0]
                                if len(item_publisher) > 0 : romdata["studio"] = item_publisher[0]
                                if len(item_genre) > 0 : romdata["genre"] = item_genre[0]
                                if len(item_plot) > 0 : romdata["plot"] = item_plot[0].replace('&quot;','"')
                                ff.close()
                        else:
                            if ( self.settings[ "datas_method" ] != "0" ):
								romdata["name"] = clean_filename(romname)
								if ( app.lower().find('mame') > 0 ) or ( self.settings[ "datas_scraper" ] == 'MAMEWorld' ):
									results = self._get_first_game(f[:-len(ext)-1],gamesys)
									selectgame = 0
								else:
									if ( self.settings[ "scrap_info" ] == "1" ):
										results = self._get_first_game(romdata["name"],gamesys)
										selectgame = 0
									else:
										results,display = self._get_games_list(romdata["name"])
										if display:
											# Display corresponding game list found
											dialog = xbmcgui.Dialog()
											# Game selection
											selectgame = dialog.select(__language__( 30078 ) % ( self.settings[ "datas_scraper" ] ), display)
											if (selectgame == -1):
												results = []
								if results:
									foundname = results[selectgame]["title"]
									if (foundname != ""):
										if ( self.settings[ "ignore_title" ] ):
											romdata["name"] = title_format(self,romname)
										else:
											romdata["name"] = title_format(self,foundname)

										# Game other game data
										gamedata = self._get_game_data(results[selectgame]["id"])
										romdata["genre"] = gamedata["genre"]
										romdata["release"] = gamedata["release"]
										romdata["studio"] = gamedata["studio"]
										romdata["plot"] = gamedata["plot"]
										progress_display = romdata["name"] + " (" + romdata["release"] + ")"
									else:
										progress_display = romname + ": " +__language__( 30503 )
								else:
									romdata["name"] = title_format(self,romname)
									progress_display = romname + ": " +__language__( 30503 )
                            else:
                                romdata["name"] = title_format(self,romname)

                        # Search if thumbnails and fanarts already exist
                        ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
                        for ext2 in ext2s:
                            if ( thumb_path == fanart_path ):
                            	test_thumb = os.path.join(thumb_path, f.replace('.'+ext, '_thumb.'+ext2))
                            	test_fanart = os.path.join(fanart_path, f.replace('.'+ext, '_fanart.'+ext2))
                                if ( os.path.isfile(test_thumb) ):
                                    thumb = test_thumb
                                if ( os.path.isfile(test_fanart) ):
                                    fanart = test_fanart
                            else:
                            	test_thumb = os.path.join(thumb_path, f.replace('.'+ext, '.'+ext2))
                            	test_fanart = os.path.join(fanart_path, f.replace('.'+ext, '.'+ext2))
                                if ( os.path.isfile(test_thumb) ):
                                    thumb = test_thumb
                                if ( os.path.isfile(test_fanart) ):
                                    fanart = test_fanart

                        title = os.path.basename(romdata["filename"]).split(".")[0]
                        
                        if ( self.settings[ "thumbs_method" ] == "2" ):
                            # If overwrite is activated or thumb file not exist
                            if ( self.settings[ "overwrite_thumbs"] ) or ( thumb == "" ):
                                pDialog.update(filesCount * 100 / len(files), __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "thumbs_scraper" ].encode('utf-8','ignore')))
                                img_url=""
	                        if (thumb_path == fanart_path):
                                    thumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.jpg'))
                                else:
                                    thumb = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.jpg'))
	                        if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'MAMEWorld' ):
                                    covers = self._get_thumbnails_list(romdata["gamesys"],title,self.settings[ "game_region" ],self.settings[ "thumb_image_size" ])
                                else:
                                    covers = self._get_thumbnails_list(romdata["gamesys"],romdata["name"],self.settings[ "game_region" ],self.settings[ "thumb_image_size" ])
                                if covers:
                                    # If MAME roms return title screen, instead return first image
                                    if ( app.lower().find('mame') > 0 ) or ( self.settings[ "thumbs_scraper" ] == 'MAMEWorld' ):
                                        img_url = self._get_thumbnail(covers[1][0])
                                    else:
                                        if ( self.settings[ "scrap_thumbs" ] == "1" ):
                                            img_url = self._get_thumbnail(covers[0][0])
                                        else:
                                            nb_images = len(covers)
                                            pDialog.close()
                                            self.image_url = MyDialog(covers)
                                            if ( self.image_url ):
                                                img_url = self._get_thumbnail(self.image_url)
                                                ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path))
                                                pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                                    cached_thumb = thumbnails.get_cached_covers_thumb( thumb ).replace("tbn" , "jpg")
                                    if ( img_url !='' ):
                                        h = urllib.urlretrieve(img_url,thumb)
                                        shutil.copy2( thumb.decode(sys.getfilesystemencoding(),'ignore') , cached_thumb.decode(sys.getfilesystemencoding(),'ignore') )
                                    else:
                                        if ( not os.path.isfile(thumb) ) & ( os.path.isfile(cached_thumb) ):
                                            os.remove(cached_thumb)
                            romdata["thumb"] = thumb
                        else :
                            if ( self.settings[ "thumbs_method" ] == "0" ):
                                romdata["thumb"] = ""
                            else:
                                pDialog.update(filesCount * 100 / len(files), __language__( 30065 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30172 )))
                                romdata["thumb"] = thumb

                        if ( self.settings[ "fanarts_method" ] == "2" ):
                            # If overwrite activated or fanart file not exist
                            if ( self.settings[ "overwrite_fanarts"] ) or ( fanart == "" ):
                                pDialog.update(filesCount * 100 / len(files), __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "fanarts_scraper" ].encode('utf-8','ignore')))
                                img_url=""
                                if (fanart_path == thumb_path):
                                    fanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.jpg'))
                                else:
                                    fanart = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.jpg'))
	                        if ( app.lower().find('mame') > 0 ) or ( self.settings[ "fanarts_scraper" ] == 'MAMEWorld' ):
                                    covers = self._get_fanarts_list(romdata["gamesys"],title,self.settings[ "fanart_image_size" ])
                                else:
                                    covers = self._get_fanarts_list(romdata["gamesys"],romdata["name"],self.settings[ "fanart_image_size" ])
                                if covers:
                                    if ( self.settings[ "scrap_fanarts" ] == "1" ):
										if ( self.settings[ "select_fanarts" ] == "0" ):
											img_url = self._get_fanart(covers[0][0])
										if ( self.settings[ "select_fanarts" ] == "1" ):
											img_url = self._get_fanart(covers[int(round(len(covers)/2))-1][0])
										if ( self.settings[ "select_fanarts" ] == "2" ):
											img_url = self._get_fanart(covers[len(covers)-1][0])
                                    else:
                                        nb_images = len(covers)
                                        pDialog.close()
                                        self.image_url = MyDialog(covers)
                                        if ( self.image_url ):
                                            img_url = self._get_fanart(self.image_url)
                                            ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path))
                                            pDialog.update(filesCount * 100 / len(files), __language__( 30061 ) % (f.replace("."+f.split(".")[-1],""),self.settings[ "datas_scraper" ].encode('utf-8','ignore')))
                                    cached_thumb = thumbnails.get_cached_covers_thumb( fanart ).replace("tbn" , "jpg")
                                    if ( img_url !='' ):
                                        h = urllib.urlretrieve(img_url,fanart)
                                        shutil.copy2( fanart.decode(sys.getfilesystemencoding(),'ignore') , cached_thumb.decode(sys.getfilesystemencoding(),'ignore') )
                                    else:
                                        if ( not os.path.isfile(fanart) ) & ( os.path.isfile(cached_thumb) ):
                                            os.remove(cached_thumb)
                            romdata["fanart"] = fanart
                        else :
                            if ( self.settings[ "fanarts_method" ] == "0" ):
                                romdata["fanart"] = ""
                            else:
                                pDialog.update(filesCount * 100 / len(files), __language__( 30071 ) % (f.replace("."+f.split(".")[-1],""),__language__( 30172 )))
                                romdata["fanart"] = fanart

                        # add rom to the roms list (using name as index)
                        romid = _get_SID()
                        roms[romid] = romdata
                        romsCount = romsCount + 1

                        if (addRoms):
                            self._add_rom(launcherID, romdata["name"], romdata["filename"], romdata["gamesys"], romdata["thumb"], romdata["fanart"], romdata["extrafanart"], romdata["genre"], romdata["release"], romdata["studio"], romdata["plot"], len(files), key)
                            romadded = True
                if not romadded:
                    skipCount = skipCount + 1

            filesCount = filesCount + 1
        self._save_launchers()
        if ( self.settings[ "scrap_info" ] != "0" ):
            pDialog.close()
        xbmc.executebuiltin("XBMC.ReloadSkin()")
        if (skipCount == 0):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30015 ) % (romsCount) + " " + __language__( 30050 )))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30016 ) % (romsCount, skipCount) + " " + __language__( 30050 )))

    def _add_launcher(self, name, cmd, path, thumbpath, fanartpath, extrafanartpath, ext, gamesys, thumb, fanart, genre, release, studio, plot, lnk, minimize, roms, total, key) :
        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s)"    % (self._path, SEARCH_COMMAND) , ))
        commands.append((__language__( 30101 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        commands.append(( __language__( 30109 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, key, EDIT_COMMAND) , ))

        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
            commands.append((__language__( 30106 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, key, ADD_COMMAND) , ))

        if (thumb):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumb )
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )

        listitem.setProperty("fanart_image", fanart)
        listitem.setInfo( "video", { "Title": name, "Plot" : plot , "Studio" : studio , "Genre" : genre , "Premiered" : release  , "Writer" : gamesys , "Trailer" : extrafanartpath } )
        listitem.addContextMenuItems( commands )
        #xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, key), listitem=listitem, isFolder=folder, totalItems=total)
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, key), listitem=listitem, isFolder=folder)

    def _add_rom( self, launcherID, name, cmd , romgamesys, thumb, romfanart, romextrafanart, romgenre, romrelease, romstudio, romplot, total, key):
        icon = "DefaultProgram.png"
        if (thumb):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumb )
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        listitem.setProperty("fanart_image", romfanart)
        listitem.setInfo( "video", { "Title": name, "Label": name, "Plot" : romplot, "Studio" : romstudio, "Genre" : romgenre, "Premiered" : romrelease, "Date" : romrelease, "Writer" : romgamesys , "Trailer" : romextrafanart } )

        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s)"    % (self._path, SEARCH_COMMAND) , ))
        commands.append(( __language__( 30107 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, launcherID, key, EDIT_COMMAND) , ))
        listitem.addContextMenuItems( commands )
        #xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, launcherID, key), listitem=listitem, isFolder=False, totalItems=total)
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, launcherID, key), listitem=listitem, isFolder=False)

    def _add_new_rom ( self , launcherID) :
        dialog = xbmcgui.Dialog()
        launcher = self.launchers[launcherID]
        app = launcher["application"]
        ext = launcher["romext"]
        roms = launcher["roms"]
        rompath = launcher["rompath"]
        romgamesys = launcher["gamesys"]
        thumb_path = launcher["thumbpath"]
        fanart_path = launcher["fanartpath"]
        extrafanart_path = launcher["extrafanartpath"]

        romfile = dialog.browse(1, __language__( 30017 ),"files", "."+ext.replace("|","|."), False, False, rompath)
        if (romfile):
            title=os.path.basename(romfile)
            keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30018 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()
                if ( title == "" ):
                    title = os.path.basename(romfile)
                    title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                # prepare rom object data
                romdata = {}
                # Romname conversion if MAME
                if ( app.lower().find('mame') > 0 ):
                    romname = self._get_mame_title(title)
                    romdata["name"] = title_format(self,romname)
                else:
                    romdata["name"] = title_format(self,title)
                romdata["filename"] = romfile
                romdata["gamesys"] = romgamesys
                romdata["thumb"] = ""
                romdata["fanart"] = ""
                # Search for default thumbnails and fanart images path
                ext2s = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'PNG', 'JPG', 'GIF', 'JPEG', 'BMP']
                f = os.path.basename(romfile)
                for ext2 in ext2s:
                    if (thumb_path == fanart_path) :
                        if (os.path.isfile(os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.'+ext2)))):
                            romdata["thumb"] = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '_thumb.'+ext2))
                    else:
                        if (thumb_path == "") :
                            romdata["thumb"] = os.path.join(os.path.dirname(romfile), f.replace("."+f.split(".")[-1], '_thumb.jpg'))
                        else:
                            if (os.path.isfile(os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                romdata["thumb"] = os.path.join(thumb_path, f.replace("."+f.split(".")[-1], '.'+ext2))
                    if (fanart_path == thumb_path) :
                        if (os.path.isfile(os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.'+ext2)))):
                            romdata["fanart"] = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '_fanart.'+ext2))
                    else:
                        if (fanart_path == "") :
                            romdata["fanart"] = os.path.join(os.path.dirname(rompath), f.replace("."+f.split(".")[-1], '_fanart.jpg'))
                        else:
                            if (os.path.isfile(os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.'+ext2)))):
                                romdata["fanart"] = os.path.join(fanart_path, f.replace("."+f.split(".")[-1], '.'+ext2))
                romdata["extrafanart"] = extrafanart_path
                romdata["genre"] = ""
                romdata["release"] = ""
                romdata["studio"] = ""
                romdata["plot"] = ""

                # add rom to the roms list (using name as index)
                romid = _get_SID()
                roms[romid] = romdata

                xbmc.executebuiltin("XBMC.Notification(%s,%s, 3000)" % (__language__( 30000 ), __language__( 30019 ) + " " + __language__( 30050 )))
        self._save_launchers()

    def _add_new_launcher ( self ) :
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30020 ), [__language__( 30021 ), __language__( 30022 )])
        if (os.environ.get( "OS", "xbox" ) == "xbox"):
            filter = ".xbe|.cut"
        else:
            if (sys.platform == "win32"):
                filter = ".bat|.exe|.cmd|.lnk"
            else:
                filter = ""

        if (type == 0):
            app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
            if (app):
                argument = self._get_program_arguments(os.path.basename(app))
                argkeyboard = xbmc.Keyboard(argument, __language__( 30024 ))
                argkeyboard.doModal()
                args = argkeyboard.getText();
                title = os.path.basename(app)
                keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                keyboard.doModal()
                title = keyboard.getText()
                if ( title == "" ):
                    title = os.path.basename(app)
                    title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                # Selection of the launcher game system
                dialog = xbmcgui.Dialog()
                platforms = _get_game_system_list()
                gamesystem = dialog.select(__language__( 30077 ), platforms)
                # Selection of the thumbnails and fanarts path
                if ( self.settings[ "launcher_thumb_path" ] == "" ):
                    thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False)
                else:
                    thumb_path = self.settings[ "launcher_thumb_path" ]
                if ( self.settings[ "launcher_fanart_path" ] == "" ):
                    fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False)
                else:
                    fanart_path = self.settings[ "launcher_fanart_path" ]
                # prepare launcher object data
                launcherdata = {}
                launcherdata["name"] = title
                launcherdata["application"] = app
                launcherdata["args"] = args
                launcherdata["rompath"] = ""
                if (thumb_path):
                    launcherdata["thumbpath"] = thumb_path
                else:
                    launcherdata["thumbpath"] = ""
                if (fanart_path):
                    launcherdata["fanartpath"] = fanart_path
                    launcherdata["extrafanartpath"] = fanart_path
                else:
                    launcherdata["fanartpath"] = ""
                    launcherdata["extrafanartpath"] = ""
                launcherdata["romext"] = ""
                if (not gamesystem == -1 ):
                    launcherdata["gamesys"] = platforms[gamesystem]
                else:
                    launcherdata["gamesys"] = ""
                launcherdata["thumb"] = ""
                launcherdata["fanart"] = ""
                launcherdata["genre"] = ""
                launcherdata["release"] = ""
                launcherdata["studio"] = ""
                launcherdata["plot"] = ""
                if (sys.platform == "win32"):
                    launcherdata["lnk"] = "true"
                else:
                    launcherdata["lnk"] = ""
                launcherdata["minimize"] = "true"
                launcherdata["roms"] = {}

                # add launcher to the launchers list (using name as index)
                launcherid = _get_SID()
                self.launchers[launcherid] = launcherdata
                self._save_launchers()

                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
                return True

        elif (type == 1):
            app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
            if (app):
                path = xbmcgui.Dialog().browse(0,__language__( 30058 ),"files", "", False, False)
                if (path):
                    extensions = self._get_program_extensions(os.path.basename(app))
                    extkey = xbmc.Keyboard(extensions, __language__( 30028 ))
                    extkey.doModal()
                    if (extkey.isConfirmed()):
                        ext = extkey.getText()
                        argument = self._get_program_arguments(os.path.basename(app))
                        argkeyboard = xbmc.Keyboard(argument, __language__( 30024 ))
                        argkeyboard.doModal()
                        args = argkeyboard.getText();
                        title = os.path.basename(app)
                        keyboard = xbmc.Keyboard(title.replace('.'+title.split('.')[-1],'').replace('.',' '), __language__( 30025 ))
                        keyboard.doModal()
                        title = keyboard.getText()
                        if ( title == "" ):
                            title = os.path.basename(app)
                            title = title.replace('.'+title.split('.')[-1],'').replace('.',' ')
                        # Selection of the launcher game system
                        dialog = xbmcgui.Dialog()
                        platforms = _get_game_system_list()
                        gamesystem = dialog.select(__language__( 30077 ), platforms)
                        # Selection of the thumbnails and fanarts path
                        thumb_path = xbmcgui.Dialog().browse(0,__language__( 30059 ),"files","", False, False, os.path.join(path))
                        fanart_path = xbmcgui.Dialog().browse(0,__language__( 30060 ),"files","", False, False, os.path.join(path))
                        # prepare launcher object data
                        launcherdata = {}
                        launcherdata["name"] = title
                        launcherdata["application"] = app
                        launcherdata["args"] = args
                        launcherdata["rompath"] = path
                        if (thumb_path):
                            launcherdata["thumbpath"] = thumb_path
                        else:
                            launcherdata["thumbpath"] = ""
                        if (fanart_path):
                            launcherdata["fanartpath"] = fanart_path
                            launcherdata["extrafanartpath"] = fanart_path
                        else:
                            launcherdata["fanartpath"] = ""
                            launcherdata["extrafanartpath"] = ""
                        launcherdata["romext"] = ext
                        if (not gamesystem == -1 ):
                            launcherdata["gamesys"] = platforms[gamesystem]
                        else:
                            launcherdata["gamesys"] = ""
                        launcherdata["thumb"] = ""
                        launcherdata["fanart"] = ""
                        launcherdata["genre"] = ""
                        launcherdata["release"] = ""
                        launcherdata["studio"] = ""
                        launcherdata["plot"] = ""
                        if (sys.platform == "win32"):
                            launcherdata["lnk"] = "true"
                        else:
                            launcherdata["lnk"] = ""
                        launcherdata["minimize"] = "true"
                        launcherdata["roms"] = {}

                        # add launcher to the launchers list (using name as index)
                        launcherid = _get_SID()
                        self.launchers[launcherid] = launcherdata
                        self._save_launchers()
                        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
                        return True
        return False

    def _find_roms( self ):
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30400 ), [__language__( 30401 ),__language__( 30402 ),__language__( 30403 ),__language__( 30404 ),__language__( 30405 )])
	type_nb = 0

        #Search by Title
        if (type == type_nb ):
            keyboard = xbmc.Keyboard("", __language__( 30036 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                search = keyboard.getText()
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search, SEARCH_COMMAND))

        #Search by Release Date
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"release")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30406 ), search)
            if (not selected == -1 ):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_DATE_COMMAND))

        #Search by System Platform
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"gamesys")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30407 ), search)
            if (not selected == -1 ):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_PLATFORM_COMMAND))

        #Search by Studio
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"studio")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30408 ), search)
            if (not selected == -1 ):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_STUDIO_COMMAND))

        #Search by Genre
        type_nb = type_nb+1
        if (type == type_nb ):
            search = []
            search = _search_category(self,"genre")
            dialog = xbmcgui.Dialog()
            selected = dialog.select(__language__( 30409 ), search)
            if (not selected == -1 ):
                xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search[selected], SEARCH_GENRE_COMMAND))

    def _find_add_roms( self, search ):
	_find_category_roms( self, search, "name" )

    def _find_date_add_roms( self, search ):
	_find_category_roms( self, search, "release" )

    def _find_platform_add_roms( self, search ):
	_find_category_roms( self, search, "gamesys" )

    def _find_studio_add_roms( self, search ):
	_find_category_roms( self, search, "studio" )

    def _find_genre_add_roms( self, search ):
	_find_category_roms( self, search, "genre" )

class MainGui( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self, *args, **kwargs )
        xbmc.executebuiltin( "Skin.Reset(AnimeWindowXMLDialogClose)" )
        xbmc.executebuiltin( "Skin.SetBool(AnimeWindowXMLDialogClose)" )
        self.listing = kwargs.get( "listing" )

    def onInit(self):
        try :
            self.img_list = self.getControl(6)
            self.img_list.controlLeft(self.img_list)
            self.img_list.controlRight(self.img_list)
            self.getControl(3).setVisible(False)
        except :
            print_exc()
            self.img_list = self.getControl(3)

        self.getControl(5).setVisible(False)

        for index, item in enumerate(self.listing):
            listitem = xbmcgui.ListItem( item[2] )
            listitem.setIconImage( item[1] )
            listitem.setLabel2( item[0] )
            print item[1]
            
            self.img_list.addItem( listitem )
        self.setFocus(self.img_list)

    def onAction(self, action):
        #Close the script
        if action == 10 :
            self.close()

    def onClick(self, controlID):
        print controlID
        #action sur la liste
        if controlID == 6 or controlID == 3:
            #Renvoie l'item selectionne
            num = self.img_list.getSelectedPosition()
            print num
            self.selected_url = self.img_list.getSelectedItem().getLabel2()
            self.close()

    def onFocus(self, controlID):
        pass

def MyDialog(img_list):
    w = MainGui( "DialogSelect.xml", BASE_PATH, listing=img_list )
    w.doModal()
    try: return w.selected_url
    except:
        print_exc()
        return False
    del w

def _update_cache(file_path):
    cached_thumb = thumbnails.get_cached_covers_thumb( file_path ).replace("tbn" , "jpg")
    shutil.copy2( file_path.decode(sys.getfilesystemencoding(),'ignore') , cached_thumb.decode(sys.getfilesystemencoding(),'ignore') )
    xbmc.executebuiltin("XBMC.ReloadSkin()")

def title_format(self,title):
    if ( self.settings[ "clean_title" ] ):
       title = re.sub('\[.*?\]', '', title)
       title = re.sub('\(.*?\)', '', title)
    new_title = title.replace(",","‚").replace('"',"''").replace("/"," ⁄ ").rstrip()
    if ( self.settings[ "title_formating" ] ):
        if (title.startswith("The ")): new_title = title.replace("The ","",1)+"‚ The"
        if (title.startswith("A ")): new_title = title.replace("A ","",1)+"‚ A"
        if (title.startswith("An ")): new_title = title.replace("An ","",1)+"‚ An"
    else:
        if (title.endswith("‚ The")): new_title = "The "+"".join(title.rsplit("‚ The",1))
        if (title.endswith("‚ A")): new_title = "A "+"".join(title.rsplit("‚ A",1))
        if (title.endswith("‚ An")): new_title = "An "+"".join(title.rsplit("‚ An",1))
    return new_title

def clean_filename(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title.replace('_',' ').replace('-',' ').replace(':',' ').replace('.',' ').rstrip()
    return title

def _get_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = md5.new( str(t1 +t2) )
    sid = base.hexdigest()
    return sid

def _get_game_system_list():
    platforms = []
    try:
        rootDir = __settings__.getAddonInfo('path')
        if rootDir[-1] == ';':rootDir = rootDir[0:-1]
        resDir = os.path.join(rootDir, 'resources')
        scrapDir = os.path.join(resDir, 'scrapers')
        csvfile = open( os.path.join(scrapDir, 'gamesys'), "rb")
        for line in csvfile.readlines():
            result = line.replace('\n', '').replace('"', '').split(',')
            platforms.append(result[0])
        platforms.sort()
        return platforms
    except:
        return platforms

def _search_category(self,category):
    search = []
    if (len(self.launchers) > 0):
        for key in sorted(self.launchers.iterkeys()):
            if (len(self.launchers[key]["roms"]) > 0) :
                for keyr in sorted(self.launchers[key]["roms"].iterkeys()):
                    if ( self.launchers[key]["roms"][keyr][category] == "" ):
                        search.append("[ %s ]" % __language__( 30410 ))
                    else:
                        search.append(self.launchers[key]["roms"][keyr][category])
    search = list(set(search))
    search.sort()
    return search

def _find_category_roms( self, search, category ):
    #sorted by name
    if (len(self.launchers) > 0):
        rl = {}
        for launcherID in sorted(self.launchers.iterkeys()):
            selectedLauncher = self.launchers[launcherID]
            roms = selectedLauncher["roms"]
            notset = ("[ %s ]" % __language__( 30410 ))
            text = search.lower();
            empty = notset.lower();
            print "Launcher: %s : searching for release date %s " % (launcherID, text)
            if (len(roms) > 0) :
                #go through rom list and search for user input
                for keyr in sorted(roms.iterkeys()):
                    rom = roms[keyr][category].lower()
                    if (rom == "") and (text == empty):
                        rl[keyr] = roms[keyr]
                        rl[keyr]["launcherID"] = launcherID
                        print roms[keyr]["filename"]
                    if category == 'name':
                        if (not rom.find(text) == -1):
                            rl[keyr] = roms[keyr]
                            rl[keyr]["launcherID"] = launcherID
                            print roms[keyr]["filename"]
                    else:
                        if (rom == text):
                            rl[keyr] = roms[keyr]
                            rl[keyr]["launcherID"] = launcherID
                            print roms[keyr]["filename"]
    #print the list sorted
    print "Launcher: search found %d roms" % (len(rl))
    for key in sorted(rl.iterkeys()):
        self._add_rom(rl[key]["launcherID"], rl[key]["name"], rl[key]["filename"], rl[key]["gamesys"], rl[key]["thumb"], rl[key]["fanart"], rl[key]["extrafanart"], rl[key]["genre"], rl[key]["release"], rl[key]["studio"], rl[key]["plot"], len(rl), key)
        print "Launcher: %s : add %s" % (rl[key]["launcherID"], rl[key]["name"])
    xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )