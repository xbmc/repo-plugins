import xbmc, xbmcgui, xbmcplugin, xbmcaddon, sys, urllib2, time, threading, urlparse, os, urllib, re, zipfile
from xml.dom import Node, minidom
from random import randint

global mode
global GetURL
global IP
global WebPort
global StreamPort
global Password
global VB
global VS
global AB
global AC
global xml
global SID
global PICON



Settings = xbmcaddon.Addon('plugin.video.enigmatv')

picon_dir = unicode(os.path.join(xbmc.translatePath(Settings.getAddonInfo('profile')), 'picons'),'utf-8')
if not os.path.isdir(picon_dir):

   os.makedirs(picon_dir)
profile_dir = unicode(os.path.join(xbmc.translatePath(Settings.getAddonInfo('path')), ''),'utf-8')
if not os.path.isdir(profile_dir):

   os.makedirs(profile_dir)

PICONFile = os.path.join(picon_dir, 'picons.zip')

IP = str(Settings.getSetting('IPServer'))
WebPort = str(Settings.getSetting('WebPort'))
StreamPort = str(Settings.getSetting('StreamPort'))
Password = str(Settings.getSetting('Password'))

language = Settings.getLocalizedString

Error10 = str(language(30009).encode('utf-8'))
Error11 = str(language(30010).encode('utf-8'))
Error12 = str(language(30011).encode('utf-8'))
Error13 = str(language(30012).encode('utf-8'))

Error20 = str(language(30013).encode('utf-8'))
Error21 = str(language(30014).encode('utf-8'))

Error30 = str(language(30015).encode('utf-8'))
Error31 = str(language(30016).encode('utf-8'))

Error40 = str(language(30017).encode('utf-8'))
Error41 = str(language(30018).encode('utf-8'))

GetURL = 'http://'+IP+':'+WebPort+'/CMD.php?FNC=GETCHANNELS&PASSWORD='+Password
GetPiconURL = 'http://'+IP+':'+WebPort+'/picons/picons.zip'


mode = 'init'
PNames = []
PIDs = []
CNames = []
CEPGs = []
CIDs = []
PCIDs = []

OK = True

def managePicons():
  try:
        print "deleting picons started"
        for the_file in os.listdir(picon_dir):
          file_path = os.path.join(picon_dir, the_file)
          try:
            if os.path.isfile(file_path):
              os.unlink(file_path)
          except Exception, e:
            print e

        try:
            from sqlite3 import dbapi2 as sqlite
            print "Loading sqlite3 as DB engine"
        except:
            from pysqlite2 import dbapi2 as sqlite
            print "Loading pysqlite2 as DB engine"

        DB = unicode(os.path.join(xbmc.translatePath("special://database"), 'Textures13.db'), "utf-8")
        db = sqlite.connect(DB)
        deletepiconsentries = db.execute("DELETE FROM texture WHERE url LIKE '"+picon_dir+"%';")
        deltedefaultpiconentries = db.execute("DELETE FROM texture WHERE url LIKE '"+profile_dir+"%';")
        db.commit();
        db.close();

        xbmc.executebuiltin('XBMC.Container.Update(path,replace)')
        xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
        xbmc.executebuiltin("XBMC.RunAddon(plugin.video.enigmatv)")
        restartdialog = xbmcgui.Dialog()
        restartdialog.ok("Enigma-TV", str(language(30200).encode('utf-8')))

  except:
      print 'Error managing the picon data'
managePicons()