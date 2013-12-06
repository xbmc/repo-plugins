"""
    Parser for iPhoto's AlbumData.xml and Aperture's ApertureData.xml
"""

__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import traceback
import xml.parsers.expat

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os
import time
import locale

try:
    from resources.lib.geo import *
except:
    from geo import *


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

class IPhotoDB:
    def __init__(self, dbfile):
	self.placeList = {}
	try:
	    print "iphoto.db: Opening database: %s" % (dbfile)
	    self.dbFile = os.path.basename(dbfile)
	    self.dbPath = os.path.dirname(dbfile)
	    self.dbconn = sqlite.connect(dbfile)
	except Exception, e:
	    print "iphoto.db: __init__: " + smart_utf8(e)
	    raise e

    def __del__(self):
	try:
	    self.CloseDB()
	except:
	    pass

    def InitDB(self):
	self.dbconn.execute("PRAGMA synchronous = OFF")
	self.dbconn.execute("PRAGMA default_synchronous = OFF")
	self.dbconn.execute("PRAGMA journal_mode = OFF")
	self.dbconn.execute("PRAGMA temp_store = MEMORY")
	self.dbconn.execute("PRAGMA encoding = \"UTF-8\"")

	print "iphoto.db: Initializing database"

	try:
	    # config table
	    self.dbconn.execute("""
	    CREATE TABLE config (
	       key varchar primary key,
	       value varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: config"

	try:
	    # media table
	    self.dbconn.execute("""
	    CREATE TABLE media (
	       id varchar primary key,
	       mediatypeid integer,
	       rollid integer,
	       caption varchar,
	       guid varchar,
	       aspectratio number,
	       latitude number,
	       longitude number,
	       rating integer,
	       mediadate integer,
	       mediasize integer,
	       mediapath varchar,
	       thumbpath varchar,
	       originalpath varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: media"

	try:
	    # mediatypes table
	    self.dbconn.execute("""
	    CREATE TABLE mediatypes (
	       id integer primary key,
	       name varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: mediatypes"

	try:
	    # rolls (events) table
	    self.dbconn.execute("""
	    CREATE TABLE rolls (
	       id integer primary key,
	       name varchar,
	       keyphotoid varchar,
	       rolldate integer,
	       photocount integer
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: rolls"

	try:
	    # rollmedia table
	    self.dbconn.execute("""
	    CREATE TABLE rollmedia (
	       rollid integer,
	       mediaid varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: rollmedia"

	try:
	    # albums table
	    self.dbconn.execute("""
	    CREATE TABLE albums (
	       id integer primary key,
	       name varchar,
	       master boolean,
	       uuid varchar,
	       photocount integer
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: albums"

	try:
	    # albummedia table
	    self.dbconn.execute("""
	    CREATE TABLE albummedia (
	       albumid integer,
	       mediaid varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: albummedia"

	try:
	    # faces table
	    self.dbconn.execute("""
	    CREATE TABLE faces (
	       id integer primary key,
	       name varchar,
	       thumbpath varchar,
	       keyphotoid varchar,
	       keyphotoidx integer,
	       photocount integer,
	       faceorder integer
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: faces"

	try:
	    # facesmedia table
	    self.dbconn.execute("""
	    CREATE TABLE facesmedia (
	       faceid integer,
	       mediaid varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: facesmedia"

	try:
	    # places table
	    self.dbconn.execute("""
	    CREATE TABLE places (
	       id integer primary key,
	       latlon varchar,
	       address varchar,
	       thumbpath varchar,
	       fanartpath varchar,
	       photocount integer
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: places"

	try:
	    # placesmedia table
	    self.dbconn.execute("""
	    CREATE TABLE placesmedia (
	       placeid integer,
	       mediaid varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: placesmedia"

	try:
	    # keywords table
	    self.dbconn.execute("""
	    CREATE TABLE keywords (
	       id integer primary key,
	       name varchar,
	       photocount integer
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: keywords"

	try:
	    # keywordmedia table
	    self.dbconn.execute("""
	    CREATE TABLE keywordmedia (
	       keywordid integer,
	       mediaid varchar
	    )""")
	except sqlite.OperationalError, e:
	    pass
	except Exception, e:
	    print "iphoto.db: InitDB: " + smart_utf8(e)
	    raise e
	else:
	    print "iphoto.db: InitDB: Created table: keywordmedia"

	self.Commit()

    def ResetDB(self):
	print "iphoto.db: Resetting database"
	for table in ['media', 'mediatypes', 'rolls', 'rollmedia', 'albums', 'albummedia', 'faces', 'facesmedia', 'places', 'placesmedia', 'keywords', 'keywordmedia']:
	    try:
		self.dbconn.execute("DROP TABLE %s" % table)
	    except sqlite.OperationalError:
		pass
	    except Exception, e:
		print "iphoto.db: ResetDB: " + smart_utf8(e)
		raise e
	    else:
		print "iphoto.db: ResetDB: Dropped table: " + table
	self.Commit()

    def CloseDB(self):
	self.dbconn.commit()
	self.dbconn.close()

    def Commit(self):
	try:
	    self.dbconn.commit()
	except Exception, e:
	    print "iphoto.db: Commit: " + smart_utf8(e)
	    raise e

    def GetConfig(self, key):
	rv = None
	cur = self.dbconn.cursor()
	try:
	    cur.execute("""SELECT value FROM config WHERE key = ? LIMIT 1""", (key,))
	    row = cur.fetchone()
	    if (row):
		rv = row[0]
	except:
	    pass
	cur.close()
	return rv

    def SetConfig(self, key, value):
	if (self.GetConfig(key) is None):
	    self.dbconn.execute("""INSERT INTO config (key, value) VALUES (?, ?)""", (key, value))
	else:
	    self.dbconn.execute("""UPDATE config SET value = ?  WHERE key = ?""", (value, key))
	self.Commit()

    def GetLibrarySource(self):
	src = self.GetConfig('source')
	return src

    def GetLibraryVersion(self):
	verstr = self.GetConfig('version')
	if (verstr is None):
	    ver = 0.0
	else:
	    ver = float('.'.join(verstr.split('.')[:2]))
	return ver

    def GetTableId(self, table, value, column='name', autoadd=False, autoclean=True):
	rv = None
	cur = self.dbconn.cursor()
	try:
	    if (autoclean and not value):
		value = "Unknown"

	    # query db for column with specified name
	    cur.execute("SELECT id FROM %s WHERE %s = ?" % (table, column),
			(value,))
	    row = cur.fetchone()

	    if (not row and autoadd and value and len(value) > 0):
		nextid = cur.execute("SELECT MAX(id) FROM %s" % table).fetchone()[0]
		if not nextid:
		    nextid = 1
		else:
		    nextid += 1
		cur.execute("INSERT INTO %s (id, %s) VALUES (?, ?)" % (table, column),
			    (nextid, value))
		rv = nextid # new id
	    else:
		rv = row[0] # existing id
	except Exception, e:
	    print "iphoto.db: GetTableId: " + smart_utf8(e)
	    raise e
	cur.close()
	return rv

    def GetMediaTypeId(self, mediatype, autoadd=False):
	return self.GetTableId('mediatypes', mediatype, 'name', autoadd)

    def GetAlbums(self):
	print "iphoto.db: Retrieving list of Albums"
	albums = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("SELECT id, name, photocount FROM albums")
	    for tuple in cur:
		albums.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetAlbums: " + smart_utf8(e)
	    pass
	cur.close()
	return albums

    def GetMediaInAlbum(self, albumid, sort_col="NULL"):
	print "iphoto.db: Retrieving media from Album ID %s" % (smart_utf8(albumid))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM albummedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.albumid = ? ORDER BY %s ASC""" % (sort_col), (albumid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaInAlbum: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def GetRolls(self):
	print "iphoto.db: Retrieving list of Events"
	rolls = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("""SELECT R.id, R.name, M.thumbpath, R.rolldate, R.photocount 
			 FROM rolls R LEFT JOIN media M ON R.keyphotoid = M.id WHERE R.keyphotoid != 0""")
	    for tuple in cur:
		rolls.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetRolls: " + smart_utf8(e)
	    pass
	cur.close()
	return rolls

    def GetMediaInRoll(self, rollid, sort_col="NULL"):
	print "iphoto.db: Retrieving media from Event ID %s" % (smart_utf8(rollid))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM media M WHERE M.rollid = ? ORDER BY %s ASC""" % (sort_col), (rollid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaInRoll: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def GetFaces(self):
	print "iphoto.db: Retrieving list of Faces"
	faces = []
	cur = self.dbconn.cursor()
	try:
	    if (self.GetLibrarySource() == "iPhoto" and self.GetLibraryVersion() < 9.4):
		idtype = "M.id"
	    else:
		idtype = "M.guid"

	    cur.execute("""SELECT F.id, F.name, F.thumbpath, F.photocount
			 FROM faces F LEFT JOIN media M ON F.keyphotoid = %s
			 ORDER BY F.faceorder""" % (idtype))

	    for tuple in cur:
		faces.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetFaces: " + smart_utf8(e)
	    pass
	cur.close()
	return faces

    def GetMediaWithFace(self, faceid, sort_col="NULL"):
	print "iphoto.db: Retrieving media with Face ID %s" % (smart_utf8(faceid))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM facesmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.faceid = ? ORDER BY %s ASC""" % (sort_col), (faceid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaWithFace: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def GetPlaces(self):
	print "iphoto.db: Retrieving list of Places"
	places = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("SELECT id, latlon, address, thumbpath, fanartpath, photocount FROM places")
	    for tuple in cur:
		places.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetPlaces: " + smart_utf8(e)
	    pass
	cur.close()
	return places

    def GetMediaWithPlace(self, placeid, sort_col="NULL"):
	print "iphoto.db: Retrieving media with Place ID %s" % (smart_utf8(placeid))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM placesmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.placeid = ? ORDER BY %s ASC""" % (sort_col), (placeid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaWithPlace: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def GetKeywords(self):
	print "iphoto.db: Retrieving list of Keywords"
	keywords = []
	cur = self.dbconn.cursor()
	try:
	    cur.execute("SELECT id, name, photocount FROM keywords ORDER BY name")
	    for tuple in cur:
		keywords.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetKeywords: " + smart_utf8(e)
	    pass
	cur.close()
	return keywords

    def GetMediaWithKeyword(self, keywordid, sort_col="NULL"):
	print "iphoto.db: Retrieving media with Keyword ID %s" % (smart_utf8(keywordid))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM keywordmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.keywordid = ? ORDER BY %s ASC""" % (sort_col), (keywordid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaWithKeyword: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def GetMediaWithRating(self, rating, sort_col="NULL"):
	print "iphoto.db: Retrieving media with Rating %s" % (smart_utf8(rating))
	media = []
	cur = self.dbconn.cursor()
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM media M WHERE M.rating = ? ORDER BY %s ASC""" % (sort_col), (rating,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print "iphoto.db: GetMediaWithRating: " + smart_utf8(e)
	    pass
	cur.close()
	return media

    def AddAlbumNew(self, album, album_ign):
	#print "AddAlbumNew()", album

	try:
	    albumid = int(album['AlbumId'])
	    albumuuid = album['uuid']
	    albumtype = album['Album Type']
	except:
	    return

	try:
	    photocount = album['PhotoCount']
	except:
	    photocount = 0
	    pass

	# weed out ignored albums
	if (photocount == 0 or albumtype in album_ign or albumuuid in album_ign):
	    try:
		print "iphoto.db: Ignoring album '%s' of type '%s'" % (album['AlbumName'], albumtype)
	    except:
		pass
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO albums (id, name, master, uuid, photocount)
	    VALUES (?, ?, ?, ?, ?)""",
				(albumid,
				 album['AlbumName'],
				 album.has_key('Master'),
				 albumuuid,
				 photocount))
	    for media in album['medialist']:
		self.dbconn.execute("""
		INSERT INTO albummedia (albumid, mediaid)
		VALUES (?, ?)""", (albumid, media))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e

    def AddRollNew(self, roll):
	#print "AddRollNew()", roll

	src = self.GetLibrarySource()

	try:
	    if (src == "iPhoto"):
		rollid = int(roll['RollID'])
		rollname = roll['RollName']
		rolldate = int(float(roll['RollDateAsTimerInterval']))
	    else:
		rollid = int(roll['AlbumId'])
		rollname = roll['ProjectName']
		rolldate = int(float(roll['ProjectEarliestDateAsTimerInterval']))
	except:
	    return

	try:
	    if (src == "iPhoto"):
		photocount = roll['PhotoCount']
	    else:
		photocount = roll['NumImages']
	except:
	    photocount = 0
	    pass

	if (photocount == 0):
	    try:
		print "iphoto.db: Ignoring empty Event '%s'" % (rollname)
	    except:
		pass
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO rolls (id, name, keyphotoid, rolldate, photocount)
	    VALUES (?, ?, ?, ?, ?)""",
				(rollid,
				 rollname,
				 roll['KeyPhotoKey'],
				 rolldate,
				 photocount))
	    for media in roll['medialist']:
		self.dbconn.execute("""
		INSERT INTO rollmedia (rollid, mediaid)
		VALUES (?, ?)""", (rollid, media))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e

    def AddFaceNew(self, face):
	#print "AddFaceNew()", face

	try:
	    faceid = int(face['key'])
	    facekey = face['key image']
	    faceidx = face['key image face index']
	except:
	    return

	try:
	    photocount = face['PhotoCount']
	except:
	    photocount = 0
	    pass

	if (photocount == 0):
	    try:
		print "iphoto.db: Ignoring empty Face '%s'" % (face['name'])
	    except:
		pass
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO faces (id, name, keyphotoid, keyphotoidx, photocount, faceorder)
	    VALUES (?, ?, ?, ?, ?, ?)""",
				(faceid,
				 face['name'],
				 facekey,
				 faceidx,
				 photocount,
				 face['Order']))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e

    def AddKeywordNew(self, keyword):
	#print "AddKeywordNew()", keyword

	try:
	    keywordid = keyword.keys()[0]
	    kword = keyword[keywordid]
	except:
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO keywords (id, name)
	    VALUES (?, ?)""",
				(int(keywordid),
				 kword))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e

    def AddMediaNew(self, media, archivePath, libraryPath, mastersPath, mastersRealPath, enablePlaces, mapAspect, updateProgress):
	#print "AddMediaNew()", media

	try:
	    mediaid = media['MediaID']
	    if (not mediaid):
		return
	except:
	    return

	# rewrite paths to image files based on configured path.
	# if the iPhoto library is mounted as a share, the paths in
	# AlbumData.xml probably won't be right.
	if (archivePath and libraryPath):
	    thumbpath = media['ThumbPath'].replace(archivePath, libraryPath)
	    if (mastersPath and mastersRealPath):
		imagepath = media['ImagePath'].replace(mastersPath, mastersRealPath)
		originalpath = media['OriginalPath'].replace(mastersPath, mastersRealPath)
		# second substitition here because unedited images reference the master,
		# but edited images reference the preview.
		imagepath = imagepath.replace(archivePath, libraryPath)
		originalpath = originalpath.replace(archivePath, libraryPath)
	    else:
		imagepath = media['ImagePath'].replace(archivePath, libraryPath)
		originalpath = media['OriginalPath'].replace(archivePath, libraryPath)
	else:
	    imagepath = media['ImagePath']
	    thumbpath = media['ThumbPath']
	    originalpath = media['OriginalPath']

	filepath = imagepath
	if (not filepath):
	    filepath = originalpath

	try:
	    mediasize = os.path.getsize(filepath)
	except:
	    mediasize = 0
	    pass

	cur = self.dbconn.cursor()
	try:
	    if (self.GetLibrarySource() == "iPhoto" and self.GetLibraryVersion() < 9.4):
		cmpkey = 'MediaID'
	    else:
		cmpkey = 'GUID'

	    faces = []
	    cur.execute("""SELECT id, keyphotoid, keyphotoidx FROM faces""")
	    for tuple in cur:
		faces.append(tuple)

	    for faceid in media['facelist']:
		cur.execute("""
		INSERT INTO facesmedia (faceid, mediaid)
		VALUES (?, ?)""", (faceid, mediaid))

		for (fid, fkey, fkeyidx) in faces:
		    if (fkey == media[cmpkey]):
			fthumb = os.path.splitext(thumbpath)[0] + "_face%s.jpg" % (fkeyidx)
			self.dbconn.execute("""
			UPDATE faces SET thumbpath = ?
			WHERE id = ?""", (fthumb, fid))

	    cur.execute("""
	    INSERT INTO media (id, mediatypeid, rollid, caption, guid, aspectratio, latitude, longitude, rating, mediadate, mediasize, mediapath, thumbpath, originalpath)
	    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
				(mediaid,
				 self.GetMediaTypeId(media['MediaType'], True),
				 media['Roll'],
				 media['Caption'],
				 media['GUID'],
				 media['Aspect Ratio'],
				 media['latitude'],
				 media['longitude'],
				 media['Rating'],
				 int(float(media['DateAsTimerInterval'])),
				 mediasize,
				 imagepath,
				 thumbpath,
				 originalpath))

	    if (enablePlaces == True):
		# convert lat/lon pair to an address
		try:
		    lat = float(media['latitude'])
		    lon = float(media['longitude'])
		    if (lat == 0.0 and lon == 0.0):
			# force exception for ungeotagged photos
			del lat, lon
		    lat = smart_utf8(lat)
		    lon = smart_utf8(lon)
		    latlon = lat + "+" + lon
		    try:
			addr = None
			placeid = None
			for i in self.placeList:
			    if (latlon in self.placeList[i]):
				addr = self.placeList[i][0]
				placeid = i
				break
			if (addr is None):
			    updateProgress("Geocode: %s %s" % (lat, lon))
			    addr = geocode("%s,%s" % (lat, lon))[0]
			    updateProgress()

			    for i in self.placeList:
				if (self.placeList[i][0] == addr):
				    placeid = i
				    break
			    if (placeid is None):
				placeid = len(self.placeList)
				self.placeList[placeid] = []
				#print "new placeid %d for addr '%s'" % (placeid, addr)
		    except ParseCanceled:
			raise
		    except Exception, e:
			print "iphoto.db: AddMediaNew: geocode: " + smart_utf8(e)
			raise e
		except:
		    #print "No location information for photo id %d" % (mediaid)
		    updateProgress("Geocode: Error")
		    pass
		else:
		    if (addr not in self.placeList[placeid]):
			# download thumbnail and fanart maps for Place
			fanartpath = ""
			thumbpath = ""
			if (mapAspect != 0.0):
			    updateProgress("Map Image: %s %s" % (lat, lon))
			    try:
				map_size_x = MAP_IMAGE_X_MAX
				map_size_y = int(float(map_size_x) / mapAspect)
				map = staticmap(self.dbPath, latlon, False, xsize=map_size_x, ysize=map_size_y)
				fanartpath = map.fetch("map_", "_%dx%d" % (map_size_x, map_size_y))
				map.set_xsize(256)
				map.set_ysize(256)
				map.set_type("roadmap")
				map.toggle_marker()
				map.zoom("", 14)
				thumbpath = map.fetch("map_", "_thumb")
			    except Exception, e:
				print "iphoto.db: AddMediaNew: map: " + smart_utf8(e)
				updateProgress("Map Image: Error downloading")
				pass
			    else:
				updateProgress()

			# add new Place
			self.placeList[placeid].append(addr)
			cur.execute("""
				    INSERT INTO places (id, latlon, address, thumbpath, fanartpath)
				    VALUES (?, ?, ?, ?, ?)""", (placeid, latlon, addr, thumbpath, fanartpath))

		    if (latlon not in self.placeList[placeid]):
			# existing Place, but add latlon to list for this address.
			# do this to prevent the script from hitting google more
			# than necessary.
			self.placeList[placeid].append(latlon)

		    cur.execute("""
				INSERT INTO placesmedia (placeid, mediaid)
				VALUES (?, ?)""", (placeid, mediaid))
		    cur.execute("""SELECT id, photocount
				FROM places
				WHERE id = ?""", (placeid,))
		    for tuple in cur:
			if (tuple[1]):
			    photocount = int(tuple[1]) + 1
			else:
			    photocount = 1
			self.dbconn.execute("""
					    UPDATE places SET photocount = ?
					    WHERE id = ?""", (photocount, placeid))

	    for keywordid in media['keywordlist']:
		cur.execute("""
			    INSERT INTO keywordmedia (keywordid, mediaid)
			    VALUES (?, ?)""", (keywordid, mediaid))
		cur.execute("""SELECT id, photocount
			    FROM keywords
			    WHERE id = ?""", (keywordid,))
		for tuple in cur:
		    if (tuple[1]):
			photocount = int(tuple[1]) + 1
		    else:
			photocount = 1
		    self.dbconn.execute("""
		    UPDATE keywords SET photocount = ?
		    WHERE id = ?""", (photocount, keywordid))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e
	cur.close()


class ParseCanceled(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)

class IPhotoParserState:
    def __init__(self):
	self.nphotos = 0
	self.nphotostotal = 0
	self.level = 0
	self.libversion = False
	self.inlibversion = 0
	self.archivepath = False
	self.inarchivepath = 0
	self.albums = False
	self.inalbum = 0
	self.rolls = False
	self.inroll = 0
	self.faces = False
	self.inface = 0
	self.keywords = False
	self.inkeyword = 0
	self.master = False
	self.inmaster = 0
	self.root = False
	self.key = False
	self.keyValue = ""
	self.value = ""
	self.valueType = ""

class IPhotoParser:
    def __init__(self, library_source="iPhoto", library_path="", xmlfile="", masters_path="", masters_real_path="",
		 album_ign=[], enable_places=False, map_aspect=0.0,
		 config_callback=None,
		 album_callback=None, roll_callback=None, face_callback=None, keyword_callback=None, photo_callback=None,
		 progress_callback=None):
	self.librarySource = library_source
	self.libraryVersion = "0.0.0"
	self.libraryPath = library_path
	self.xmlfile = xmlfile
	self.mastersPath = masters_path
	self.mastersRealPath = masters_real_path
	print "iphoto.parser: Library source is %s" % (self.librarySource)
	print "iphoto.parser: Reading '%s'" % (self.xmlfile)
	if (self.mastersPath and self.mastersRealPath):
	    try:
		print "iphoto.parser: Rewriting referenced masters path '%s'" % (smart_utf8(self.mastersPath))
		print "iphoto.parser: as '%s'" % (smart_utf8(self.mastersRealPath))
	    except:
		pass
	self.imagePath = ""
	self.parser = xml.parsers.expat.ParserCreate()
	self.parser.StartElementHandler = self.StartElement
	self.parser.EndElementHandler = self.EndElement
	self.parser.CharacterDataHandler = self.CharData
	self.state = IPhotoParserState()
	self.ele = ""
	self.currentPhoto = {}
	self.currentAlbum = {}
	self.currentRoll = {}
	self.currentFace = {}
	self.currentKeyword = {}
	self.photoList = []
	self.albumList = []
	self.rollList = []
	self.faceList = []
	self.keywordList = []
	self.albumIgn = album_ign
	self.enablePlaces = enable_places
	self.mapAspect = map_aspect
	self.ConfigCallback = config_callback
	self.AlbumCallback = album_callback
	self.RollCallback = roll_callback
	self.FaceCallback = face_callback
	self.KeywordCallback = keyword_callback
	self.PhotoCallback = photo_callback
	self.ProgressCallback = progress_callback
	self.lastdata = False
	self._reset_photo()
	self._reset_album()
	self._reset_roll()
	self._reset_face()
	self._reset_keyword()

    def _reset_photo(self):
	self.currentPhoto = {}
	for a in ['OriginalPath', 'Caption', 'ThumbPath', 'Rating', 'ImagePath',
		  'Roll', 'MediaType', 'GUID', 'DateAsTimerInterval']:
	    self.currentPhoto[a] = ""
	self.currentPhoto['Aspect Ratio'] = '0'
	self.currentPhoto['DateAsTimerInterval'] = '0'
	self.currentPhoto['latitude'] = '0'
	self.currentPhoto['longitude'] = '0'
	self.currentPhoto['facelist'] = []
	self.currentPhoto['keywordlist'] = []

    def _reset_album(self):
	self.currentAlbum = {}
	for a in ['uuid', 'master']:
	    self.currentAlbum[a] = ""
	for a in self.currentAlbum.keys():
	    self.currentAlbum[a] = ""
	self.currentAlbum['medialist'] = []

    def _reset_roll(self):
	self.currentRoll = {}
	for a in self.currentRoll.keys():
	    self.currentRoll[a] = ""
	self.currentRoll['PhotoCount'] = '0'
	self.currentRoll['NumImages'] = '0'
	self.currentRoll['medialist'] = []

    def _reset_face(self):
	self.currentFace = {}
	for a in self.currentFace.keys():
	    self.currentFace[a] = ""

    def _reset_keyword(self):
	self.currentKeyword = {}
	for a in self.currentKeyword.keys():
	    self.currentKeyword[a] = ""

    def updateProgress(self, altinfo=" "):
	if (not self.ProgressCallback):
	    return

	state = self.state
	ret = self.ProgressCallback(altinfo, state.nphotos, state.nphotostotal)
	if (ret is None):
	    raise ParseCanceled("Parse canceled by user")

    def commitAll(self):
	state = self.state

	state.nphotostotal = len(self.albumList) + len(self.rollList) + len(self.faceList) + len(self.keywordList) + len(self.photoList)

	try:
	    if (self.ConfigCallback):
		print "iphoto.parser: Writing configuration"
		self.ConfigCallback('source', self.librarySource)
		if (self.libraryVersion != "0.0.0"):
		    self.ConfigCallback('version', self.libraryVersion)
		try:
		    self.ConfigCallback('lastimport', smart_utf8(time.time()))
		except:
		    pass

	    if (self.AlbumCallback and len(self.albumList) > 0):
		print "iphoto.parser: Adding albums to database"
		for a in self.albumList:
		    self.AlbumCallback(a, self.albumIgn)
		    state.nphotos += 1
		    self.updateProgress()

	    if (self.RollCallback and len(self.rollList) > 0):
		print "iphoto.parser: Adding events to database"
		for a in self.rollList:
		    self.RollCallback(a)
		    state.nphotos += 1
		    self.updateProgress()

	    if (self.FaceCallback and len(self.faceList) > 0):
		print "iphoto.parser: Adding faces to database"
		for a in self.faceList:
		    self.FaceCallback(a)
		    state.nphotos += 1
		    self.updateProgress()

	    if (self.KeywordCallback and len(self.keywordList) > 0):
		print "iphoto.parser: Adding keywords to database"
		for a in self.keywordList:
		    self.KeywordCallback(a)
		    state.nphotos += 1
		    self.updateProgress()

	    if (self.PhotoCallback and len(self.photoList) > 0):
		print "iphoto.parser: Adding photos to database"
		for a in self.photoList:
		    self.PhotoCallback(a, self.imagePath, self.libraryPath, self.mastersPath, self.mastersRealPath, self.enablePlaces, self.mapAspect, self.updateProgress)
		    state.nphotos += 1
		    self.updateProgress()
	except ParseCanceled:
	    raise
	except Exception, e:
	    print "iphoto.parser: commitAll: " + smart_utf8(e)
	    raise e

    def Parse(self):
	try:
	    BLOCKSIZE = 8192
	    f = open(self.xmlfile, "r")
	    buf = f.read(BLOCKSIZE)
	    while buf:
		self.parser.Parse(buf, False)
		buf = f.read(BLOCKSIZE)
	    self.parser.Parse(buf, True)
	    f.close()
	except Exception, e:
	    print "iphoto.parser: Parse: " + smart_utf8(e)
	    print "iphoto.parser: Parse failed"
	    raise e

	try:
	    self.commitAll()
	except Exception, e:
	    print "iphoto.parser: Parse: " + smart_utf8(e)
	    print "iphoto.parser: Parse failed"
	    raise e

	print "iphoto.parser: Parse successful"

    def StartElement(self, name, attrs):
	state = self.state
	self.lastdata = False
	if (state.libversion):
	    state.inlibversion += 1
	    state.key = name
	elif (state.archivepath):
	    state.inarchivepath += 1
	    state.key = name
	elif (state.albums):
	    state.inalbum += 1
	    state.key = name
	elif (state.rolls):
	    state.inroll += 1
	    state.key = name
	elif (state.faces):
	    state.inface += 1
	    state.key = name
	elif (state.keywords):
	    state.inkeyword += 1
	    state.key = name
	elif (state.master):
	    state.inmaster += 1
	    state.key = name

	if (name == "key"):
	    state.key = True
	    #print "Got key type " + smart_utf8(name)
	else:
	    if (state.key):
		state.valueType = name
		#print "Got value type " + smart_utf8(name)
	    else:
		state.valueType = ""
		#print "Got empty value type"
	    state.key = False

	state.level += 1

    def EndElement(self, name):
	self.lastdata = False
	state = self.state

	# Application Version
	if (state.libversion):
	    if (not state.key):
		self.libraryVersion = state.value
		print "iphoto.parser: Detected %s Version %s" % (self.librarySource, self.libraryVersion)
		state.libversion = False
	    state.inlibversion -= 1

	# Archive Path
	elif (state.archivepath):
	    if (not state.key):
		self.imagePath = state.value
		state.archivepath = False
		if (self.imagePath != self.libraryPath):
		    try:
			print "iphoto.parser: Rewriting archive path '%s'" % (smart_utf8(self.imagePath))
			print "iphoto.parser: as '%s'" % (smart_utf8(self.libraryPath))
		    except:
			pass
	    state.inarchivepath -= 1

	# Albums
	elif (state.albums):
	    if (state.inalbum == 3 and self.currentAlbum.has_key('AlbumId')):
		self.currentAlbum['medialist'].append(state.value)
	    elif (state.inalbum == 2 and not state.key):
		#print "Mapping %s => %s" % ( smart_utf8(state.keyValue), smart_utf8(state.value))
		self.currentAlbum[state.keyValue] = state.value
	    state.inalbum -= 1
	    if (state.inalbum == 0 and self.currentAlbum.has_key('AlbumId')):
		# Finished reading album
		self.albumList.append(self.currentAlbum)
		self._reset_album()

	# Rolls
	elif (state.rolls):
	    if (state.inroll == 3 and (self.currentRoll.has_key('RollID') or self.currentRoll.has_key('AlbumId'))):
		self.currentRoll['medialist'].append(state.value)
	    elif (state.inroll == 2 and not state.key):
		#print "Mapping %s => %s" % ( smart_utf8(state.keyValue), smart_utf8(state.value))
		self.currentRoll[state.keyValue] = state.value
	    state.inroll -= 1
	    if (state.inroll == 0 and (self.currentRoll.has_key('RollID') or self.currentRoll.has_key('AlbumId'))):
		# Finished reading roll
		self.rollList.append(self.currentRoll)
		self._reset_roll()

	# Faces
	elif (state.faces):
	    if (state.inface == 2 and not state.key):
		#print "Mapping %s => %s" % ( smart_utf8(state.keyValue), smart_utf8(state.value))
		self.currentFace[state.keyValue] = state.value
	    state.inface -= 1
	    if (state.inface == 0 and not state.key):
		# Finished reading faces
		self.faceList.append(self.currentFace)
		self._reset_face()

	# Keywords
	elif (state.keywords):
	    if (state.inkeyword == 1 and not state.key):
		#print "Mapping %s => %s" % ( smart_utf8(state.keyValue), smart_utf8(state.value))
		self.currentKeyword[state.keyValue] = state.value
	    state.inkeyword -= 1
	    if (state.inkeyword == 0 and not state.key):
		# Finished reading keywords
		self.keywordList.append(self.currentKeyword)
		self._reset_keyword()

	# Master Image List
	elif (state.master):
	    if (state.inmaster == 1 and state.key):
		self.currentPhoto['MediaID'] = state.keyValue
		if (self.librarySource == "Aperture"):
		    self.currentPhoto['GUID'] = state.keyValue
	    elif (state.inmaster == 3 and not state.key and state.keyValue == "Keywords"):
		self.currentPhoto['keywordlist'].append(state.value)
	    elif (state.inmaster == 4 and not state.key and state.keyValue == "face key"):
		self.currentPhoto['facelist'].append(state.value)
	    elif (state.inmaster == 2 and not state.key):
		#print "Mapping %s => %s" % ( smart_utf8(state.keyValue), smart_utf8(state.value))
		self.currentPhoto[state.keyValue] = state.value
	    state.inmaster -= 1
	    if (state.inmaster == 0 and self.currentPhoto.has_key('ThumbPath') and self.currentPhoto['ThumbPath']):
		# Finished reading master photo list
		self.photoList.append(self.currentPhoto)
		self._reset_photo()

	state.level -= 1

    def CharData(self, data):
	state = self.state
	if (self.lastdata):
	    data = self.lastdata + data
	self.lastdata = data

	data = data.strip()

	if (state.key and data):
	    state.keyValue = data
	else:
	    state.value = data

	# determine which section we are in
	if (state.key and state.level == 3):
	    if (data == "Application Version"):
		state.libversion = True
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "Archive Path"):
		state.archivepath = True
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Albums"):
		state.libversion = False
		state.archivepath = False
		state.albums = True
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Rolls" or data == "Project List"):
		state.libversion = False
		state.archivepath = False
		state.albums = False
		state.rolls = True
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Faces"):
		state.libversion = False
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = True
		state.keywords = False
		state.master = False
	    elif (data == "List of Keywords"):
		state.libversion = False
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = True
		state.master = False
	    elif (data == "Master Image List"):
		state.libversion = False
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = True

	return


def test_progress_callback(altinfo, nphotos, ntotal):
    percent = int(float(nphotos * 100) / ntotal)
    print "%d/%d (%d%%)" % (nphotos, ntotal, percent)
    if (altinfo != ""):
	print altinfo
    return nphotos

def profile_main():
    import cProfile,pstats
    cProfile.run('main()', 'iphoto.prof')
    p = pstats.Stats('iphoto.prof')
    p.strip_dirs().sort_stats('time', 'cum').print_stats()

def main():
    try:
	xmltype = sys.argv[1]
	xmlpath = os.path.dirname(sys.argv[2])
	xmlfile = sys.argv[2]
	dbfile = sys.argv[3]
    except:
	print "Usage iphoto_parser.py <iPhoto|Aperture> <xmlfile> <db>"
	sys.exit(1)

    db = IPhotoDB(dbfile)
    db.ResetDB()
    db.InitDB()
    iparser = IPhotoParser(xmltype, xmlpath, xmlfile, "", "", [], False, 0.0, db.SetConfig, db.AddAlbumNew, db.AddRollNew, db.AddFaceNew, db.AddKeywordNew, db.AddMediaNew, test_progress_callback)
    try:
	iparser.Parse()
    except:
	print traceback.print_exc()
    db.Commit()

if __name__=="__main__":
    #main()
    profile_main()

# vim: tabstop=8 softtabstop=4 shiftwidth=4 noexpandtab:
