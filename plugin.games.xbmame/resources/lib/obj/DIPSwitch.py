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

from XMLHelper import XMLHelper

class DIPSwitch(object):

    def __init__(self, db, id=0, xml=""):
        self._db=db
        self.id = 0
        self.romset_id = 0
        self.name = ""
        self.tag = ""
        self.mask = ""
        self.defvalue = 0
        self.value = 0
        self.values_by_name = {}
        self.values_by_value = {}
        if id:self._fromDB(id)
        if xml:self._fromXML(xml)

    def _fromDB(self, id):
        data = self._db.Query("SELECT id, romset_id, name, tag, mask, defvalue, value FROM Dipswitches WHERE id=?", (id,))[0]
        self.id=data[0]
        self.romset_id=data[1]
        self.name=data[2]
        self.tag=data[3]
        self.mask=data[4]
        self.defvalue=data[5]
        self.value=data[6]
        for data in self._db.Query("SELECT id, name, value FROM DipswitchesValues WHERE dipswitch_id=?", (self.id,)):
            self.values_by_name[data[1]] = data[2]
            self.values_by_value[data[2]] = data[1]

    def _fromXML(self, xml):
        self.name = XMLHelper().getAttribute(xml, "dipswitch", "name")
        self.tag = XMLHelper().getAttribute(xml, "dipswitch", "tag")
        self.mask = XMLHelper().getAttribute(xml, "dipswitch", "mask")
        self.value = 0
        for dipvalue in XMLHelper().getNodes(xml, "dipvalue"):
            name = XMLHelper().getAttribute(dipvalue, "dipvalue", "name")
            value = XMLHelper().getAttribute(dipvalue, "dipvalue", "value")
            self.values_by_name[name] = value
            self.values_by_value[value] = name
            if bool(XMLHelper().getAttribute(dipvalue, "dipvalue", "default")=="yes"):
                self.defvalue = value
                self.value = value
        del xml
        return self

    def writeDB(self, romset_id=0):
        if romset_id:
            dipswitch_id = self._db.execute("INSERT INTO Dipswitches VALUES(null, ?, ?, ?, ?, ?, ?)", (romset_id, self.name, self.tag, self.mask, self.value, self.value,))
            for key in self.values_by_name.keys():
                self._db.execute("INSERT INTO DipswitchesValues VALUES(null, ?, ?, ?)", (dipswitch_id,  self.values_by_name[key], key,))
        else:
            self._db.execute("UPDATE Dipswitches SET value=? WHERE id=?", (self.value,self.id,))
            self._db.commit()
