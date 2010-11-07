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

import urllib
import xbmcgui
import xbmcaddon

CONTROL_TITLE = 20
CONTROL_OK = 10
CONTROL_MENU = 30501
CONTROL_TEXTBOX = 30502
CONTROL_RUN = 30503
CONTROL_RELATED = 30504

class InfoDialog(xbmcgui.WindowXMLDialog):

    GAME_RELATED = 11
    GAME_SETTINGS = 12
    GAME_INFO = 13
    GAME_EXECUTE = 14

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.pluginid = kwargs["plugin_id"]
        self.__language__ =  xbmcaddon.Addon(self.pluginid).getLocalizedString
        self.titlebox = None
        self.textbox = None
        self.menu = None
        self.related = ""
        self.notext = True
        self.game = kwargs["game"]
        self.prevmenu = None
        self.IDCard = ""
        self.command=""
        self.doModal()

    def onInit(self):
        self.titlebox = self.getControl(CONTROL_TITLE)
        self.textbox = self.getControl(CONTROL_TEXTBOX)
        self.menu = self.getControl(CONTROL_MENU)
        self.titlebox.setLabel(self.game.gamename)

        self.related = self.game.info.games

        self.getControl(CONTROL_RUN).setLabel(self.__language__(CONTROL_RUN))
        self.getControl(CONTROL_RUN).setEnabled(self.game.have)
        self.getControl(CONTROL_RELATED).setLabel(self.__language__(CONTROL_RELATED))
        self.getControl(CONTROL_RELATED).setEnabled(len(self.related)>0)

        self.IDCard += self.addInfo(self.game.gamename, self.__language__(30550))
        self.IDCard += self.addInfo(self.game.manufacturer, self.__language__(30551))
        self.IDCard += self.addInfo(self.game.year, self.__language__(30552))
        self.IDCard += self.addInfo(self.game.info.levels, self.__language__(30553))
        self.IDCard += self.addInfo(self.game.info.otheremu , self.__language__(30554), True)
        self.IDCard += self.addInfo(self.game.info.romsetinfo, self.__language__(30555))
        self.IDCard += self.addInfo(self.game.history.sources, self.__language__(30556), True)

        self.addMenu(self.IDCard, self.__language__(30557))
        self.addMenu(self.game.history.bio, self.__language__(30558))
        self.addMenu(self.game.history.trivia, self.__language__(30559))
        self.addMenu(self.game.history.technical, self.__language__(30560))
        self.addMenu(self.game.history.scoring, self.__language__(30561))
        self.addMenu(self.game.history.tips, self.__language__(30562))
        self.addMenu(self.game.info.testmode, self.__language__(30563))
        self.addMenu(self.game.info.setup, self.__language__(30564))
        self.addMenu(self.game.history.updates, self.__language__(30565))
        self.addMenu(self.game.info.wip, self.__language__(30566))
        self.addMenu(self.game.info.todo, self.__language__(30567))
        self.addMenu(self.game.info.bugs, self.__language__(30568))
        self.addMenu(self.game.info.note,self.__language__(30569))
        self.addMenu(self.game.history.series, self.__language__(30570))
        self.addMenu(self.game.history.staff, self.__language__(30571))
        self.addMenu(self.game.history.ports, self.__language__(30572))

    def addInfo(self, info, label, ret=False):
        if info==None:info = ""
        if info:
            if ret:
                return "%s :[CR]%s[CR][CR]" % (label, info)
            else:
                return "%s : %s[CR][CR]" % (label, info)
        else: return ""
    
    def addMenu(self, info, label):
        control = self.getControl(CONTROL_MENU)
        if info==None:info = ""
        if info:
            item = xbmcgui.ListItem(label)
            item.setProperty("text", info)
            control.addItem(item)
            if self.notext:
                self.textbox.setText(info)
                self.notext = False

    def onClick( self, controlId ):
        if controlId==CONTROL_RUN:
            self.close()
            self.command = "RunPlugin(\"plugin://%s?action=%s&item=%s\")" % (self.pluginid, self.GAME_EXECUTE, self.game.id)
        elif controlId==CONTROL_RELATED:
            self.close()
            self.command = "ReplaceWindow(10001, \"plugin://%s?action=%s&item=%s\")" % (self.pluginid, self.GAME_RELATED, urllib.quote(self.related))
        elif controlId==CONTROL_OK:
            self.close()
        else:
            pass

    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
	if action.getId()==10:
            self.close()
        if self.prevmenu!=self.menu.getSelectedItem():
            self.textbox.setText(self.menu.getSelectedItem().getProperty("text"))
            self.prevmenu = self.menu.getSelectedItem()
