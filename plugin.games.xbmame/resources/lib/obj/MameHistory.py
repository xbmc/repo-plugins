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

import os
import re

class HistoryFile(object):

    def __init__(self, db, path=""):
        self._db = db
        self.createTable()
        data = ""
        if path:
            datpath1 = os.path.join(path, "history.dat")
            datpath2 = os.path.join(path, "inp", "history.dat")
            if os.path.exists(datpath1):
                file = open(datpath1)
                data = file.read()
                file.close()
            elif os.path.exists(datpath2):
                file = open(datpath2)
                data = file.read()
                file.close()
        self.data = data.decode("iso-8859-1")

    def parse(self):
        self.dropTable()
        self.createTable()
        data = re.sub("\r\n", "&&", self.data)
        items = re.findall("(\$info=.*?\$end)", data , re.S+re.M)
        for item in items:
            HistoryItem(self._db, data=item).writeDB()
        self._db.commit()

    def dropTable(self):
        self._db.dropTable("MameHistory")

    def createTable(self):
        if not self._db.tableExists("MameHistory"):
            self._db.execute("CREATE TABLE MameHistory (id INTEGER PRIMARY KEY, bio TEXT, technical TEXT, trivia TEXT, scoring TEXT, updates TEXT, tips TEXT, series TEXT, staff TEXT, ports TEXT, sources TEXT)")

class HistoryItem(object):

    def __init__(self, db, data="", id=0):
        self._db = db
        self.romsets=""
        self.bio=""
        self.trivia=""
        self.technical=""
        self.scoring=""
        self.updates=""
        self.tips=""
        self.series=""
        self.staff=""
        self.ports=""
        self.sources = ""
        if data:self.fromData(data)
        elif id:self.fromDB(id)

    def writeDB(self):
        id = self._db.execute("INSERT INTO MameHistory VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.bio, self.technical, self.trivia, self.scoring, self.updates, self.tips,
            self.series, self.staff, self.ports, self.sources,))
        self._db.execute("UPDATE Games SET history=? WHERE romset IN (%s)" % self.romsets, (id,))

    def fromData(self, data):
        try:
            romsets = re.findall("\$info=(.*?),&&", data)[0].strip().split(",")
            for romset in romsets:
                self.romsets += "'%s'," % romset
            self.romsets = self.romsets[0:len(self.romsets)-1]

        except IndexError:
            pass
        try:
            self.bio = re.findall("\$bio(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.technical = re.findall("- TECHNICAL -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.trivia = re.findall("- TRIVIA -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.scoring = re.findall("- SCORING -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.updates = re.findall("- UPDATES -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.tips = re.findall("- TIPS AND TRICKS -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.series = re.findall("- SERIES -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.staff = re.findall("- STAFF -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        try:
            self.ports = re.findall("- PORTS -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "").replace("* ", "")
        except IndexError:
            pass
        try:
            self.sources = re.findall("- SOURCES -(.*?)(\$end|- .* -)", data)[0][0].replace("&&&&", "\n").strip().replace("&&", "")
        except IndexError:
            pass
        return self

    def fromDB(self, id):
        sql = "SELECT bio, technical, trivia, scoring, updates, tips, series, staff, ports, sources FROM MameHistory WHERE id=?"
        results = self._db.Query(sql, (id,))
        for data in results:
            self.bio=data[0]
            self.technical=data[1]
            self.trivia=data[2]
            self.scoring=data[3]
            self.updates=data[4]
            self.tips=data[5]
            self.series=data[6]
            self.staff=data[7]
            self.ports=data[8]
            self.sources=data[9]
        return self

    def isEmpty(self):
        return not(self.bio or self.technical or self.trivia or self.scoring or\
        self.updates or self.tips or self.series or self.staff or self.ports or self.sources)
