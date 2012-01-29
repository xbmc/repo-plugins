# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

#import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os
#import urllib2, string, re, htmlentitydefs, time, unicodedata

#from xml.sax.saxutils import unescape
#from xml.dom import minidom
#from urllib import quote_plus

from icecast_common import * 

DB_FILE_NAME = 'icecast.sqlite'
DB_CREATE_TABLE_STATIONS = 'CREATE TABLE stations (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255));'
DB_CREATE_TABLE_FAVOURITES = 'CREATE TABLE favourites (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255));'
DB_CREATE_TABLE_RECENT = 'CREATE TABLE recent (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255), unix_timestamp VARCHAR(255));'
DB_CREATE_TABLE_SETTINGS = 'CREATE TABLE settings (name VARCHAR(255), val VARCHAR(255))'
DB_CREATE_TABLE_UPDATES = 'CREATE TABLE updates (unix_timestamp VARCHAR(255));'
DB_CREATE_TABLE_VERSION = 'CREATE TABLE version (version INT);'
DB_REQUIRED_VERSION = 1 

# Init function for SQLite
def initSQLite():
  try:
    from sqlite3 import dbapi2 as sqlite
    log_notice("Using built-in SQLite via sqlite3!")
  except:
    try:
      from pysqlite2 import dbapi2 as sqlite
      log_notice("Using external SQLite via pysqlite2!")
    except:
      log_notice("SQLite not found -- reverting to older (and slower) text cache.")
      return 0, 0, 0, 0

  sqlite_file_name = getSQLiteFileName()
  sqlite_con = sqlite.connect(sqlite_file_name)
  sqlite_cur = sqlite_con.cursor()
  try:
    sqlite_cur.execute(DB_CREATE_TABLE_STATIONS)
    sqlite_cur.execute(DB_CREATE_TABLE_FAVOURITES)
    sqlite_cur.execute(DB_CREATE_TABLE_RECENT)
    sqlite_cur.execute(DB_CREATE_TABLE_SETTINGS)
    sqlite_cur.execute(DB_CREATE_TABLE_UPDATES)
    sqlite_cur.execute(DB_CREATE_TABLE_VERSION)

    sql_query = "INSERT INTO version (version) VALUES (%u)" % (DB_REQUIRED_VERSION)
    sqlite_cur.execute(sql_query)

    sql_query = "INSERT INTO settings (name, val) VALUES ('%s','%s')" % ('30098','0')
    sqlite_cur.execute(sql_query)

    sql_query = "INSERT INTO updates (unix_timestamp) VALUES ('1000')"
    sqlite_cur.execute(sql_query)

    sqlite_con.commit()

    sqlite_is_empty = 1
  except:
    # Check if the database needs upgrade
    try:
      version = 0
      sqlite_cur.execute("SELECT version FROM version")
      for version in sqlite_cur:
        if version < DB_REQUIRED_VERSION:
          upgradeDatabase(sqlite_con, sqlite_cur, version)
    except:
      # Upgrde from old version that has no 'version' table
      upgradeDatabase(0, sqlite_cur)
    sqlite_is_empty = 0

  return sqlite_con, sqlite_cur, sqlite_is_empty, 1

# Database upgrade
def upgradeDatabase(sqlite_con, sqlite_cur, version):
  if version == 0:
    sqlite_cur.execute(DB_CREATE_TABLE_FAVOURITES)
    sqlite_cur.execute(DB_CREATE_TABLE_RECENT)
    sqlite_cur.execute(DB_CREATE_TABLE_SETTINGS)
    sqlite_cur.execute(DB_CREATE_TABLE_VERSION)
    sql_query = "INSERT INTO version (version) VALUES (%u)" % (DB_REQUIRED_VERSION)
    sqlite_cur.execute(sql_query)
    sql_query = "INSERT INTO settings (name, val) VALUES ('%s','%s')" % ('30098','0')
    sqlite_cur.execute(sql_query)
    sqlite_con.commit()

# Compose the SQLite database file name
def getSQLiteFileName():
  cache_file_dir = getUserdataDir()
  db_file_name = os.path.join(cache_file_dir,DB_FILE_NAME)
  return db_file_name

