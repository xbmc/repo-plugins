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

class InfoFile(object):

    def __init__(self, db, path=""):
        self._db = db
        self.createTable()
        datpath1 = os.path.join(path, "mameinfo.dat")
        datpath2 = os.path.join(path, "inp", "mameinfo.dat")
        data = ""
        if path:
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
            InfoItem(self._db, data=item).writeDB()
        self._db.commit()

    def dropTable(self):
        self._db.dropTable("MameInfo")

    def createTable(self):
        if not self._db.tableExists("MameInfo"):
            self._db.execute("CREATE TABLE MameInfo (id INTEGER PRIMARY KEY, testmode TEXT, note TEXT, setup TEXT, levels TEXT, romsetinfo TEXT, todo TEXT, bugs TEXT, wip TEXT, otheremu TEXT, games TEXT, driver BOOL, samples BOOL, artwork BOOL)")

class InfoItem(object):

    def __init__(self, db, data="", id=""):
        self._db = db
        self.romset=""
        self.testmode=""
        self.note=""
        self.setup=""
        self.levels=""
        self.romsetinfo=""
        self.todo=""
        self.bugs=""
        self.wip=""
        self.otheremu=""
        self.games=""
        self.driver = False
        self.samples = False
        self.artwork = False
        if data:self.fromData(data)
        elif id:self.fromDB(id)

    def writeDB(self):
        id = self._db.execute("INSERT INTO MameInfo VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.testmode, self.note, self.setup, self.levels, self.romsetinfo, self.todo,
            self.bugs, self.wip, self.otheremu, self.games, self.driver, self.samples, self.artwork,))
        self._db.execute("UPDATE Games SET info=? WHERE romset=? or romof=?", (id, self.romset, self.romset))

    def fromDB(self, id):
        sql = "SELECT testmode, note, setup, levels, romsetinfo, todo, bugs, wip, otheremu, games, driver, samples, artwork FROM MameInfo WHERE id=?"
        results = self._db.Query(sql, (id,))
        for data in results:
            self.testmode=data[0]
            self.note=data[1]
            self.setup=data[2]
            self.levels=data[3]
            self.romsetinfo=data[4]
            self.todo=data[5]
            self.bugs=data[6]
            self.wip=data[7]
            self.otheremu=data[8]
            self.games=data[9]
            self.driver=data[10]
            self.samples=data[11]
            self.artwork=data[12]

    def fromData(self, data):
        try:
            self.romset = re.findall("\$info=(.*?)&&", data)[0].strip()
        except IndexError:
            pass
        try:
            self.testmode = re.findall("TEST MODE:(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip()
        except IndexError:
            pass
        try:
            self.note = re.findall("NOTE:(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip()
        except IndexError:
            pass
        try:
            self.setup = re.findall("SETUP:(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip()
        except IndexError:
            pass
        try:
            self.levels = re.findall("LEVELS:(.*?)&&&&", data)[0].strip()
        except IndexError:
            pass
        try:
            self.romsetinfo = re.findall("Romset:(.*?)&&&&", data)[0].strip()
        except IndexError:
            pass
        self.driver = bool(re.search("(\$drv)", data))
        self.samples = bool(re.search("(Samples required)", data))
        self.artwork = bool(re.search("(Artwork available)", data))
        try:
            self.todo = re.findall("TODO:&&&&(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip().replace("* ", "")
        except IndexError:
            pass
        try:
            self.bugs = re.findall("Bugs:&&&&(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip().replace("- ", "")
        except IndexError:
            pass
        try:
            self.wip = re.findall("WIP:&&&&(.*?)&&&&&&", data)[0].replace("&&&&", "\n").strip().replace("- ", "")
        except IndexError:
            pass
        try:
            self.otheremu = re.findall("Other Emulators:&&&&(.*?)&&&&&&", data)[0].replace("&&&&", "\n").replace("* ", "").strip()
        except IndexError:
            pass
        try:
            relatedgames = re.findall("Recommended Games.*?:&&&&(.*?)&&&&&&", data)
            for games in relatedgames:
                self.games += re.sub(".\((.*?)\)", "", games.replace("&&&&", ",").strip())
        except IndexError:
            pass

