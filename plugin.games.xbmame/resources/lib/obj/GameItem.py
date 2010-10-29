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

import re

from XMLHelper import XMLHelper
from DIPSwitch import DIPSwitch

class GameItem(object):

    def __init__(self, db, commands=(), id=0, xml=""):
        self._db=db
        self.dipswitches = []
        self.id=0
        self.romset=""
        self.driver=""
        self.cloneof=""
        self.romof=""
        self.isbios=""
        self.gamename=""
        self.gamecomment=""
        self.manufacturer=""
        self.year=""
        self.hasdisk=0
        self.isworking=0
        self.emul=0
        self.color=0
        self.graphic=0
        self.sound=0
        self.view=0
        self.rotate=0
        self.backdrops=0
        self.overlays=0
        self.bezels=0
        self.zoom=0
        self.have=0
        self.hasdips=False

        if id:self._fromDB(id)
        if xml:self._fromXML(xml)

    def _fromDB(self, id):
        data = self._db.getGames("SELECT id, romset, driver, cloneof, romof, gamename, gamecomment, manufacturer, year, hasdisk, isworking, emul, color, graphic, sound, view, rotate, backdrops, overlays, bezels, zoom, hasdips, have FROM Games WHERE id=?", (id,))[0]
        self.id=data[0]
        self.romset=data[1]
        self.driver=data[2]
        self.cloneof=data[3]
        self.romof=data[4]
        self.gamename=data[5]
        self.gamecomment=data[6]
        self.manufacturer=data[7]
        self.year=data[8]
        self.hasdisk=bool(data[9])
        self.isworking=bool(data[10])
        self.emul=bool(data[11])
        self.color=bool(data[12])
        self.graphic=bool(data[13])
        self.sound=bool(data[14])
        self.view=data[15]
        self.rotate=data[16]
        self.backdrops=data[17]
        self.overlays=data[18]
        self.bezels=data[19]
        self.zoom=data[20]
        self.hasdips=bool(data[21])
        self.have=bool(data[22])
        self.dipswitches = self._db.getGames("SELECT id FROM Dipswitches WHERE romset_id=? ORDER BY tag, mask",  (self.id,))

    def _fromXML(self, xml):
        self.id = ""
        self.romset = XMLHelper().getAttribute(xml, "game", "name")
        self.driver = XMLHelper().getAttribute(xml, "game", "sourcefile")
        self.cloneof = XMLHelper().getAttribute(xml,"game", "cloneof")
        self.romof = XMLHelper().getAttribute(xml,"game", "romof")
        self.isbios = int(XMLHelper().getAttribute(xml, "game", "isbios")!="")
        description = XMLHelper().getNodeValue(xml, "description")
        self.gamename = re.sub(" \(.*?\)", "", description)
        self.gamecomment = re.sub("[\(|\)]", "", description[len(self.gamename)+1:])
        self.year = XMLHelper().getNodeValue(xml, "year")
        if self.year=="":
            self.year="19??"
        self.hasdisk = int(XMLHelper().getAttribute(xml, "disk", "name")!="")
        self.isworking = int(XMLHelper().getAttribute(xml, "driver", "status")!="preliminary")
        self.emul = int(XMLHelper().getAttribute(xml, "driver", "emulation")=="good")
        self.color = int(XMLHelper().getAttribute(xml, "driver", "color")=="good")
        self.graphic = int(XMLHelper().getAttribute(xml, "driver", "graphic")=="good")
        self.sound = int(XMLHelper().getAttribute(xml, "driver", "sound")=="good")
        self.manufacturer = XMLHelper().getNodeValue(xml, "manufacturer")
        for dipswitch in XMLHelper().getNodes(xml, "dipswitch"):
            self.dipswitches.append(DIPSwitch(self._db, xml=dipswitch))
            self.hasdips=True
        del xml
        return self

    def writeDB(self):
        if not self.id:
            romset_id = self._db.execute("INSERT INTO Games VALUES(null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.romset, self.cloneof, self.romof, self.driver, self.gamename, self.gamecomment, self.manufacturer, self.year, self.isbios, self.hasdisk, self.isworking, self.emul, self.color, self.graphic, self.sound, self.hasdips, 0, 0, 1, 1, 1, 0, 0, 0))
            for dipswitch in self.dipswitches:
                dipswitch.writeDB(romset_id)
        else:
            self._db.execute("UPDATE Games SET view=?, rotate=?, backdrops=?, overlays=?, bezels=?, zoom=? WHERE ID=?", (self.view, self.rotate, self.backdrops, self.overlays, self.bezels, self.zoom, self.id))
