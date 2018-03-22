# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Zip Tools
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import base64, re, urllib, string, sys, zipfile, os, os.path
import xbmc
import plugintools

class ziptools:

    def extract(self, file, dir):
        plugintools.log("file=%s" % file)
        plugintools.log("dir=%s" % dir)
        
        if not dir.endswith(':') and not os.path.exists(dir):
            os.mkdir(dir)

        zf = zipfile.ZipFile(file)
        self._createstructure(file, dir)
        num_files = len(zf.namelist())

        for name in zf.namelist():
            plugintools.log("name=%s" % name)
            if not name.endswith('/'):
                plugintools.log("no es un directorio")
                try:
                    (path,filename) = os.path.split(os.path.join(dir, name))
                    plugintools.log("path=%s" % path)
                    plugintools.log("name=%s" % name)
                    os.makedirs( path )
                except:
                    pass
                outfilename = os.path.join(dir, name)
                plugintools.log("outfilename=%s" % outfilename)
                try:
                    outfile = open(outfilename, 'wb')
                    outfile.write(zf.read(name))
                except:
                    plugintools.log("Error en fichero "+name)

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def create_necessary_paths(filename):
        try:
            (path,name) = os.path.split(filename)
            os.makedirs( path)
        except:
            pass

    def _makedirs(self, directories, basedir):
        for dir in directories:
            curdir = os.path.join(basedir, dir)
            if not os.path.exists(curdir):
                os.mkdir(curdir)

    def _listdirs(self, file):
        zf = zipfile.ZipFile(file)
        dirs = []
        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name)

        dirs.sort()
        return dirs
