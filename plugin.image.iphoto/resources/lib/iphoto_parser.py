"""
    Parser for iPhoto's AlbumData.xml
"""

__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "Anoop Menon, Nuka1195, JMarshal, jingai"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import traceback
import xml.parsers.expat
from pysqlite2 import dbapi2 as sqlite
from urllib import unquote
import sys
import os
import os.path

class IPhotoDB:
    def __init__(self, dbfile):
        self.dbconn = sqlite.connect(dbfile)
        self.InitDB()
        return

    def _cleanup_filename(self, filename):
        if filename.startswith("file://localhost"):
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
            print str(e)
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
            # tracks table
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
               mediapath varchar,
               thumbpath varchar,
               originalpath varchar
            )""")
        except:
            pass

        try:
            # filetypes table
            self.dbconn.execute("""
            CREATE TABLE keywords (
               id integer primary key,
               name varchar
            )""")
        except:
            pass

        try:
            # filetypes table
            self.dbconn.execute("""
            CREATE TABLE mediatypes (
               id integer primary key,
               name varchar
            )""")
        except:
            pass

        try:
            # genres table
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
            # playlist tracks
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
            # playlist tracks
            self.dbconn.execute("""
            CREATE TABLE albummedia (
               albumid integer,
               mediaid integer,
               mediaorder integer
            )""")
        except Exception, e:
            pass

    def GetConfig(self, key):
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT value
                           FROM config
                           WHERE key = ? LIMIT 1""",
                        (key,))
            row = cur.fetchone()
            if row:
                return row[0]
            return None
        except:
            return None

    def SetConfig(self, key, value):
        if self.GetConfig(key)==None:
            cur = self.dbconn.cursor()
            cur.execute("""INSERT INTO config(key,value)
                           VALUES(?,?)""",
                        (key, value))
            self.Commit()
        else:
            cur = self.dbconn.cursor()
            cur.execute("""UPDATE config
                           SET value=?
                           WHERE key=?""",
                        (value, key))
            self.Commit()

    def UpdateLastImport(self):
        self.SetConfig('lastimport', 'dummy')
        self.dbconn.execute("""UPDATE config
                               SET value=datetime('now')
                               WHERE key=?""",
                            ('lastimport',))
        self.Commit()

    def GetAlbums(self):
        albums = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name FROM albums")
            for tuple in cur:
                albums.append(tuple)
        except:
            pass
        return albums

    def GetRolls(self):
        rolls = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT R.id,R.name,M.thumbpath,R.rolldate,R.photocount 
                         FROM rolls R LEFT JOIN media M ON R.keyphotoid=M.id""")
            for tuple in cur:
                rolls.append(tuple)
        except Exception, e:
            print str(e)
            pass
        return rolls

    def GetMediaInRoll(self, rollid):
        media = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating
                        FROM media M WHERE M.rollid = ?""", (rollid,))
            for tuple in cur:
                media.append(tuple)
        except Exception, e:
            print str(e)
            pass
        return media

    def GetMediaWithRating(self, rating):
        media = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating
                        FROM media M WHERE M.rating = ?""", (rating,))
            for tuple in cur:
                media.append(tuple)
        except Exception, e:
            print str(e)
            pass
        return media

    def GetMediaInAlbum(self, albumid):
        media = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("""SELECT M.caption, M.mediapath, M.thumbpath, M.originalpath, M.rating
                        FROM albummedia A LEFT JOIN media M ON A.mediaid=M.id
                        WHERE A.albumid = ?""", (albumid,))
            for tuple in cur:
                media.append(tuple)
        except Exception, e:
            print str(e)
            pass
        return media

    def GetKeywords(self):
        genres = []
        try:
            cur = self.dbconn.cursor()
            cur.execute("SELECT id,name FROM keywords")
            for tuple in cur:
                genres.append(tuple)
        except Exception, e:
            print str(e)
            pass
        return genres

    def GetAlbumId(self, album, artist, autoadd=False):
        albumid = self.GetTableId('albums', album, 'name', autoadd)
        if artist:
            artistid = self.GetArtistId(artist, autoadd=True)
            self.dbconn.execute("""UPDATE albums SET artistid = ?
                                   WHERE id = ? """, (artistid, albumid))
        return albumid

    def GetMediaTypeId(self, mediatype, autoadd=False):
        return self.GetTableId('mediatypes', mediatype, 'name', autoadd)

    def GetTableId(self, table, value, column='name', autoadd=False, autoclean=True):
        try:
            if autoclean and not value:
                value = "Unknown"
            cur = self.dbconn.cursor()

            # query db for column with specified name
            cur.execute("SELECT id FROM %s WHERE %s = ?" % (table, column),
                        (value,))
            row = cur.fetchone()

            # create named ID if requested
            if not row and autoadd and value and len(value)>0:
                nextid = cur.execute("SELECT MAX(id) FROM %s" % table).fetchone()[0]
                if not nextid:
                    nextid = 1
                else:
                    nextid += 1
                cur.execute("INSERT INTO %s(id, %s) VALUES (?,?)" % (table, column),
                            (nextid, value))
                #self.Commit()
                return nextid # return new artist id
            return row[0] # return artist id
        except Exception, e:
            print str(e)
            raise e
            #return None

    def Commit(self):
        try:
            self.dbconn.commit()
        except Exception, e:
            print "Commit Error: " + str(e)
            pass

    def ResetDB(self):
        for table in ['keywords','rolls','rollmedia','albums','albummedia','media','mediatypes']:
            try:
                self.dbconn.execute("DROP TABLE %s" % table)
            except Exception, e:
                print str(e)
                pass
        try:
            self.InitDB()
        except Exception, e:
            print str(e)
            raise e

    def GetNextId(self, tablename):
        cur = self.dbconn.cursor()
        cur.execute("SELECT MAX(id) FROM %s" % tablename)
        row = cur.fetchone()
        if not row:
            return 1
        return row[0]+1

    def _track_from_tuple(self, tuple):
        track = {}
        # TODO: convert track to a class
        track['id'] = tuple[0]
        track['name'] = tuple[1]
        track['playcount'] = tuple[2]
        track['rating'] = tuple[3]
        track['year'] = tuple[4]
        track['bitrate'] = tuple[5]
        track['albumtracknumber'] = tuple[6]
        track['filename'] = tuple[7]
        track['album'] = tuple[8]
        track['artist'] = tuple[9]
        track['playtime'] = tuple[10]
        track['genre'] = tuple[11]
        return track

    def AddAlbumNew(self, album, album_ign):
        try:
            albumid = int(album['AlbumId'])
	    albumtype = album['Album Type']
        except:
            return

	# weed out ignored albums
	if albumtype in album_ign:
	    return
	#print "Adding album of type %s" % (albumtype)

        try:
            self.dbconn.execute("""
            INSERT INTO albums (id, name, master, guid, photocount)
            VALUES (?,?,?,?,?)""",
                                (albumid,
                                 album['AlbumName'],
                                 album.has_key('Master'),
                                 album['GUID'],
                                 album['PhotoCount']))
            for media in album['medialist']:
                self.dbconn.execute("""
                INSERT INTO albummedia ( albumid, mediaid )
                VALUES (?,?)""", (albumid, media))
        except sqlite.IntegrityError:
            pass
        except Exception, e:
            raise e
        #self.Commit()

    def AddRollNew(self, roll):
        try:
            rollid = int(roll['RollID'])
        except:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO rolls (id, name, keyphotoid, rolldate, photocount)
            VALUES (?,?,?,?,?)""",
                                (rollid,
                                 roll['RollName'],
                                 roll['KeyPhotoKey'],
                                 int(float(roll['RollDateAsTimerInterval'])),
                                 roll['PhotoCount']))
            for media in roll['medialist']:
                self.dbconn.execute("""
                INSERT INTO rollmedia ( rollid, mediaid )
                VALUES (?,?)""", (rollid, media))
        except sqlite.IntegrityError:
            pass
        except Exception, e:
            raise e
        #self.Commit()

    def AddKeywordNew(self, keyword):
        try:
            kid = keyword.keys()[0]
            kword = keyword[kid]
        except:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO keywords (id, name)
            VALUES (?,?)""",
                                (int(kid),
                                 kword))
        except sqlite.IntegrityError:
            pass
        except Exception, e:
            raise e
        #self.Commit()

    def AddMediaNew(self, media):
        #print "Media => " + str(media)
        try:
            mediaid = media['MediaID']
            if not mediaid:
                return
        except Exception, e:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO media (id, mediatypeid, rollid, caption, guid,
                              aspectratio, rating, mediadate, mediapath,
                              thumbpath, originalpath)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                (mediaid,
                                 self.GetMediaTypeId(media['MediaType'], True),
                                 media['Roll'],
                                 media['Caption'],
                                 media['GUID'],
                                 media['Aspect Ratio'],
                                 media['Rating'],
                                 int(float(media['DateAsTimerInterval'])),
                                 media['ImagePath'],
                                 media['ThumbPath'],
                                 media['OriginalPath']))
        except sqlite.IntegrityError:
            pass
        except Exception, e:
            raise e
        #self.Commit()

    def AddMediaToAlbum(self, mediaid, albumid, order):
        if not playlistid or not trackid:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO albummedia ( albumid, mediaid, mediaorder )
            VALUES (?,?,?)""", (albumid, mediaid, order))
        except Exception, e:
            print str(e)

    def AddMediaToRoll(self, mediaid, rollid, order):
        if not playlistid or not trackid:
            return
        try:
            self.dbconn.execute("""
            INSERT INTO rollmedia ( rollid, mediaid, mediaorder )
            VALUES (?,?,?)""", (rollid, mediaid, order))
        except Exception, e:
            print str(e)


