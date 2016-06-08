# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import hashlib,json

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

from resources.lib.modules import control


def add(url):
    try:
        data = json.loads(url)

        dbid = hashlib.md5()
        for i in data['bookmark']: dbid.update(str(i))
        for i in data['action']: dbid.update(str(i))
        dbid = str(dbid.hexdigest())

        item = dict((k,v) for k, v in data.iteritems() if not k == 'bookmark')
        item = repr(item)

        control.makeFile(control.dataPath)
        dbcon = database.connect(control.bookmarksFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""dbid TEXT, ""item TEXT, ""UNIQUE(dbid)"");")
        dbcur.execute("DELETE FROM bookmark WHERE dbid = '%s'" % dbid)
        dbcur.execute("INSERT INTO bookmark Values (?, ?)", (dbid, item))
        dbcon.commit()
    except:
        pass


def delete(url):
    try:
        data = json.loads(url)

        dbid = hashlib.md5()
        for i in data['delbookmark']: dbid.update(str(i))
        for i in data['action']: dbid.update(str(i))
        dbid = str(dbid.hexdigest())

        control.makeFile(control.dataPath)
        dbcon = database.connect(control.bookmarksFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""dbid TEXT, ""item TEXT, ""UNIQUE(dbid)"");")
        dbcur.execute("DELETE FROM bookmark WHERE dbid = '%s'" % dbid)
        dbcon.commit()

        control.refresh()
    except:
        pass


def get():
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.bookmarksFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM bookmark")
        items = dbcur.fetchall()
        items = [eval(i[1].encode('utf-8')) for i in items]
        return items
    except:
        pass


