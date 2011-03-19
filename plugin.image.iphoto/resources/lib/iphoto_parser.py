"""
    Parser for iPhoto's AlbumData.xml
"""

__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import traceback
import xml.parsers.expat
from urllib import unquote
try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os
import os.path
import locale

def to_unicode(text):
    if (isinstance(text, unicode)):
	return text

    if (hasattr(text, '__unicode__')):
	return text.__unicode__()

    text = str(text)

    try:
	return unicode(text, 'utf-8')
    except UnicodeError:
	pass

    try:
	return unicode(text, locale.getpreferredencoding())
    except UnicodeError:
	pass

    return unicode(text, 'latin1')

def to_str(text):
    if (isinstance(text, str)):
	return text

    if (hasattr(text, '__unicode__')):
	text = text.__unicode__()

    if (hasattr(text, '__str__')):
	return text.__str__()

    return text.encode('utf-8')

class IPhotoDB:
    def __init__(self, dbfile):
	try:
	    self.dbconn = sqlite.connect(dbfile)
	    self.InitDB()
	except Exception, e:
	    print to_str(e)
	    pass
	return

    def _cleanup_filename(self, filename):
	if (filename.startswith("file://localhost")):
	    return unquote(filename[16:])
	else:
	    return unquote(filename)

    def InitDB(self):
	try:
	    self.dbconn.execute("PRAGMA synchronous = OFF")
	    self.dbconn.execute("PRAGMA default_synchronous = OFF")
	    self.dbconn.execute("PRAGMA journal_mode = OFF")
	    self.dbconn.execute("PRAGMA temp_store = MEMORY")
	    self.dbconn.execute("PRAGMA encoding = \"UTF-8\"")
	except Exception, e:
	    print to_str(e)
	    pass

	try:
	    # config table
	    self.dbconn.execute("""
	    CREATE TABLE config (
	       key varchar primary key,
	       value varchar
	    )""")
	except:
	    pass

	try:
	    # media table
	    self.dbconn.execute("""
	    CREATE TABLE media (
	       id integer primary key,
	       mediatypeid integer,
	       rollid integer,
	       caption varchar,
	       guid varchar,
	       aspectratio number,
	       rating integer,
	       mediadate integer,
	       mediasize integer,
	       mediapath varchar,
	       thumbpath varchar,
	       originalpath varchar
	    )""")
	except:
	    pass

	try:
	    # mediatypes table
	    self.dbconn.execute("""
	    CREATE TABLE mediatypes (
	       id integer primary key,
	       name varchar
	    )""")
	except:
	    pass

	try:
	    # rolls (events) table
	    self.dbconn.execute("""
	    CREATE TABLE rolls (
	       id integer primary key,
	       name varchar,
	       keyphotoid integer,
	       rolldate integer,
	       photocount integer
	    )""")
	except:
	    pass

	try:
	    # rollmedia table
	    self.dbconn.execute("""
	    CREATE TABLE rollmedia (
	       rollid integer,
	       mediaid integer,
	       mediaorder integer
	    )""")
	except Exception, e:
	    pass

	try:
	    # albums table
	    self.dbconn.execute("""
	    CREATE TABLE albums (
	       id integer primary key,
	       name varchar,
	       master boolean,
	       guid varchar,
	       photocount integer
	    )""")
	except:
	    pass

	try:
	    # albummedia table
	    self.dbconn.execute("""
	    CREATE TABLE albummedia (
	       albumid integer,
	       mediaid integer,
	       mediaorder integer
	    )""")
	except Exception, e:
	    pass

	try:
	    # faces table
	    self.dbconn.execute("""
	    CREATE TABLE faces (
	       id integer primary key,
	       name varchar,
	       keyphotoid integer,
	       photocount integer,
	       faceorder integer
	    )""")
	except:
	    pass

	try:
	    # facesmedia table
	    self.dbconn.execute("""
	    CREATE TABLE facesmedia (
	       faceid integer,
	       mediaid integer,
	       mediaorder integer
	    )""")
	except Exception, e:
	    pass

	try:
	    # keywords table
	    self.dbconn.execute("""
	    CREATE TABLE keywords (
	       id integer primary key,
	       name varchar,
	       photocount integer
	    )""")
	except:
	    pass

	try:
	    # keywordmedia table
	    self.dbconn.execute("""
	    CREATE TABLE keywordmedia (
	       keywordid integer,
	       mediaid integer,
	       mediaorder integer
	    )""")
	except Exception, e:
	    pass

    def ResetDB(self):
	for table in ['media', 'mediatypes', 'rolls', 'rollmedia', 'albums', 'albummedia', 'faces', 'facesmedia', 'keywords', 'keywordmedia']:
	    try:
		self.dbconn.execute("DROP TABLE %s" % table)
	    except Exception, e:
		print to_str(e)
		pass
	try:
	    self.InitDB()
	except Exception, e:
	    print to_str(e)
	    raise e

    def Commit(self):
	try:
	    self.dbconn.commit()
	except Exception, e:
	    print "Commit Error: " + to_str(e)
	    pass

    def GetConfig(self, key):
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT value
			   FROM config
			   WHERE key = ? LIMIT 1""",
			(key,))
	    row = cur.fetchone()
	    if (row):
		return row[0]
	    return None
	except:
	    return None

    def SetConfig(self, key, value):
	if (self.GetConfig(key) == None):
	    cur = self.dbconn.cursor()
	    cur.execute("""INSERT INTO config (key, value)
			   VALUES (?, ?)""",
			(key, value))
	    self.Commit()
	else:
	    cur = self.dbconn.cursor()
	    cur.execute("""UPDATE config
			   SET value = ?
			   WHERE key = ?""",
			(value, key))
	    self.Commit()

    def UpdateLastImport(self):
	self.SetConfig('lastimport', 'dummy')
	self.dbconn.execute("""UPDATE config
			       SET value = datetime('now')
			       WHERE key = ?""",
			    ('lastimport',))
	self.Commit()

    def GetTableId(self, table, value, column='name', autoadd=False, autoclean=True):
	try:
	    if (autoclean and not value):
		value = "Unknown"
	    cur = self.dbconn.cursor()

	    # query db for column with specified name
	    cur.execute("SELECT id FROM %s WHERE %s = ?" % (table, column),
			(value,))
	    row = cur.fetchone()

	    # create named ID if requested
	    if not row and autoadd and value and len(value) > 0:
		nextid = cur.execute("SELECT MAX(id) FROM %s" % table).fetchone()[0]
		if not nextid:
		    nextid = 1
		else:
		    nextid += 1
		cur.execute("INSERT INTO %s (id, %s) VALUES (?, ?)" % (table, column),
			    (nextid, value))
		return nextid # return new id
	    return row[0] # return id
	except Exception, e:
	    print to_str(e)
	    raise e

    def GetMediaTypeId(self, mediatype, autoadd=False):
	return self.GetTableId('mediatypes', mediatype, 'name', autoadd)

    def GetAlbums(self):
	albums = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("SELECT id, name, photocount FROM albums")
	    for tuple in cur:
		albums.append(tuple)
	except:
	    pass
	return albums

    def GetMediaInAlbum(self, albumid):
	media = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM albummedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.albumid = ?""", (albumid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return media

    def GetRolls(self):
	rolls = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT R.id, R.name, M.thumbpath, R.rolldate, R.photocount 
			 FROM rolls R LEFT JOIN media M ON R.keyphotoid = M.id""")
	    for tuple in cur:
		rolls.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return rolls

    def GetMediaInRoll(self, rollid):
	media = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM media M WHERE M.rollid = ?""", (rollid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return media

    def GetFaces(self):
	faces = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT F.id, F.name, M.thumbpath, F.photocount
			 FROM faces F LEFT JOIN media M ON F.keyphotoid = M.id
			 ORDER BY F.faceorder""")
	    for tuple in cur:
		faces.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return faces

    def GetMediaWithFace(self, faceid):
	media = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM facesmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.faceid = ?""", (faceid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return media

    def GetKeywords(self):
	keywords = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("SELECT id, name, photocount FROM keywords")
	    for tuple in cur:
		keywords.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return keywords

    def GetMediaWithKeyword(self, keywordid):
	media = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM keywordmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.keywordid = ?""", (keywordid,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return media

    def GetMediaWithRating(self, rating):
	media = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM media M WHERE M.rating = ?""", (rating,))
	    for tuple in cur:
		media.append(tuple)
	except Exception, e:
	    print to_str(e)
	    pass
	return media

    def AddAlbumNew(self, album, album_ign):
	#print "AddAlbumNew()", album

	try:
	    albumid = int(album['AlbumId'])
	    albumtype = album['Album Type']
	except:
	    return

	# weed out ignored albums
	if (albumtype in album_ign):
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO albums (id, name, master, guid, photocount)
	    VALUES (?, ?, ?, ?, ?)""",
				(albumid,
				 album['AlbumName'],
				 album.has_key('Master'),
				 album['GUID'],
				 album['PhotoCount']))
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

	try:
	    rollid = int(roll['RollID'])
	except:
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO rolls (id, name, keyphotoid, rolldate, photocount)
	    VALUES (?, ?, ?, ?, ?)""",
				(rollid,
				 roll['RollName'],
				 roll['KeyPhotoKey'],
				 int(float(roll['RollDateAsTimerInterval'])),
				 roll['PhotoCount']))
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
	except:
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO faces (id, name, keyphotoid, photocount, faceorder)
	    VALUES (?, ?, ?, ?, ?)""",
				(faceid,
				 face['name'],
				 face['key image'],
				 face['PhotoCount'],
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

    def AddMediaNew(self, media, archivePath, libraryPath):
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
	    imagepath = media['ImagePath'].replace(archivePath, libraryPath)
	    thumbpath = media['ThumbPath'].replace(archivePath, libraryPath)
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

	try:
	    self.dbconn.execute("""
	    INSERT INTO media (id, mediatypeid, rollid, caption, guid, aspectratio, rating, mediadate, mediasize, mediapath, thumbpath, originalpath)
	    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
				(mediaid,
				 self.GetMediaTypeId(media['MediaType'], True),
				 media['Roll'],
				 media['Caption'],
				 media['GUID'],
				 media['Aspect Ratio'],
				 media['Rating'],
				 int(float(media['DateAsTimerInterval'])),
				 mediasize,
				 imagepath,
				 thumbpath,
				 originalpath))

	    for faceid in media['facelist']:
		self.dbconn.execute("""
		INSERT INTO facesmedia (faceid, mediaid)
		VALUES (?, ?)""", (faceid, mediaid))
		cur = self.dbconn.cursor()

	    for keywordid in media['keywordlist']:
		self.dbconn.execute("""
		INSERT INTO keywordmedia (keywordid, mediaid)
		VALUES (?, ?)""", (keywordid, mediaid))
		cur = self.dbconn.cursor()
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
    def __init__(self, library_path="", xmlfile="", album_callback=None, album_ign=[],
		 roll_callback=None, face_callback=None, keyword_callback=None, photo_callback=None,
		 progress_callback=None, progress_dialog=None):
	self.libraryPath = library_path
	self.xmlfile = xmlfile
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
	self.AlbumCallback = album_callback
	self.albumIgn = album_ign
	self.RollCallback = roll_callback
	self.FaceCallback = face_callback
	self.KeywordCallback = keyword_callback
	self.PhotoCallback = photo_callback
	self.ProgressCallback = progress_callback
	self.ProgressDialog = progress_dialog
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
	self.currentPhoto['facelist'] = []
	self.currentPhoto['keywordlist'] = []

    def _reset_album(self):
	self.currentAlbum = {}
	for a in ['GUID', 'Master']:
	    self.currentAlbum[a] = ""
	for a in self.currentAlbum.keys():
	    self.currentAlbum[a] = ""
	self.currentAlbum['medialist'] = []

    def _reset_roll(self):
	self.currentRoll = {}
	for a in self.currentRoll.keys():
	    self.currentRoll[a] = ""
	self.currentRoll['medialist'] = []

    def _reset_face(self):
	self.currentFace = {}
	for a in self.currentFace.keys():
	    self.currentFace[a] = ""

    def _reset_keyword(self):
	self.currentKeyword = {}
	for a in self.currentKeyword.keys():
	    self.currentKeyword[a] = ""

    def updateProgress(self):
	if (not self.ProgressCallback):
	    return

	state = self.state
	state.nphotos = self.ProgressCallback(self.ProgressDialog, state.nphotos, state.nphotostotal)
	if (state.nphotos == None):
	    raise ParseCanceled(0)

    def commitAll(self):
	state = self.state

	state.nphotostotal = len(self.albumList) + len(self.rollList) + len(self.faceList) + len(self.keywordList) + len(self.photoList)

	try:
	    if (self.AlbumCallback and len(self.albumList) > 0):
		for a in self.albumList:
		    self.AlbumCallback(a, self.albumIgn)
		    self.updateProgress()

	    if (self.RollCallback and len(self.rollList) > 0):
		for a in self.rollList:
		    self.RollCallback(a)
		    self.updateProgress()

	    if (self.FaceCallback and len(self.faceList) > 0):
		for a in self.faceList:
		    self.FaceCallback(a)
		    self.updateProgress()

	    if (self.KeywordCallback and len(self.keywordList) > 0):
		for a in self.keywordList:
		    self.KeywordCallback(a)
		    self.updateProgress()

	    if (self.PhotoCallback and len(self.photoList) > 0):
		for a in self.photoList:
		    self.PhotoCallback(a, self.imagePath, self.libraryPath)
		    self.updateProgress()
	except ParseCanceled:
	    raise
	except Exception, e:
	    print to_str(e)
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
	except ParseCanceled:
	    return
	except Exception, e:
	    print to_str(e)
	    raise e

	try:
	    self.commitAll()
	except ParseCanceled:
	    return
	except Exception, e:
	    print to_str(e)
	    raise e

    def StartElement(self, name, attrs):
	state = self.state
	self.lastdata = False
	if (state.archivepath):
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
	    #print "Got key type " + to_str(name)
	else:
	    if (state.key):
		state.valueType = name
		#print "Got value type " + to_str(name)
	    else:
		state.valueType = ""
		#print "Got empty value type"
	    state.key = False

	state.level += 1

    def EndElement(self, name):
	self.lastdata = False
	state = self.state

	if (state.archivepath):
	    if (not state.key):
		self.imagePath = state.value
		print "Rewriting iPhoto archive path '%s'" % (to_str(self.imagePath))
		print "as '%s'" % (to_str(self.libraryPath))
		state.archivepath = False
	    state.inarchivepath -= 1

	# Albums
	elif (state.albums):
	    if (state.inalbum == 3 and self.currentAlbum.has_key('AlbumId')):
		self.currentAlbum['medialist'].append(state.value)
	    elif (state.inalbum == 2 and not state.key):
		#print "Mapping %s => %s" % ( to_str(state.keyValue), to_str(state.value))
		self.currentAlbum[state.keyValue] = state.value
	    state.inalbum -= 1
	    if (state.inalbum == 0 and self.currentAlbum.has_key('AlbumId')):
		# Finished reading album
		self.albumList.append(self.currentAlbum)
		self._reset_album()

	# Rolls
	elif (state.rolls):
	    if (state.inroll == 3 and self.currentRoll.has_key('RollID')):
		self.currentRoll['medialist'].append(state.value)
	    elif (state.inroll == 2 and not state.key):
		#print "Mapping %s => %s" % ( to_str(state.keyValue), to_str(state.value))
		self.currentRoll[state.keyValue] = state.value
	    state.inroll -= 1
	    if (state.inroll == 0 and self.currentRoll.has_key('RollID')):
		# Finished reading roll
		self.rollList.append(self.currentRoll)
		self._reset_roll()

	# Faces
	elif (state.faces):
	    if (state.inface == 2 and not state.key):
		#print "Mapping %s => %s" % ( to_str(state.keyValue), to_str(state.value))
		self.currentFace[state.keyValue] = state.value
	    state.inface -= 1
	    if (state.inface == 0 and not state.key):
		# Finished reading faces
		self.faceList.append(self.currentFace)
		self._reset_face()

	# Keywords
	elif (state.keywords):
	    if (state.inkeyword == 1 and not state.key):
		#print "Mapping %s => %s" % ( to_str(state.keyValue), to_str(state.value))
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
	    elif (state.inmaster == 3 and not state.key and state.keyValue == "Keywords"):
		self.currentPhoto['keywordlist'].append(state.value)
	    elif (state.inmaster == 4 and not state.key and state.keyValue == "face key"):
		self.currentPhoto['facelist'].append(state.value)
	    elif (state.inmaster == 2 and not state.key):
		#print "Mapping %s => %s" % ( to_str(state.keyValue), to_str(state.value))
		self.currentPhoto[state.keyValue] = state.value
	    state.inmaster -= 1
	    if (state.inmaster == 0 and self.currentPhoto.has_key('GUID') and self.currentPhoto['GUID']):
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
	    if (data == "Archive Path"):
		state.archivepath = True
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Albums"):
		state.archivepath = False
		state.albums = True
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Rolls"):
		state.archivepath = False
		state.albums = False
		state.rolls = True
		state.faces = False
		state.keywords = False
		state.master = False
	    elif (data == "List of Faces"):
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = True
		state.keywords = False
		state.master = False
	    elif (data == "List of Keywords"):
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = True
		state.master = False
	    elif (data == "Master Image List"):
		state.archivepath = False
		state.albums = False
		state.rolls = False
		state.faces = False
		state.keywords = False
		state.master = True

	return


def profile_main():
    import hotshot, hotshot.stats
    prof = hotshot.Profile("iphoto.prof")
    prof.runcall(main)
    prof.close()
    stats = hotshot.stats.load("iphoto.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(20)

def main():
    try:
	xmlfile = sys.argv[1]
    except:
	print "Usage iphoto_parser.py <xmlfile>"
	sys.exit(1)

    db = IPhotoDB("iphoto.db")
    db.ResetDB()
    iparser = IPhotoParser("", xmlfile, db.AddAlbumNew, "", db.AddRollNew, db.AddFaceNew, db.AddKeywordNew, db.AddMediaNew)
    try:
	iparser.Parse()
    except:
	print traceback.print_exc()
    db.Commit()

if __name__=="__main__":
    main()
    #profile_main()
