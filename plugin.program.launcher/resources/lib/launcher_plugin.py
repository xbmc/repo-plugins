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

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

import time
import re
import urllib

BASE_PATH = os.getcwd()
print BASE_PATH

try:
    from xbmcaddon import Addon

    # source path for launchers data
    PLUGIN_DATA_PATH = xbmc.translatePath( os.path.join( "special://profile/addon_data", "plugin.program.launcher") )

    __settings__ = Addon( id="plugin.program.launcher" )
    __language__ = __settings__.getLocalizedString
    print "Mode AddOn ON"
    print PLUGIN_DATA_PATH


except : 
    # source path for launchers data
    PLUGIN_DATA_PATH = xbmc.translatePath( os.path.join( "special://profile/plugin_data", "programs", sys.modules[ "__main__" ].__plugin__) )

    __settings__ = xbmcplugin
    __language__ = __language__
    print "Mode plugin ON"
    print PLUGIN_DATA_PATH

# source path for launchers data
BASE_CURRENT_SOURCE_PATH = os.path.join( PLUGIN_DATA_PATH , "launchers.xml" )
SHORTCUT_FILE = os.path.join( PLUGIN_DATA_PATH , "shortcut.cut" )
THUMBS_PATH = os.path.join( PLUGIN_DATA_PATH , "thumbs" )

REMOVE_COMMAND = "%%REMOVE%%"
ADD_COMMAND = "%%ADD%%"
IMPORT_COMMAND = "%%IMPORT%%"
SCAN_COMMAND = "%%SCAN%%"
RENAME_COMMAND = "%%RENAME%%"
SET_THUMB_COMMAND = "%%SETTHUMB%%"
WAIT_TOGGLE_COMMAND = "%%WAIT_TOGGLE%%"
COMMAND_ARGS_SEPARATOR = "^^"
SEARCH_COMMAND = "%%SEARCH%%"#search
SEARCH_ALL_COMMAND = "%%SEARCH_ALL%%"#search all

