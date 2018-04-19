# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
"""
Database module

This module handles all MySQL and SQLite queries

This file is part of Special Features.

Special Features is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

Special Features is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Special Features. If not, see <http://www.gnu.org/licenses/>.

@author: smitchell6879
@author: evertiro
@license: GPL-3.0
"""

from lib.sys_init import *


class QUERY:
    def queries(self):
        QUERY = {'movies': '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "genre", "year", "rating", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "playcount", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "runtime", "set", "showlink", "streamdetails", "top250", "votes", "fanart", "thumbnail", "file", "sorttitle", "resume", "setid", "dateadded", "tag", "art", "userrating", "ratings", "premiered", "uniqueid"], "sort": { "method": "label" } }, "id": 1}',
                 'tvshows': '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["title", "genre", "year", "rating", "plot", "studio", "mpaa", "cast", "playcount", "episode", "imdbnumber", "premiered", "votes", "lastplayed", "fanart", "thumbnail", "file", "originaltitle","sorttitle","episodeguide","season","watchedepisodes","dateadded","tag","art","userrating","ratings","runtime","uniqueid"], "sort": { "method": "label" } }, "id": 1}',
                 'seasons': '{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": {"properties": ["season", "showtitle", "playcount", "episode", "fanart", "thumbnail", "tvshowid", "watchedepisodes", "art", "userrating"], "sort": { "method": "label" } }, "id": 1}',
                 }
        return QUERY

    def jsonquery(self, query):
        self.json = xbmc.executeJSONRPC('{}'.format(query))
        return json.loads(self.json)

    def router(self, query):
        self.queries = self.queries()
        self.result = self.jsonquery(self.queries.get('{}'.format(query)))
        return self.result

    def executeJSON(self, method, params):
        self.json = json.dumps({'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1})
        self.result = json.loads(xbmc.executeJSONRPC(self.json))
        return self.result


class SQL:
    def mySql(self):
        self.conI = connect(host=ipadd, port=ipport, user=user, password=pword, charset=charSet, cursorclass=cuType)
        self.cuI = self.conI.cursor()
        self.command = "CREATE DATABASE IF NOT EXISTS {}".format(dbName)
        self.cuI.execute(self.command)
        self.conO = connect(host=ipadd, port=ipport, user=user, password=pword, db=dbName, charset=charSet, cursorclass=cuType)
        self.cuO = self.conO.cursor()
        self.tables = Build().queries()
        for self.table in self.tables:
            self.command = self.tables.get(self.table)
            self.cuO.execute(self.command)
        self.conI.close()
        self.conO.close()
        return

    def sqLite(self):
        if not xbmcvfs.exists(dbdir):
            xbmcvfs.mkdir(addir)
        self.con = sqlite3.connect('{}'.format(dbdir))
        self.cu = self.con.cursor()
        self.tables = Build().queries()
        for self.table in self.tables:
            self.command = self.tables.get(self.table)
            self.cu.execute('{}'.format(self.command))
            self.con.commit()
        return

    def setControl(self):
        info("QUERYING DATABASE")
        if mysql == 'true':
            self.mySql()
            self.con = connect(host=ipadd, port=ipport, user=user, password=pword, db=dbName, charset=charSet, cursorclass=cuType)
            self.queries = Build().mysql()
        else:
            self.sqLite()
            self.con = sqlite3.connect('{}'.format(dbdir))
            self.queries = Build().sqlite()

        self.con.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
        global con
        con = self.con
        global cu
        cu = self.con.cursor()
        global queries
        queries = self.queries
        return

    def exeCute(self, query="", var="", mode=""):
        self.command = queries.get('{}'.format(query))
        if mode == 'one':
            cu.execute(self.command, (var,))
            return cu.fetchone()
        if mode == 'onev':
            cu.execute(self.command, var)
            return cu.fetchone()
        elif mode == 'all':
            cu.execute(self.command)
            return cu.fetchall()
        elif mode == 'allv':
            cu.execute(self.command, var)
            return cu.fetchall()
        elif mode == 'com':
            cu.execute(self.command, var)
            con.commit()
        elif mode == 'com2':
            cu.execute(self.command, (var,))
            con.commit()
        elif mode == "":
            cu.execute(self.command)
            con.commit()
        return


class Build:
    def queries(self):
        QUERY = {'tvshows': 'CREATE TABLE IF NOT EXISTS tvshows (file TEXT, title TEXT, year TEXT, plot TEXT, rating TEXT, votes TEXT, dateadded TEXT, mpaa TEXT, premiered TEXT, userrating TEXT, top250 TEXT, trailer TEXT, sorttitle TEXT, tid text)',
                 'movies': 'CREATE TABLE IF NOT EXISTS movies (file TEXT, title TEXT, year TEXT, plot TEXT, rating TEXT, votes TEXT, dateadded TEXT, mpaa TEXT, premiered TEXT, userrating TEXT, top250 TEXT, trailer TEXT, sorttitle TEXT, mid text)',
                 'art': 'CREATE TABLE IF NOT EXISTS art (file TEXT, type TEXT, location TEXT)',
                 'cast': 'CREATE TABLE IF NOT EXISTS cast ( file TEXT, name TEXT, thumbnail TEXT, role TEXT, ordr TEXT)',
                 'special': 'CREATE TABLE IF NOT EXISTS special (file TEXT, title TEXT, bpath TEXT, sorttitle TEXT, plot TEXT, thumb TEXT)'
                 }
        # 'ratings'  : 'CREATE TABLE IF NOT EXISTS cast ()'
        # 'studio'   : 'CREATE TABLE IF NOT EXISTS cast ()'
        # 'genre'    : 'CREATE TABLE IF NOT EXISTS cast ()'
        # 'tag'      : 'CREATE TABLE IF NOT EXISTS cast ()'
        return QUERY

    def sqlite(self):
        # SELECT ALL
        QUERY = {'all_tvshows': 'SELECT * FROM tvshows',
                 'all_movies': 'SELECT * FROM movies',
                 'all_special': 'SELECT * FROM special',
                 'alw_movies': 'SELECT * FROM movies WHERE title=?',
                 'alw_tvshows': 'SELECT * FROM tvshows WHERE title=?',
                 # SELECT FROM WHERE
                 'fw_tvshows': 'SELECT * FROM tvshows WHERE file=?',
                 'fw_movies': 'SELECT * FROM movies WHERE file=?',
                 'fw_special': 'SELECT * FROM special WHERE file=?',
                 'fw_special2': 'SELECT * FROM special WHERE bpath=?',
                 'fw_special3': 'SELECT * FROM special WHERE file=? AND title=?',
                 'fw_art': 'SELECT * FROM art WHERE file=?',
                 'fw_art2': 'SELECT * FROM art WHERE file=? AND type=?',
                 'fw_cast': 'SELECT * FROM cast WHERE file=?',
                 'fw_cast2': 'SELECT * FROM cast WHERE file=? AND name=?',
                 # INSERT
                 'in_tvshows': 'INSERT INTO tvshows VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                 'in_movies': 'INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                 'in_special': 'INSERT INTO special VALUES (?,?,?,?,?,?)',
                 'in_art': 'INSERT INTO art VALUES (?,?,?)',
                 'in_cast': 'INSERT INTO cast VALUES (?,?,?,?,?)',
                 # UPDATE
                 'up_special': 'UPDATE special SET title=?,sorttitle=?,plot=? WHERE file=? AND bpath=?',
                 # DELETE
                 'd_tvshows': 'DELETE FROM tvshows WHERE file=?',
                 'd_movies': 'DELETE FROM movies WHERE file=?',
                 'd_special': 'DELETE FROM special WHERE file=?',
                 'd_special2': 'DELETE FROM special WHERE bpath=?',
                 'd_art': 'DELETE FROM art WHERE file=?',
                 'd_cast': 'DELETE FROM cast WHERE file=?',
                 }
        return QUERY

    def mysql(self):
        # SELECT ALL
        QUERY = {'all_tvshows': 'SELECT * FROM tvshows',
                 'all_movies': 'SELECT * FROM movies',
                 'all_special': 'SELECT * FROM special',
                 'alw_movies': 'SELECT * FROM movies WHERE title=%s',
                 'alw_tvshows': 'SELECT * FROM tvshows WHERE title=%s',
                 # SELECT FROM WHERE
                 'fw_tvshows': 'SELECT * FROM tvshows WHERE file=%s',
                 'fw_movies': 'SELECT * FROM movies WHERE file=%s',
                 'fw_special': 'SELECT * FROM special WHERE file=%s',
                 'fw_special2': 'SELECT * FROM special WHERE bpath=%s',
                 'fw_special3': 'SELECT * FROM special WHERE file=%s AND title=%s',
                 'fw_art': 'SELECT * FROM art WHERE file=%s',
                 'fw_art2': 'SELECT * FROM art WHERE file=%s AND type=%s',
                 'fw_cast': 'SELECT * FROM cast WHERE file=%s',
                 'fw_cast2': 'SELECT * FROM cast WHERE file=%s AND name=%s',
                 # INSERT
                 'in_tvshows': 'INSERT INTO tvshows VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                 'in_movies': 'INSERT INTO movies VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                 'in_special': 'INSERT INTO special VALUES (%s,%s,%s,%s,%s,%s)',
                 'in_art': 'INSERT INTO art VALUES (%s,%s,%s)',
                 'in_cast': 'INSERT INTO cast VALUES (%s,%s,%s,%s,%s)',
                 # UPDATE
                 'up_special': 'UPDATE special SET title=%s,sorttitle=%s,plot=%s WHERE file=%s AND bpath=%s',
                 # DELETE
                 'd_tvshows': 'DELETE FROM tvshows WHERE file=%s',
                 'd_movies': 'DELETE FROM movies WHERE file=%s',
                 'd_special': 'DELETE FROM special WHERE file=%s',
                 'd_special2': 'DELETE FROM special WHERE bpath=%s',
                 'd_art': 'DELETE FROM art WHERE file=%s',
                 'd_cast': 'DELETE FROM cast WHERE file=%s',
                 }
        return QUERY

    def checkout(self):
        return len(carList)
