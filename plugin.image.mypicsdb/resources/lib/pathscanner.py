#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

import os, urllib, re
import xbmc, xbmcvfs
import common
import json

class Scanner(object):

    def walk(self, path, recursive = False, types = None):
        filenames = []
        dirnames  = []
        files_to_return = []
        dirs_to_return = []

        if type(path).__name__=='unicode':
            path = path.encode('utf-8')
            
        if path.startswith('multipath://'):
            common.log("Scanner.walk", 'multipath "%s"'%path)
            dirs = path[12:-1].split('/')
            for item in dirs:
                dirnames1, filenames1 = self._walk(urllib.unquote_plus(item), recursive, types)

                for dirname in dirnames1:
                    dirnames.append(dirname)
                for filename in filenames1:
                    filenames.append(filename)               
               
        else:
            common.log("Scanner.walk", 'path "%s"'%path)
            dirnames, filenames = self._walk(path, recursive, types)

        # Make sure everything is a unicode
        for filename in filenames:
            files_to_return.append(common.smart_unicode(filename))
        for dirname in dirnames:
            dirs_to_return.append(common.smart_unicode(dirname))

        return dirs_to_return, files_to_return


    def _walk(self, path, recursive, types):
        filenames = []
        dirnames   = []
        files     = []

        path = xbmc.translatePath(path)
        common.log("Scanner._walk",'"%s"'%path)
        #if xbmcvfs.exists(xbmc.translatePath(path)) or re.match(r"[a-zA-Z]:\\", path) is not None:
        subdirs, files = self._listdir(path)
        for subdir in subdirs:
            dirnames.append(os.path.join(path, subdir))

        for filename in files:
            if types is not None:
                if os.path.splitext(filename)[1].upper() in types or os.path.splitext(filename)[1].lower() in types :
                    filenames.append(os.path.join(path, filename))
                else:
                    common.log("Scanner:_walk", 'Found file "%s" is excluded'%os.path.join(path, filename))
            else:              
                filenames.append(os.path.join(path, filename))


        if recursive:
            for item in subdirs:
                dirnames1, filenames1 = self._walk(os.path.join(path, item), recursive, types)
                for item in dirnames1:
                    dirnames.append(item)
                for item in filenames1:
                    filenames.append(item)
        
        return dirnames, filenames


    def getname(self, filename):
        filename = common.smart_unicode(filename)
        return os.path.basename(filename)

    def delete(self, filename):
        xbmcvfs.delete(filename)
        
    def getlocalfile(self, filename):
        
        filename = common.smart_unicode(filename)
        
        # Windows NEEDS unicode but OpenElec utf-8
        try:
            exists = os.path.exists(filename)
        except:
            exists = os.path.exists(common.smart_utf8(filename))
        if exists:
            return filename, False
        else:
            tempdir     = xbmc.translatePath('special://temp').decode('utf-8')
            basefilename    = self.getname(filename)
            destination = os.path.join(tempdir, basefilename)
            xbmcvfs.copy(filename, destination)

            return common.smart_unicode(destination), True

            
    def _listdir(self, path):

        try:
            return xbmcvfs.listdir(path)
        except:
            file_list = []
            dir_list  = []
            json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } } , "id" : 1 }' % common.smart_utf8(path.replace('\\', '\\\\')))
            jsonobject = json.loads(json_response)

            try:
                if jsonobject['result']['files']:

                    for item in jsonobject['result']['files']:

                        filename = common.smart_utf8(item['label'])
                        if item['filetype'] == 'directory':
                            dir_list.append(filename)
                        else:
                            file_list.append(filename)
                            
            except Exception,msg:
                common.log("Scanner.listdir", 'Path "%s"'%path, xbmc.LOGERROR )
                common.log("Scanner.listdir", "%s - %s"%(Exception,msg), xbmc.LOGERROR )
                
            return dir_list, file_list
