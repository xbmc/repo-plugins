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

class BiosSet(object):

    def __init__(self, db, romset_id=0, name="", description=""):
        self._db = db
        self.romset_id=romset_id
        self.name=name
        self.description=description

    def setRomSetID(self, romset_id):
        self.romset_id=romset_id

    def setName(self, name):
        self.name=name

    def setDescription(self, description):
        self.description=description

    def writeDB(self):
        self._db.execute("INSERT INTO BiosSets VALUES (null, ?, ?, ?)", (self.romset_id, self.name, self.description,))

    def getByName(self, name):
        try:
            data = self._db.Query("SELECT romset_id, name, description FROM BiosSets WHERE name=?", (name,))[0]
            item = BiosSet(self._db, data[0], data[1], data[2])
        except KeyError:
            item = BiosSet(self._db)
        return item

    def getByDescription(self, description):
        try:
            data = self._db.Query("SELECT romset_id, name, description FROM BiosSets WHERE description=?", (description,))[0]
            item = BiosSet(self._db, data[0], data[1], data[2])
        except KeyError:
            item = BiosSet(self._db)
        return item

    def getByRomsetID(self, romset_id):
        items = []
        data = self._db.Query("SELECT romset_id, name, description FROM BiosSets WHERE romset_id=?", (romset_id,))
        print "Biossets found:%s" % len(data)
        for dat in data:
            items.append(BiosSet(self._db, dat[0], dat[1], dat[2]))
        return items
