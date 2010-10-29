# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is plugin.games.xbmame.
#
# The Initial Developer of the Original Code is Olivier LODY aka Akira76.
# Portions created by the XBMC team are Copyright (C) 2003-2010 XBMC.
# All Rights Reserved.

from pysqlite2 import dbapi2 as sqlite

class DBHelper(object):

    _tables = [ "Games", "Dipswitches", "DipswitchesValues" ]

    def __init__(self, dbpath):
        self._db = sqlite.connect(dbpath)
        self._cursor = self._db.cursor()

    def commit(self):
        self.db.commit()

    def isEmpty(self):
        if self.getCount("main.sqlite_master")==0:
            return True
        else:
            rows = 0
            for t in self._tables:
                rows+=self.getCount(t)
            return (rows==0)

    def execute(self, sql, values=""):
        if values:
            self._cursor.execute(sql, values)
        else:
            self._cursor.execute(sql)
        return self._cursor.lastrowid

    def getCount(self, table):
        self._cursor.execute("SELECT count(*) as tblcount FROM %s" % table)
        return self._cursor.fetchone()[0]

    def commit(self):
        self._db.commit()

    def getGames(self, sql, values):
        self._cursor.execute(sql, values)
        results = self._cursor.fetchall()
        return results

    def getList(self, table, fields, criteria={}):
        filters=""
        for key in criteria.keys():
            filters+=" AND %s%s" % (key, criteria[key])
        fieldlist = ""
        for field in fields:
            fieldlist += ", %s" % field
        fieldlist = fieldlist[1:]

        sql = "SELECT %s FROM %s WHERE id>0 %s GROUP BY %s ORDER BY %s ASC" % (fieldlist, table, filters, fields[0], fields[0])
        return self.runQuery(sql)

    def getResult(self, table, field, id):
        return self.runQuery("SELECT %s FROM %s WHERE id=%s" % (field, table, id))[0]

    def getResults(self, table, field, id):
        return self.runQuery("SELECT %s FROM %s WHERE id=%s" % (field, table, id))

    def runQuery(self, sql, values=()):
        cursor = self._db.cursor()
        cursor.execute(sql, values)
        headers = [tuple[0] for tuple in cursor.description]
        results = cursor.fetchall()
        return self._getRows(headers, results)

    def _getRow(self, headers, results):
        for result in results:
            fields = {}
            for i in range(len(headers)):
                fields[headers[i]]=result[i]
        return fields

    def _getRows(self, headers, results):
        values = []
        for result in results:
            fields = {}
            for i in range(len(headers)):
                fields[headers[i]]=result[i]
            values.append(fields)
        return values