class IPhotoParserState:
    def __init__(self):
        self.level = 0
        self.albums = False
        self.inalbum = 0
        self.rolls = False
        self.inroll = 0
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
    def __init__(self, album_callback=None, album_ign=[], roll_callback=None,
                 keyword_callback=None, photo_callback=None, progress_callback=None):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.StartElement
        self.parser.EndElementHandler = self.EndElement
        self.parser.CharacterDataHandler = self.CharData
        self.state = IPhotoParserState()
        self.ele = ""
        self.currentPhoto = {}
        self.currentAlbum = {}
        self.currentRoll = {}
        self.currentKeyword = {}
        self.AlbumCallback = album_callback
	self.albumIgn = album_ign
        self.RollCallback = roll_callback
        self.KeywordCallback = keyword_callback
        self.PhotoCallback = photo_callback
        self.ProgressCallback = progress_callback
        self.lastdata = False
        self._reset_photo()
        self._reset_album()
        self._reset_roll()
        self._reset_keyword()

    def _reset_photo(self):
        self.currentPhoto = {}
        for a in ['OriginalPath','Caption','ThumbPath','Rating','ImagePath',
                  'Roll','MediaType','GUID','DateAsTimerInterval']:
            self.currentPhoto[a] = ''
        self.currentPhoto['Aspect Ratio'] = '0'
        self.currentPhoto['DateAsTimerInterval'] = '0'

    def _reset_album(self):
        try:
            del self.currentAlbum['Master']
        except:
            pass
        for a in self.currentAlbum.keys():
            self.currentAlbum[a] = ""
        self.currentAlbum['medialist'] = []

    def _reset_roll(self):
        for a in self.currentRoll.keys():
            self.currentRoll[a] = ""
        self.currentRoll['medialist'] = []

    def _reset_keyword(self):
        for a in self.currentKeyword.keys():
            del self.currentKeyword[a]

    def Parse(self, filename):
        try:
            #totalsize = os.path.getsize(filename)
            BLOCKSIZE = 8192
            #readsize = BLOCKSIZE
            f = open(filename, "r")
            buf = f.read(BLOCKSIZE)
            while buf:
                self.parser.Parse(buf, False)
                #readsize += BLOCKSIZE
                buf = f.read(BLOCKSIZE)
            self.parser.Parse(buf, True)
            f.close()
        except Exception, e:
            print str(e)
            raise e

    def StartElement(self, name, attrs):
        state = self.state
        self.lastdata = False
        if state.albums:
            state.inalbum += 1
            state.key = name
        elif state.rolls:
            state.inroll += 1
            state.key = name
        elif state.keywords:
            state.inkeyword += 1
            state.key = name
        elif state.master:
            state.inmaster += 1
            state.key = name

        if name == "key":
            state.key = True
            #print "Got key type " + str(name)
        else:
            if state.key:
                state.valueType = name
                #print "Got value type " + str(name)
            else:
                state.valueType = ""
                #print "Got empty value type "
            state.key = False
        state.level += 1

    def EndElement(self, name):
        self.lastdata = False
        state = self.state
        # Albums
        if state.albums:
            # Handle updating a track
            if state.inalbum == 3 and self.currentAlbum.has_key('AlbumId'):
                self.currentAlbum['medialist'].append(state.value)
            elif state.inalbum == 2 and not state.key:
                #print "Mapping %s => %s" % ( str(state.keyValue), str(state.value))
                self.currentAlbum[state.keyValue] = state.value
            state.inalbum -= 1
            if state.inalbum == 0 and self.currentAlbum.has_key('AlbumId'):
                # Finished reading album, process it now
                if self.AlbumCallback:
                    self.AlbumCallback(self.currentAlbum, self.albumIgn)
                if self.ProgressCallback:
                    try:
                        self.ProgressCallback(-1, -1)
                    except:
                        pass
                #print self.currentTrack
                self._reset_album()

        # Rolls
        elif state.rolls:
            # Handle updating a track
            if state.inroll == 3 and self.currentRoll.has_key('RollID'):
                self.currentRoll['medialist'].append(state.value)
            elif state.inroll == 2 and not state.key:
                #print "Mapping %s => %s" % ( str(state.keyValue), str(state.value))
                self.currentRoll[state.keyValue] = state.value
            state.inroll -= 1
            if state.inroll == 0 and self.currentRoll.has_key('RollID'):
                # Finished reading album, process it now
                if self.RollCallback:
                    self.RollCallback(self.currentRoll)
                if self.ProgressCallback:
                    try:
                        self.ProgressCallback(-1, -1)
                    except:
                        pass
                self._reset_roll()

        # Keywords
        elif state.keywords:
            # Handle updating a track
            if state.inkeyword == 1 and not state.key:
                #print "Mapping %s => %s" % ( str(state.keyValue), str(state.value))
                self.currentKeyword[state.keyValue] = state.value
            state.inkeyword -= 1
            if state.inkeyword == 0 and not state.key:
                # Finished reading album, process it now
                if self.KeywordCallback:
                    self.KeywordCallback(self.currentKeyword)
                if self.ProgressCallback:
                    try:
                        self.ProgressCallback(-1, -1)
                    except:
                        pass
                self._reset_keyword()

        # Master Image List
        elif state.master:
            # Handle updating a track
            if state.inmaster == 1 and state.key:
                self.currentPhoto['MediaID'] = state.keyValue
            elif state.inmaster == 2 and not state.key:
                #print "Mapping %s => %s" % ( str(state.keyValue), str(state.value))
                self.currentPhoto[state.keyValue] = state.value
            state.inmaster -= 1
            if state.inmaster == 0 and self.currentPhoto.has_key('GUID') and self.currentPhoto['GUID']:
                # Finished reading album, process it now
                if self.PhotoCallback:
                    self.PhotoCallback(self.currentPhoto)
                if self.ProgressCallback:
                    try:
                        self.ProgressCallback(-1, -1)
                    except:
                        pass
                self._reset_photo()

        state.level -= 1

    def CharData(self, data):
        state = self.state
        if self.lastdata:
            data = self.lastdata + data
        self.lastdata = data

        data = data.strip()

        # FIXME: next condition probably not needed
        #if state.albums or state.master or state.rolls or state.keywords:
            # store key => value pairs
        if state.key and data:
            state.keyValue = data
        else:
            state.value = data

        # determine which section we are in
        if state.key and state.level==3:
            if data=="List of Albums":
                state.albums = True
                state.rolls  = False
                state.keywords = False
                state.master = False
            elif data=="List of Rolls":
                state.albums = False
                state.rolls  = True
                state.keywords = False
                state.master = False
            elif data=="List of Keywords":
                state.albums = False
                state.rolls  = False
                state.master = False
                state.keywords = True
            elif data=="Master Image List":
                state.albums = False
                state.rolls  = False
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
    xmlfile = ""
    try:
        xmlfile = sys.argv[1]
    except:
        print "Usage iphoto_parser.py <xmlfile>"
        sys.exit(1)

    db = IPhotoDB("iphoto.db")
    db.ResetDB()
    iparser = IPhotoParser(db.AddAlbumNew, db.AddRollNew, db.AddKeywordNew, db.AddMediaNew)
    try:
        iparser.Parse(xmlfile)
    except:
        print traceback.print_exc()
    db.Commit()

if __name__=="__main__":
    main()
    #profile_main()
