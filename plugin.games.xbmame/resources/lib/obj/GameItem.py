import re

from XMLHelper import XMLHelper
from DIPSwitch import DIPSwitch
from BiosSet import BiosSet

class GameItem(object):

    def __init__(self, db, id=0, romset="", xml=""):
        self._db=db
        self.dipswitches = []
        self.id=0
        self.romset=""
        self.driver=""
        self.cloneof=""
        self.romof=""
        self.isbios=""
        self.biosset=""
        self.biossets = []
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
        if id:self._fromDB(id=id)
        if romset:self._fromDB(romset=romset)
        if xml:self._fromXML(xml)

    def _fromDB(self, id=0, romset=""):
        if id:
            data = self._db.getGames("SELECT id, romset, driver, cloneof, romof, biosset, gamename, gamecomment, manufacturer, year, isbios, hasdisk, isworking, emul, color, graphic, sound, view, rotate, backdrops, overlays, bezels, zoom, hasdips, have FROM Games WHERE id=?", (id,))[0]
        else:
            data = self._db.getGames("SELECT id, romset, driver, cloneof, romof, biosset, gamename, gamecomment, manufacturer, year, isbios, hasdisk, isworking, emul, color, graphic, sound, view, rotate, backdrops, overlays, bezels, zoom, hasdips, have FROM Games WHERE romset=?", (romset,))[0]
        self.id=data[0]
        self.romset=data[1]
        self.driver=data[2]
        self.cloneof=data[3]
        self.romof=data[4]
        if self.romof:
            parent = GameItem(self._db, romset=self.romof)
            self.biossets=parent.biossets
        self.biosset=data[5]
        self.gamename=data[6]
        self.gamecomment=data[7]
        self.manufacturer=data[8]
        self.year=data[9]
        self.isbios=data[10]
        if self.isbios:
            print "looking for biossets for %s" % self.romset
            self.biossets=BiosSet(self._db).getByRomsetID(self.id)
        self.hasdisk=bool(data[11])
        self.isworking=bool(data[12])
        self.emul=bool(data[13])
        self.color=bool(data[14])
        self.graphic=bool(data[15])
        self.sound=bool(data[16])
        self.view=data[17]
        self.rotate=data[18]
        self.backdrops=data[19]
        self.overlays=data[20]
        self.bezels=data[21]
        self.zoom=data[22]
        self.hasdips=bool(data[23])
        self.have=bool(data[24])
        self.dipswitches = self._db.getGames("SELECT id FROM Dipswitches WHERE romset_id=? ORDER BY tag, mask",  (self.id,))

    def _fromXML(self, xml):
        self.id = ""
        self.romset = XMLHelper().getAttribute(xml, "game", "name")
        self.driver = XMLHelper().getAttribute(xml, "game", "sourcefile")
        self.cloneof = XMLHelper().getAttribute(xml,"game", "cloneof")
        self.romof = XMLHelper().getAttribute(xml,"game", "romof")
        self.isbios = int(XMLHelper().getAttribute(xml, "game", "isbios")!="")
        for biosset in XMLHelper().getNodes(xml, "biosset"):
            self.biossets.append(
                BiosSet(self._db, name=XMLHelper().getAttribute(biosset, "biosset", "name"),
                    description=XMLHelper().getAttribute(biosset, "biosset", "description")))
            if XMLHelper().getAttribute(biosset, "biosset", "default"):
                self.biosset = XMLHelper().getAttribute(biosset, "biosset", "name")
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
            dipswitch = DIPSwitch(self._db, xml=dipswitch)
            if dipswitch.name!="Unused" and dipswitch.name!="Unknown":
                self.dipswitches.append(dipswitch)
                self.hasdips=True
        del xml
        return self

    def writeDB(self):
        if not self.id:
            romset_id = self._db.execute("INSERT INTO Games VALUES(null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.romset, self.cloneof, self.romof, self.biosset, self.driver, self.gamename, self.gamecomment, self.manufacturer, self.year, self.isbios, self.hasdisk, self.isworking, self.emul, self.color, self.graphic, self.sound, self.hasdips, 0, 0, 1, 1, 1, 0, self.have, 0))
            for biosset in self.biossets:
                biosset.setRomSetID(romset_id)
                biosset.writeDB()
            for dipswitch in self.dipswitches:
                dipswitch.writeDB(romset_id)
        else:
            self._db.execute("UPDATE Games SET biosset=?, view=?, rotate=?, backdrops=?, overlays=?, bezels=?, zoom=? WHERE ID=?", (self.biosset, self.view, self.rotate, self.backdrops, self.overlays, self.bezels, self.zoom, self.id))
