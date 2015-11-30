"""
    DB access for Photo App library
"""

__author__ = "Claude Marksteiner <PhotoApp.KodiPlugin@stonebug.com>"
__credits__ = ""
__url__ = ""


try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os
import time
import locale

def smart_unicode(s):
    """credit : sfaxman"""
    if not s:
	return ''
    try:
	if not isinstance(s, basestring):
	    if hasattr(s, '__unicode__'):
		s = unicode(s)
	    else:
		s = unicode(str(s), 'UTF-8')
	elif not isinstance(s, unicode):
	    s = unicode(s, 'UTF-8')
    except:
	if not isinstance(s, basestring):
	    if hasattr(s, '__unicode__'):
		s = unicode(s)
	    else:
		s = unicode(str(s), 'ISO-8859-1')
	elif not isinstance(s, unicode):
	    s = unicode(s, 'ISO-8859-1')
    return s

def smart_utf8(s):
    return smart_unicode(s).encode('utf-8')

class PhotoAppDB:
    def __init__(self, dbfile):
	self.placeList = {}
	try:
	    print "photoapp.db: Opening database: %s" % (dbfile)
	    self.dbFile = os.path.basename(dbfile)
	    self.dbPath = os.path.dirname(dbfile)
	    self.dbconn = sqlite.connect(dbfile)
	except Exception, e:
	    print "photoapp.db: __init__: " + smart_utf8(e)
	    raise e

    def __del__(self):
	try:
	    self.CloseDB()
	except:
	    pass

    def CloseDB(self):
	self.dbconn.commit()
	self.dbconn.close()

    def Commit(self):
	try:
	    self.dbconn.commit()
	except Exception, e:
	    print "iphoto.db: Commit: " + smart_utf8(e)
	    raise e

    def GetMomentList(self, year, month):
	print "photoapp.db: Retrieving list of moments"
	moment_list = []
	cur = self.dbconn.cursor()
	try:
	    #SELECT strftime('%Y', startDate, 'unixepoch', 'localtime'), startDate FROM `RKMoment` WHERE  strftime('%Y', startDate, 'unixepoch', 'localtime') = '1974'
	    if year is None:
	        cur.execute("""SELECT strftime('%Y', startDate, 'unixepoch', 'localtime')+31, 0 
	                       FROM RKMoment 
	                       GROUP BY strftime('%Y', startDate, 'unixepoch', 'localtime')""")
	    elif month is None:
	        cur.execute("""SELECT strftime('%m', startDate, 'unixepoch', 'localtime'), 0 
	                       FROM RKMoment 
	                       WHERE strftime('%Y', startDate, 'unixepoch', 'localtime') = ?
	                       GROUP BY strftime('%Y-%m', startDate, 'unixepoch', 'localtime')""", ('%s' % (int(year[0])-31),))
	    else:
	        cur.execute("""SELECT strftime('%d', startDate, 'unixepoch', 'localtime'), uuid 
	                       FROM RKMoment 
	                       WHERE strftime('%Y-%m', startDate, 'unixepoch', 'localtime') = ?
	                       ORDER BY startDate""", ('%s-%s' % (int(year[0])-31, month[0]),))
	    for row in cur:
		moment_list.append(row)
	except Exception, e:
	    print "photoapp.db: GetMomentList: " + smart_utf8(e)
	    pass
	cur.close()
	return moment_list

    def GetFolderList(self, folderUuid):
	print "photoapp.db: Retrieving list of folders"
	folder_list = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("""SELECT name, uuid FROM RKFolder 
	                   WHERE isHidden = 0 AND isInTrash = 0 AND parentFolderUuid = ? 
	                   ORDER BY name ASC""", (folderUuid,))
	    for row in cur:
		folder_list.append(row)
	except Exception, e:
	    print "photoapp.db: GetFolderList: " + smart_utf8(e)
	    pass
	cur.close()
	return folder_list

    def GetAlbumList(self, folderUuid):
	print "photoapp.db: Retrieving list of albums"
	album_list = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("""SELECT name, uuid FROM RKAlbum 
	                   WHERE isHidden = 0 AND isInTrash = 0 AND customSortAvailable = 1 AND folderUuid = ? 
	                   ORDER BY name ASC""", (folderUuid,))
	    for row in cur:
		album_list.append(row)
	except Exception, e:
	    print "photoapp.db: GetAlbumList: " + smart_utf8(e)
	    pass
	cur.close()
	return album_list

    def GetPictureList(self, uuid, action):
	print "photoapp.db: Retrieving list of pictures"
	picture_list = []
	cur = self.dbconn.cursor()
	try:
	    if action == 'moments':
	        cur.execute("""SELECT v.filename, m.imagePath 
	                       FROM RKCustomSortOrder o, RKVersion v, RKMaster m 
	                       WHERE o.objectUuid = v.Uuid AND v.masterUuid = m.uuid 
	                       AND v.momentUuid = ? 
	                       ORDER BY o.orderNumber ASC""", (uuid,))
	    else:
	        cur.execute("""SELECT v.filename, m.imagePath 
	                       FROM RKCustomSortOrder o, RKVersion v, RKMaster m 
	                       WHERE o.objectUuid = v.Uuid AND v.masterUuid = m.uuid 
	                       AND o.containerUuid = ? 
	                       ORDER BY o.orderNumber ASC""", (uuid,))
	    for row in cur:
		picture_list.append(row)
	except Exception, e:
	    print "photoapp.db: GetPictureList: " + smart_utf8(e)
	    pass
	cur.close()
	return picture_list