# breaks the plugin partly
# when using
# xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s/%s)" % (self._path, launcherName, search, SEARCH_COMMAND))
# for example
#pDialog = xbmcgui.DialogProgress()
#pDialog.create( sys.modules[ "__main__" ].__plugin__ )

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
                /launcher/%%IMPORT%% - import roms from rom path into launcher
                /launcher/%%SCAN%% - scan for launcher & roms data from the internet
                /launcher/rom/%%SCAN%% - scan for rom data from the internet
                /launcher/%%WAIT_TOGGLE%% - toggle wait state 
                /%%ADD%% - add a new launcher (open wizard)
                
                (blank)     - open a list of the available launchers. if no launcher exists - open the launcher creation wizard.
    '''                        
    def __init__( self ):
        # store an handle pointer
        self._handle = int(sys.argv[ 1 ])
        print self._handle
                    
        self._path = sys.argv[ 0 ]
        
        # get users preference
        self._get_settings()
        self._load_launchers(self.get_xml_source())

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
                if (rom == RENAME_COMMAND):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._rename_launcher(launcher)
                    else:
                        self._rename_rom(os.path.dirname(launcher), os.path.basename(launcher))
                elif (rom == SCAN_COMMAND):
                    # check if it is a single rom scan or a launcher scan
                    if (not os.path.dirname(launcher)):
                        self._scan_launcher(launcher)
                    else:
                        romname = os.path.basename(launcher)
                        launcher = os.path.dirname(launcher)
                        self._search_thumb(launcher, romname)
                elif (rom == SET_THUMB_COMMAND):
                    thumb = command[1]
                    # check if it is a single rom or a launcher 
                    if (not os.path.dirname(launcher)):
                        self._set_thumb(launcher, "", thumb)
                    else:
                        romname = os.path.basename(launcher)
                        launcher = os.path.dirname(launcher)
                        self._set_thumb(launcher, romname, thumb)
                elif (rom == ADD_COMMAND):
                    self._add_new_rom(launcher)
                elif (rom == IMPORT_COMMAND):
                    self._import_roms(launcher)
                elif (rom == WAIT_TOGGLE_COMMAND):
                    self._toggle_wait(launcher)
                elif (rom == SEARCH_COMMAND):#search
                    # check if we need to get user input or search the rom list
                    if (not os.path.dirname(launcher)):
                        self._find_roms(launcher)
                    else:
                        romname = os.path.basename(launcher)
                        launcher = os.path.dirname(launcher)
                        self._find_add_roms(launcher, romname)
                elif (rom == SEARCH_ALL_COMMAND):#search all
                    # check if we need to get user input or search the rom list
                    self._find_add_all_roms(launcher)
                else:
                    self._run_rom(launcher, rom)
            else:
                launcher = basename

                if (launcher == SEARCH_ALL_COMMAND):#search all
                    # check if we need to get user input or search the rom list
                    self._find_all_roms()
                
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
                    
    def _remove_rom(self, launcher, rom):        
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % rom)
        if (ret):
            self.launchers[launcher]["roms"].pop(rom)
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))
            
    def _remove_launcher(self, launcherName):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % launcherName)
        if (ret):
            self.launchers.pop(launcherName)
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            
    def _rename_rom(self, launcher, rom):        
        keyboard = xbmc.Keyboard(self.launchers[launcher]["roms"][rom]["name"], __language__( 30018 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.launchers[launcher]["roms"][rom]["name"] = keyboard.getText()
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcher))
        
    def _rename_launcher(self, launcherName):
        keyboard = xbmc.Keyboard(self.launchers[launcherName]["name"], __language__( 30025 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.launchers[launcherName]["name"] = keyboard.getText()
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            
    def _run_launcher(self, launcherName):
        if (self.launchers.has_key(launcherName)):
            launcher = self.launchers[launcherName]
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                xbmc.executebuiltin('XBMC.Runxbe(' + launcher["application"] + ')')
            else:
                if (sys.platform == 'win32'):
                    if (launcher["wait"] == "true"):
                        cmd = "System.ExecWait"
                    else:
                        cmd = "System.Exec"
                    #this minimizes xbmc some apps seems to need it
                    xbmc.executehttpapi("Action(199)")
                    xbmc.executebuiltin("%s(\\\"%s\\\" \\\"%s\\\")" % (cmd, launcher["application"], launcher["args"]))
                    #this brings xbmc back
                    xbmc.executehttpapi("Action(199)")
                elif (sys.platform.startswith('linux')):
                    #this minimizes xbmc some apps seems to need it
                    xbmc.executehttpapi("Action(199)")
                    os.system("%s %s" % (launcher["application"], launcher["args"]))
                    #this brings xbmc back
                    xbmc.executehttpapi("Action(199)")
                elif (sys.platform.startswith('darwin')):
                    #this minimizes xbmc some apps seems to need it
                    xbmc.executehttpapi("Action(199)")
                    os.system("\"%s\" %s" % (launcher["application"], launcher["args"]))
                    #this brings xbmc back
                    xbmc.executehttpapi("Action(199)")
                else:
                    pass;
                    # unsupported platform
                             

    def _run_rom(self, launcherName, romName):
        if (self.launchers.has_key(launcherName)):
            launcher = self.launchers[launcherName]
            if (launcher["roms"].has_key(romName)):
                rom = self.launchers[launcherName]["roms"][romName]
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
                        if (launcher["wait"] == "true"):
                            cmd = "System.ExecWait"
                        else:
                            cmd = "System.Exec"
                        xbmc.executebuiltin("%s(\\\"%s\\\" %s \\\"%s\\\")" % (cmd, launcher["application"], launcher["args"], rom["filename"]))
                    elif (sys.platform.startswith('linux')):
                        os.system("\"%s\" %s \"%s\"" % (launcher["application"], launcher["args"], rom["filename"]))
                    elif (sys.platform.startswith('darwin')):
                        os.system("\"%s\" %s \"%s\"" % (launcher["application"], launcher["args"], rom["filename"]))
                    else:
                        pass;
                        # unsupported platform

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
            # return the xml string without \n\r (newline)
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

    def _save_launchers (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
            
        usock = open( BASE_CURRENT_SOURCE_PATH, 'w' )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<launchers>\n")
        for launcherIndex in self.launchers:
            launcher = self.launchers[launcherIndex]
            usock.write("\t<launcher>\n")
            usock.write("\t\t<name>"+launcher["name"]+"</name>\n")
            usock.write("\t\t<application>"+launcher["application"]+"</application>\n")
            usock.write("\t\t<args>"+launcher["args"]+"</args>\n")
            usock.write("\t\t<rompath>"+launcher["rompath"]+"</rompath>\n")
            usock.write("\t\t<romext>"+launcher["romext"]+"</romext>\n")
            usock.write("\t\t<thumb>"+launcher["thumb"]+"</thumb>\n")
            usock.write("\t\t<wait>"+launcher["wait"]+"</wait>\n")
            usock.write("\t\t<roms>\n")
            for romIndex in launcher["roms"]:
                romdata = launcher["roms"][romIndex]
                usock.write("\t\t\t<rom>\n")
                usock.write("\t\t\t\t<name>"+romdata["name"]+"</name>\n")
                usock.write("\t\t\t\t<filename>"+romdata["filename"]+"</filename>\n")
                usock.write("\t\t\t\t<thumb>"+romdata["thumb"]+"</thumb>\n")
                usock.write("\t\t\t</rom>\n")
            usock.write("\t\t</roms>\n")
            usock.write("\t</launcher>\n")            
        usock.write("</launchers>")
        usock.close()
        
    ''' read the list of launchers and roms from launchers.xml file '''
    def _load_launchers( self , xmlSource):
        launchers = re.findall( "<launcher>(.*?)</launcher>", xmlSource )
        print "Launcher: found %d launchers" % ( len(launchers) )
        for launcher in launchers:
            name = re.findall( "<name>(.*?)</name>", launcher )
            application = re.findall( "<application>(.*?)</application>", launcher )
            args = re.findall( "<args>(.*?)</args>", launcher )
            rompath = re.findall( "<rompath>(.*?)</rompath>", launcher )
            romext = re.findall( "<romext>(.*?)</romext>", launcher )
            thumb = re.findall( "<thumb>(.*?)</thumb>", launcher )
            wait = re.findall( "<wait>(.*?)</wait>", launcher )
            romsxml = re.findall( "<rom>(.*?)</rom>", launcher )

            if len(name) > 0 : name = name[0]
            else: name = "unknown"

            if len(application) > 0 : application = application[0]
            else: application = ""

            if len(args) > 0 : args = args[0]
            else: args = ""

            if len(rompath) > 0 : rompath = rompath[0]
            else: rompath = ""

            if len(romext) > 0: romext = romext[0]
            else: romext = ""

            if len(thumb) > 0: thumb = thumb[0]
            else: thumb = ""

            if len(wait) > 0: wait = wait[0]
            else: wait = ""
            
            roms = {}
            for rom in romsxml:
                romname = re.findall( "<name>(.*?)</name>", rom )
                romfilename = re.findall( "<filename>(.*?)</filename>", rom )
                romthumb = re.findall( "<thumb>(.*?)</thumb>", rom )

                if len(romname) > 0 : romname = romname[0]
                else: romname = "unknown"

                if len(romfilename) > 0 : romfilename = romfilename[0]
                else: romfilename = ""

                if len(romthumb) > 0 : romthumb = romthumb[0]
                else: romthumb = ""

                # prepare rom object data
                romdata = {}
                romdata["name"] = romname
                romdata["filename"] = romfilename
                romdata["thumb"] = romthumb

                # add rom to the roms list (using name as index)
                roms[romname] = romdata

            # prepare launcher object data
            launcherdata = {}
            launcherdata["name"] = name
            launcherdata["application"] = application
            launcherdata["args"] = args
            launcherdata["rompath"] = rompath
            launcherdata["romext"] = romext
            launcherdata["thumb"] = thumb
            launcherdata["wait"] = wait
            launcherdata["roms"] = roms

            # add launcher to the launchers list (using name as index)
            self.launchers[name] = launcherdata
    
    def _get_launchers( self ):
        if (len(self.launchers) > 0):
            for key in sorted(self.launchers.iterkeys()):
                self._add_launcher(self.launchers[key]["name"], self.launchers[key]["application"], self.launchers[key]["rompath"], self.launchers[key]["romext"], self.launchers[key]["thumb"], self.launchers[key]["wait"], self.launchers[key]["roms"], len(self.launchers))
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True   
        else:
            return False

    def _get_roms( self, launcherName ):
        if (self.launchers.has_key(launcherName)):
            selectedLauncher = self.launchers[launcherName]
            roms = selectedLauncher["roms"]
            print "Launcher: %s : found %d roms " % (launcherName, len(roms))
            if (len(roms) > 0) :
                for key in sorted(roms.iterkeys()):
                    self._add_rom(launcherName, roms[key]["name"], roms[key]["filename"], roms[key]["thumb"], len(roms))
            else:
                dialog = xbmcgui.Dialog()
                ret = dialog.yesno(__language__( 30000 ), __language__( 30013 ))
                if (ret):
                    self._import_roms(launcherName, addRoms = True)
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True
        else:
            return False

    def _search_thumb(self, launcherName, romname):
        search_engine = self._get_search_engine()
        pDialog.update( 0, __language__( 30031 ) % (launcherName, romname, self.settings[ "search_engine" ]) )
        if (romname) :
            search_string = "%s %s" % (romname, launcherName)
        else:
            search_string = "%s" % (launcherName)
        results = search_engine.search(search_string)
        stopSearch = False
        while (len(results)==0 and not stopSearch):
            keyboard = xbmc.Keyboard(search_string, __language__( 30034 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                search_string = keyboard.getText()
                results = search_engine.search(search_string)
            else:
                stopSearch = True
                
        if (len(results)>0):
            dialog = xbmcgui.Dialog()
            thumbs = []
            total = len(results)
            for result in results:
                thumbnail = self._get_thumbnail(result["thumb"])
                listitem = xbmcgui.ListItem( "%s (%s)" % (result["title"], result["url"]), iconImage="DefaultProgram.png", thumbnailImage=thumbnail )
                xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s/%s%s%s"  % (self._path, launcherName, romname, SET_THUMB_COMMAND, COMMAND_ARGS_SEPARATOR, result["url"]), listitem=listitem, isFolder=False, totalItems=total)

        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

    def _set_thumb(self, launcherName, romname, url):
        self.url = url
        # download thumb
        urllib.urlretrieve( url, None, self._report_hook )

        # copy it into thumbs path
        path = self.settings[ "thumbs_path" ]
        filepath = os.path.join(path, os.path.basename(url))
        
        pDialog.update( 100, __language__( 30032 ))
        xbmc.sleep( 50 )
        xbmc.executehttpapi( "FileCopy(%s,%s)" % (url, filepath, ) )

        launcher = self.launchers[launcherName]

        if (romname):
            rom = launcher["roms"][romname]
            rom["thumb"] = filepath
        else:
            launcher["thumb"] = filepath
                
        self._save_launchers()

        # returning back to the previous window
        if (romname):
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s)" % (self._path, launcherName))
        else:
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))

    def _report_hook( self, count, blocksize, totalsize ):
         percent = int( float( count * blocksize * 100) / totalsize )
         msg1 = __language__( 30033 )  % ( os.path.split( self.url )[ 1 ], )
         pDialog.update( percent, msg1 )
         if ( pDialog.iscanceled() ): raise
        
    def _scan_launcher(self, launchername):
        self._search_thumb(launchername, "")
        self._save_launchers()

    def _import_roms(self, launcherName, addRoms = False):
        dialog = xbmcgui.Dialog()
        romsCount = 0
        filesCount = 0
        skipCount = 0
        selectedLauncher = self.launchers[launcherName]
        pDialog = xbmcgui.DialogProgress()
        path = selectedLauncher["rompath"]
        exts = selectedLauncher["romext"]
        roms = selectedLauncher["roms"]
        
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
                xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30502 ) % (removedRoms)))
        
        ret = pDialog.create(__language__( 30000 ), __language__( 30014 ) % (path));
        
        files = os.listdir(path)
        for f in files:
            pDialog.update(filesCount * 100 / len(files))
            fullname = os.path.join(path, f)
            for ext in exts.split("|"):
                romadded = False
                if f.upper().endswith("." + ext.upper()):
                    romname =  f[:-len(ext)-1].capitalize()
                    if (not roms.has_key(romname)):
                        # prepare rom object data
                        romdata = {}
                        romname =  f[:-len(ext)-1].capitalize()
                        romdata["name"] = romname
                        romdata["filename"] = fullname
                        #try the filename of the rom with different extension to get a valid thumbnail
                        thumb = self._get_local_thumb(fullname)
                        if thumb:
                            romdata["thumb"] = thumb
                        else:
                            romdata["thumb"] = ""

                        # add rom to the roms list (using name as index)
                        roms[romname] = romdata
                        romsCount = romsCount + 1
                        
                        if (addRoms):
                            self._add_rom(launcherName, romdata["name"], romdata["filename"], romdata["thumb"], len(files))
                            romadded = True
                if not romadded:
                    skipCount = skipCount + 1
                
            filesCount = filesCount + 1    
        pDialog.close()
        self._save_launchers()
        if (skipCount == 0):
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30015 ) % (romsCount) + " " + __language__( 30050 )))
            #dialog.ok(__language__( 30000 ), (__language__( 30015 )+ "\n" + __language__( 30050 )) % (romsCount))
        else:
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 12000)" % (__language__( 30000 ), __language__( 30016 ) % (romsCount, skipCount) + " " + __language__( 30050 )))
            #dialog.ok(__language__( 30000 ), (__language__( 30016 )+ "\n" + __language__( 30050 )) % (romsCount, skipCount))

    def _get_thumbnail( self, thumbnail_url ):
        # make the proper cache filename and path so duplicate caching is unnecessary
        if ( not thumbnail_url.startswith( "http://" ) ): return thumbnail_url
        try:
            filename = xbmc.getCacheThumbName( thumbnail_url )
            filepath = xbmc.translatePath( os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename ) )
            # if the cached thumbnail does not exist fetch the thumbnail
            if ( not os.path.isfile( filepath ) ):
                # fetch thumbnail and save to filepath
                info = urllib.urlretrieve( thumbnail_url, filepath )
                # cleanup any remaining urllib cache
                urllib.urlcleanup()
            return filepath
        except:
            # return empty string if retrieval failed
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return ""
        
    def _get_thumb(self, displayName, fileName):
        exts = ['png', 'jpg', 'gif', 'bmp']
        for ext in exts:
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (displayName, ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename
            thumbfilename = os.path.join(self.settings[ "thumbs_path" ], "%s.%s" % (os.path.basename(fileName).split(".")[0], ext))
            if (os.path.isfile(thumbfilename)):
                return thumbfilename
        
    def _add_launcher(self, name, cmd, path, ext, thumb, wait, roms, total) :
        commands = []
        commands.append((__language__( 30512 ), "XBMC.RunPlugin(%s?%s)"    % (self._path, SEARCH_ALL_COMMAND) , ))#search all
        commands.append((__language__( 30511 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, SEARCH_COMMAND) , ))#search

        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
            commands.append((__language__( 30105 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, IMPORT_COMMAND) , ))
            commands.append((__language__( 30106 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, ADD_COMMAND) , ))
        #not working anymore
        #commands.append((__language__( 30102 ), "ReplaceWindow(Programs,%s?%s/%s)" % (self._path, name, SCAN_COMMAND) , ))
        commands.append((__language__( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
        if (sys.platform == "win32"):
            commands.append((__language__( 30103 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, WAIT_TOGGLE_COMMAND) , ))

        commands.append((__language__( 30101 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        commands.append((__language__( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))

        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
            
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, name), listitem=listitem, isFolder=folder, totalItems=total)

    def _add_rom( self, launcher, name, cmd , thumb, total):
        if (thumb):
            thumbnail = thumb
        else:
            thumbnail = self._get_thumb(name, cmd)
        icon = "DefaultProgram.png"
        if (thumbnail):
            listitem = xbmcgui.ListItem( name, iconImage=icon, thumbnailImage=thumbnail)
        else:
            listitem = xbmcgui.ListItem( name, iconImage=icon )
        commands = []
        commands.append(( __language__( 30511 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, launcher, SEARCH_COMMAND) , ))#search
        #not working anymore
        #commands.append(( __language__( 30102 ), "ReplaceWindow(Programs,%s?%s/%s/%s)" % (self._path, launcher, name, SCAN_COMMAND) , ))
        commands.append(( __language__( 30107 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, launcher, name, RENAME_COMMAND) , ))
        commands.append(( __language__( 30104 ), "XBMC.RunPlugin(%s?%s/%s/%s)" % (self._path, launcher, name, REMOVE_COMMAND) , ))
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s/%s"  % (self._path, launcher, name), listitem=listitem, isFolder=False, totalItems=total)

    def _add_new_rom ( self , launcherName) :
        dialog = xbmcgui.Dialog()
        launcher = self.launchers[launcherName]
        ext = launcher["romext"]
        roms = launcher["roms"]
        rompath = launcher["rompath"]
        
        romfile = dialog.browse(1, __language__( 30017 ),"files", "."+ext, False, False, rompath)
        if (romfile):
            title=os.path.basename(romfile).split(".")[0].capitalize()
            keyboard = xbmc.Keyboard(title, __language__( 30018 ))
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                title = keyboard.getText()

                # prepare rom object data
                romdata = {}
                romdata["name"] = title
                romdata["filename"] = romfile
                romdata["thumb"] = ""

                # add rom to the roms list (using name as index)
                roms[title] = romdata

                xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30019 ) + " " + __language__( 30050 )))
                #xbmcgui.Dialog().ok(__language__( 30000 ), __language__( 30019 )+ "\n" + __language__( 30050 ))
        self._save_launchers()

    def _add_new_launcher ( self ) :
        dialog = xbmcgui.Dialog()
        type = dialog.select(__language__( 30020 ), [__language__( 30021 ), __language__( 30022 )])
        if (os.environ.get( "OS", "xbox" ) == "xbox"):
            filter = ".xbe|.cut"
        else:
            if (sys.platform == "win32"):
                filter = ".bat|.exe|.cmd"
            else:
                filter = ""
            
        if (type == 0):
            app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
            if (app):
                argkeyboard = xbmc.Keyboard("", __language__( 30024 ))
                argkeyboard.doModal()
                if (argkeyboard.isConfirmed()):
                    args = argkeyboard.getText();
                    title = os.path.basename(app).split(".")[0].capitalize()
                    keyboard = xbmc.Keyboard(title, __language__( 30025 ))
                    keyboard.doModal()
                    if (keyboard.isConfirmed()):
                        title = keyboard.getText()                    
                        # prepare launcher object data
                        launcherdata = {}
                        launcherdata["name"] = title
                        launcherdata["application"] = app
                        launcherdata["args"] = args 
                        launcherdata["rompath"] = ""
                        launcherdata["romext"] = ""
                        #try the filename with different extension to get a valid thumbnail
                        thumb = self._get_local_thumb(app)
                        if thumb:
                            launcherdata["thumb"] = thumb
                        else:
                            launcherdata["thumb"] = ""
                        launcherdata["wait"] = "true"
                        launcherdata["roms"] = {}
                    
                        # add launcher to the launchers list (using name as index)
                        self.launchers[title] = launcherdata
                        self._save_launchers()

                        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
                        return True
        elif (type == 1):
            app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
            if (app):
                argkeyboard = xbmc.Keyboard("", __language__( 30024 ))
                argkeyboard.doModal()
                if (argkeyboard.isConfirmed()):
                    args = argkeyboard.getText();
                    path = xbmcgui.Dialog().browse(0,__language__( 30027 ),"files", "", False, False, os.path.dirname(app))
                    if (path):
                        extkey = xbmc.Keyboard("", __language__( 30028 ))
                        extkey.doModal()
                        if (extkey.isConfirmed()):
                            ext = extkey.getText()
                            title = os.path.basename(app).split(".")[0].capitalize()
                            keyboard = xbmc.Keyboard(title, __language__( 30025 ))
                            keyboard.doModal()
                            if (keyboard.isConfirmed()):
                                title = keyboard.getText()
                                # prepare launcher object data
                                launcherdata = {}
                                launcherdata["name"] = title
                                launcherdata["application"] = app
                                launcherdata["args"] = args 
                                launcherdata["rompath"] = path
                                launcherdata["romext"] = ext
                                #try the filename and path with different extension to get a valid thumbnail
                                thumb = self._get_local_thumb(path[:-1] + ".dir")
                                print "thumbs_path: " + path
                                print "thumbs_app: " + app
                                if thumb:
                                    launcherdata["thumb"] = thumb
                                else:
                                    thumb = self._get_local_thumb(app)
                                    if thumb:
                                        launcherdata["thumb"] = thumb
                                    else:
                                        launcherdata["thumb"] = ""
                                launcherdata["wait"] = "true"
                                launcherdata["roms"] = {}
                        
                                # add launcher to the launchers list (using name as index)
                                self.launchers[title] = launcherdata
                                self._save_launchers()
                                xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
                                return True
        return False

    def _toggle_wait( self, launcher ):
        # toggle wait state
        if (self.launchers[launcher]["wait"] == "true"):
            self.launchers[launcher]["wait"] = "false"
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30029 )  ))
            #xbmcgui.Dialog().ok(__language__( 30000 ), __language__( 30029 ))
        else:
            self.launchers[launcher]["wait"] = "true"
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30030 )  ))
            #xbmcgui.Dialog().ok(__language__( 30000 ), __language__( 30030 ))
        self._save_launchers()

        

    def _get_search_engine( self ):
        exec "import resources.search_engines.%s.search_engine as search_engine" % ( self.settings[ "search_engine" ], )
        return search_engine.SearchEngine()
                                
    def _get_settings( self ):
        self.settings = {}
        self.settings[ "thumbs_path" ]     =  THUMBS_PATH
        
        try: 
            self.settings[ "search_engine" ]   =  __settings__.getSetting( int(sys.argv[1]),"search_engine" )
        except: 
            self.settings[ "search_engine" ]   =  __settings__.getSetting( "search_engine" )
        
        if (not os.path.isdir(os.path.dirname(self.settings[ "thumbs_path" ]))):
            os.makedirs(os.path.dirname(self.settings[ "thumbs_path" ]));

    def _get_local_thumb( self, filename ):
        exts = ['png', 'jpg', 'gif', 'bmp']
        for ext in exts:
            #try with chnaged extension
            thumb = filename[:-len(os.path.splitext(filename)[-1])] + "." + ext
            if (os.path.isfile(thumb)):
                return thumb
            #also try with original extension
            thumb = filename + "." + ext
            if (os.path.isfile(thumb)):
                return thumb

    def _find_all_roms( self ):
        #get user input to search for
        keyboard = xbmc.Keyboard("", __language__( 30024 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            search = keyboard.getText()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self._path, search, SEARCH_ALL_COMMAND))

    def _find_add_all_roms( self, search ):
        #sorted by name
        if (len(self.launchers) > 0):
            rl = {}
            for key in sorted(self.launchers.iterkeys()):
                launcherName = self.launchers[key]["name"]
                selectedLauncher = self.launchers[launcherName]
                roms = selectedLauncher["roms"]
                text = search.lower();
                print "Launcher: %s : searching for %s " % (launcherName, text)
                if (len(roms) > 0) :
                    #go through rom list and search for user input
                    for keyr in sorted(roms.iterkeys()):
                        romname = roms[keyr]["name"].lower()
                        if (not romname.find(text) == -1):
                            rl[keyr] = roms[keyr]
                            rl[keyr]["launcherName"] = launcherName
                            print roms[keyr]["filename"]
        #print the list sorted
        print "Launcher: (ALL) : search found %d roms" % (len(rl))
        for key in sorted(rl.iterkeys()):
            self._add_rom(rl[key]["launcherName"], rl[key]["name"], rl[key]["filename"], rl[key]["thumb"], len(rl))
            print "Launcher: %s : add %s" % (rl[key]["launcherName"], rl[key]["name"])
        
        xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )

#        #sorted by launcher
#        if (len(self.launchers) > 0):
#            i = 0
#            for key in sorted(self.launchers.iterkeys()):
#                i += 1
#                self._find_add_roms(self.launchers[key]["name"], search, (len(self.launchers) == i))

    def _find_roms( self, launcherName ):
        #get user input to search for
        keyboard = xbmc.Keyboard("", __language__( 30024 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            search = keyboard.getText()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s/%s)" % (self._path, launcherName, search, SEARCH_COMMAND))

    def _find_add_roms ( self, launcherName, search, lastone=True ):
        if (self.launchers.has_key(launcherName)):
            selectedLauncher = self.launchers[launcherName]
            roms = selectedLauncher["roms"]
            text = search.lower();
            print "Launcher: %s : searching for %s " % (launcherName, text)
            if (len(roms) > 0) :
                #go through rom list and search for user input
                for key in sorted(roms.iterkeys()):
                    romname = roms[key]["name"].lower()
                    if (not romname.find(text) == -1):
                        self._add_rom(launcherName, roms[key]["name"], roms[key]["filename"], roms[key]["thumb"], len(roms))

            if (lastone):
                xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True
        else:
            return False
