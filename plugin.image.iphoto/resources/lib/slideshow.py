"""
    Slideshow database
"""

__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import traceback

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os
import locale

try:
    from resources.lib.common import *
except:
    from common import *


class SlideshowDB:
    def __init__(self, dbfile):
	try:
	    self.dbPath = os.path.dirname(dbfile)
	    self.dbconn = sqlite.connect(dbfile)
	    self.InitDB()
	except Exception, e:
	    print "slideshow: init: " + to_str(e)
	    raise e

    def InitDB(self):
	self.dbconn.execute("PRAGMA synchronous = OFF")
	self.dbconn.execute("PRAGMA default_synchronous = OFF")
	self.dbconn.execute("PRAGMA journal_mode = OFF")
	self.dbconn.execute("PRAGMA temp_store = MEMORY")
	self.dbconn.execute("PRAGMA encoding = \"UTF-8\"")

	try:
	    # media table
	    self.dbconn.execute("""
	    CREATE TABLE media (
	       id integer primary key,
	       caption varchar,
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
	    # shows table
	    self.dbconn.execute("""
	    CREATE TABLE shows (
	       id integer primary key,
	       name varchar,
	       photocount integer
	    )""")
	except:
	    pass

	try:
	    # showmedia table
	    self.dbconn.execute("""
	    CREATE TABLE showmedia (
	       showid integer,
	       mediaid integer
	    )""")
	except:
	    pass

    def ResetDB(self):
	for table in ['media', 'shows', 'showmedia']:
	    try:
		self.dbconn.execute("DROP TABLE %s" % table)
	    except Exception, e:
		print "slideshow: ResetDB: " + to_str(e)
		raise e

	self.InitDB()

    def Commit(self):
	try:
	    self.dbconn.commit()
	except Exception, e:
	    print "slideshow: Commit: " + to_str(e)
	    raise e

    def GetMedia(self, mediapath, sort_col="NULL"):
	media = []
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM media M WHERE M.mediapath = ? ORDER BY %s ASC""" % (sort_col), (mediapath,))
	    for tuple in cur:
		media.append(tuple)
	    cur.close()
	except Exception, e:
	    print "slideshow: GetMedia: " + to_str(e)
	    pass

	return media

    def GetShows(self):
	shows = []
	try:
	    cur = self.dbconn.cursor()
	    cur.execute("SELECT id, name, photocount FROM shows")
	    for tuple in cur:
		shows.append(tuple)
	    cur.close()
	except Exception, e:
	    print "slideshow: GetShows: " + to_str(e)
	    pass

	return shows

    def GetMediaInShow(self, showid, sort_col="NULL"):
	media = []
	try:
	    if (sort_col != "NULL"):
		sort_col = "M." + sort_col
	    cur = self.dbconn.cursor()
	    cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating, M.mediadate, M.mediasize
			FROM showmedia A LEFT JOIN media M ON A.mediaid = M.id
			WHERE A.showid = ? ORDER BY %s ASC""" % (sort_col), (showid,))
	    for tuple in cur:
		media.append(tuple)
	    cur.close()
	except Exception, e:
	    print "slideshow: GetMediaInShow: " + to_str(e)
	    pass

	return media

    def AddShow(self, show):
	#print "AddShow()", show

	try:
	    showid = int(show['id'])
	except:
	    return

	try:
	    self.dbconn.execute("""
	    INSERT INTO shows (id, name, photocount)
	    VALUES (?, ?, ?)""",
				(showid,
				 show['name'],
				 show['PhotoCount']))
	    for media in show['medialist']:
		self.dbconn.execute("""
		INSERT INTO showmedia (showid, mediaid)
		VALUES (?, ?)""", (showid, media))
	except sqlite.IntegrityError:
	    pass
	except Exception, e:
	    raise e

# vim: tabstop=8 softtabstop=4 shiftwidth=4 noexpandtab:
