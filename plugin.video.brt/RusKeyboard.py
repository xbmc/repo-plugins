# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, os
addon = xbmcaddon.Addon(id='plugin.video.brt')
path = addon.getAddonInfo('path')

caps = 0
background = os.path.join(path, 'background.png')
lang1 = ["А","Б","В","Г","Д","Е","Ё","Ж","З","И","Й","К","Л","М","Н","О","П","Р","С","Т","У","Ф","Х","Ц","Ч","Ш","Щ","Ъ","Ы","Ь","Э","Ю","Я"]
lang2 = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","","","","","","",""]
lang3 = ["а","б","в","г","д","е","ё","ж","з","и","й","к","л","м","н","о","п","р","с","т","у","ф","х","ц","ч","ш","щ","ъ","ы","ь","э","ю","я"]
lang4 = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","","","","","","",""]
lang5 = ["1","2","3","4","5","6","7","8","9","0","","!",".",",","=","{","}","[","]",'"',"'",":","@","|","/","?","+","-","<",">","%","$","&"]
xy = 54
yx = 50
class Key(xbmcgui.WindowDialog):
    templng = 1
    text = ""
    d = False
    urlpath = ""
    type=""
    tempcaps = False
    def __init__ (self):
        
        self.setCoordinateResolution(6)
        self.confirmed = False
        self.back = xbmcgui.ControlImage(120,120,400,300,background)
        self.addControl(self.back)
        self.a = xbmcgui.ControlButton(90 + xy,150 + yx,32,40,lang3[0])
        self.addControl(self.a)
        self.b = xbmcgui.ControlButton(122 + xy,150 + yx,32,40,lang3[1])
        self.addControl(self.b)
        self.c = xbmcgui.ControlButton(154 + xy,150 + yx,32,40,lang3[2])
        self.addControl(self.c)
        self.d = xbmcgui.ControlButton(186 + xy,150 + yx,32,40,lang3[3])
        self.addControl(self.d)
        self.e = xbmcgui.ControlButton(218 + xy,150 + yx,32,40,lang3[4])
        self.addControl(self.e)
        self.f = xbmcgui.ControlButton(250 + xy,150 + yx,32,40,lang3[5])
        self.addControl(self.f)
        self.g = xbmcgui.ControlButton(282 + xy,150 + yx,32,40,lang3[6])
        self.addControl(self.g)
        self.h = xbmcgui.ControlButton(314 + xy,150 + yx,32,40,lang3[7])
        self.addControl(self.h)
        self.i = xbmcgui.ControlButton(346 + xy,150 + yx,32,40,lang3[8])
        self.addControl(self.i)
        self.j = xbmcgui.ControlButton(378 + xy,150 + yx,32,40,lang3[9])
        self.addControl(self.j)
        self.k = xbmcgui.ControlButton(410 + xy,150 + yx,32,40,lang3[10])
        self.addControl(self.k)
        self.l = xbmcgui.ControlButton(90 + xy,190 + yx,32,40,lang3[11])
        self.addControl(self.l)
        self.m = xbmcgui.ControlButton(122 + xy,190 + yx,32,40,lang3[12])
        self.addControl(self.m)
        self.n = xbmcgui.ControlButton(154 + xy,190 + yx,32,40,lang3[13])
        self.addControl(self.n)
        self.o = xbmcgui.ControlButton(186 + xy,190 + yx,32,40,lang3[14])
        self.addControl(self.o)
        self.p = xbmcgui.ControlButton(218 + xy,190 + yx,32,40,lang3[15])
        self.addControl(self.p)
        self.q = xbmcgui.ControlButton(250 + xy,190 + yx,32,40,lang3[16])
        self.addControl(self.q)
        self.r = xbmcgui.ControlButton(282 + xy,190 + yx,32,40,lang3[17])
        self.addControl(self.r)
        self.s = xbmcgui.ControlButton(314 + xy,190 + yx,32,40,lang3[18])
        self.addControl(self.s)
        self.t = xbmcgui.ControlButton(346 + xy,190 + yx,32,40,lang3[19])
        self.addControl(self.t)
        self.u = xbmcgui.ControlButton(378 + xy,190 + yx,32,40,lang3[20])
        self.addControl(self.u)
        self.v = xbmcgui.ControlButton(410 + xy,190 + yx,32,40,lang3[21])
        self.addControl(self.v)
        self.w = xbmcgui.ControlButton(90 + xy,230 + yx,32,40,lang3[22])
        self.addControl(self.w)
        self.x = xbmcgui.ControlButton(122 + xy,230 + yx,32,40,lang3[23])
        self.addControl(self.x)
        self.y = xbmcgui.ControlButton(154 + xy,230 + yx,32,40,lang3[24])
        self.addControl(self.y)
        self.z = xbmcgui.ControlButton(186 + xy,230 + yx,32,40,lang3[25])
        self.addControl(self.z)
        self.a1 = xbmcgui.ControlButton(218 + xy,230 + yx,32,40,lang3[26])
        self.addControl(self.a1)
        self.b1 = xbmcgui.ControlButton(250 + xy,230 + yx,32,40,lang3[27])
        self.addControl(self.b1)
        self.c1 = xbmcgui.ControlButton(282 + xy,230 + yx,32,40,lang3[28])
        self.addControl(self.c1)
        self.d1 = xbmcgui.ControlButton(314 + xy,230 + yx,32,40,lang3[29])
        self.addControl(self.d1)
        self.e1 = xbmcgui.ControlButton(346 + xy,230 + yx,32,40,lang3[30])
        self.addControl(self.e1)
        self.f1 = xbmcgui.ControlButton(378 + xy,230 + yx,32,40,lang3[31])
        self.addControl(self.f1)
        self.g1 = xbmcgui.ControlButton(410 + xy,230 + yx,32,40,lang3[32])
        self.addControl(self.g1)
        self.caps = xbmcgui.ControlButton(90 + xy,270 + yx,78,40,"Caps Lock")
        self.addControl(self.caps)
        self.space = xbmcgui.ControlButton(168 + xy,270 + yx,98,40,"Space")
        self.addControl(self.space)
        self.backspace = xbmcgui.ControlButton(266 + xy,270 + yx,98,40,"Back Space")
        self.addControl(self.backspace)
        self.lng = xbmcgui.ControlButton(364 + xy,270 + yx,78,40,"ENG")
        self.addControl(self.lng)
        self.ok = xbmcgui.ControlButton(286 + xy,315 + yx,78,40,"OK")
        self.addControl(self.ok)
        self.cancel = xbmcgui.ControlButton(364 + xy,315 + yx,78,40,"Отмена")
        self.addControl(self.cancel)
        self.textbox = xbmcgui.ControlTextBox(155,150,330,30,textColor = '0xFFFFFFFF')
        self.addControl(self.textbox)
        
        self.a.controlRight(self.b)
        self.b.controlRight(self.c)
        self.c.controlRight(self.d)
        self.d.controlRight(self.e)
        self.e.controlRight(self.f)
        self.f.controlRight(self.g)
        self.g.controlRight(self.h)
        self.h.controlRight(self.i)
        self.i.controlRight(self.j)
        self.j.controlRight(self.k)
        
        self.l.controlRight(self.m)
        self.m.controlRight(self.n)
        self.n.controlRight(self.o)
        self.o.controlRight(self.p)
        self.p.controlRight(self.q)
        self.q.controlRight(self.r)
        self.r.controlRight(self.s)
        self.s.controlRight(self.t)
        self.t.controlRight(self.u)
        self.u.controlRight(self.v)
        
        self.w.controlRight(self.x)
        self.x.controlRight(self.y)
        self.y.controlRight(self.z)
        self.z.controlRight(self.a1)
        self.a1.controlRight(self.b1)
        self.b1.controlRight(self.c1)
        self.c1.controlRight(self.d1)
        self.d1.controlRight(self.e1)
        self.e1.controlRight(self.f1)
        self.f1.controlRight(self.g1)
        
        self.caps.controlRight(self.space)
        self.space.controlRight(self.backspace)
        self.backspace.controlRight(self.lng)
        self.ok.controlRight(self.cancel)
        
        
        self.b.controlLeft(self.a)
        self.c.controlLeft(self.b)
        self.d.controlLeft(self.c)
        self.e.controlLeft(self.d)
        self.f.controlLeft(self.e)
        self.g.controlLeft(self.f)
        self.h.controlLeft(self.g)
        self.i.controlLeft(self.h)
        self.j.controlLeft(self.i)
        self.k.controlLeft(self.j)
        
        self.m.controlLeft(self.l)
        self.n.controlLeft(self.m)
        self.o.controlLeft(self.n)
        self.p.controlLeft(self.o)
        self.q.controlLeft(self.p)
        self.r.controlLeft(self.q)
        self.s.controlLeft(self.r)
        self.t.controlLeft(self.s)
        self.u.controlLeft(self.t)
        self.v.controlLeft(self.u)
        
        self.x.controlLeft(self.w)
        self.y.controlLeft(self.x)
        self.z.controlLeft(self.y)
        self.a1.controlLeft(self.z)
        self.b1.controlLeft(self.a1)
        self.c1.controlLeft(self.b1)
        self.d1.controlLeft(self.c1)
        self.e1.controlLeft(self.d1)
        self.f1.controlLeft(self.e1)
        self.g1.controlLeft(self.f1)
        
        
        self.space.controlLeft(self.caps)
        self.backspace.controlLeft(self.space)
        self.lng.controlLeft(self.backspace)
        self.cancel.controlLeft(self.ok)
        
        self.a.controlDown(self.l)
        self.b.controlDown(self.m)
        self.c.controlDown(self.n)
        self.d.controlDown(self.o)
        self.e.controlDown(self.p)
        self.f.controlDown(self.q)
        self.g.controlDown(self.r)
        self.h.controlDown(self.s)
        self.i.controlDown(self.t)
        self.j.controlDown(self.u)
        self.k.controlDown(self.v)
        
        self.l.controlDown(self.w)
        self.m.controlDown(self.x)
        self.n.controlDown(self.y)
        self.o.controlDown(self.z)
        self.p.controlDown(self.a1)
        self.q.controlDown(self.b1)
        self.r.controlDown(self.c1)
        self.s.controlDown(self.d1)
        self.t.controlDown(self.e1)
        self.u.controlDown(self.f1)
        self.v.controlDown(self.g1)
        
        self.w.controlDown(self.caps)
        self.x.controlDown(self.caps)
        self.y.controlDown(self.space)
        self.z.controlDown(self.space)
        self.a1.controlDown(self.space)
        self.b1.controlDown(self.backspace)
        self.c1.controlDown(self.backspace)
        self.d1.controlDown(self.backspace)
        self.e1.controlDown(self.backspace)
        self.f1.controlDown(self.lng)
        self.g1.controlDown(self.lng)
        self.caps.controlDown(self.ok)
        self.space.controlDown(self.ok)
        self.backspace.controlDown(self.ok)
        self.lng.controlDown(self.ok)
        
        
        self.l.controlUp(self.a)
        self.m.controlUp(self.b)
        self.n.controlUp(self.c)
        self.o.controlUp(self.d)
        self.p.controlUp(self.e)
        self.q.controlUp(self.f)
        self.r.controlUp(self.g)
        self.s.controlUp(self.h)
        self.t.controlUp(self.i)
        self.u.controlUp(self.j)
        self.v.controlUp(self.k)
        
        self.w.controlUp(self.l)
        self.x.controlUp(self.m)
        self.y.controlUp(self.n)
        self.z.controlUp(self.o)
        self.a1.controlUp(self.p)
        self.b1.controlUp(self.q)
        self.c1.controlUp(self.r)
        self.d1.controlUp(self.s)
        self.e1.controlUp(self.t)
        self.f1.controlUp(self.u)
        self.g1.controlUp(self.v)
        
        self.caps.controlUp(self.x)
        self.space.controlUp(self.y)
        self.backspace.controlUp(self.c1)
        self.lng.controlUp(self.g1)
        self.ok.controlUp(self.backspace)
        self.cancel.controlUp(self.lng)
        
        self.textbox.setText("|")
        self.setFocus(self.a)
    def onControl(self,c):
        if self.ok == c:
            t = self.text
            t = t.encode('utf-8')
            xbmc.executebuiltin('XBMC.Container.Update("'+ self.urlpath + '?mode=search1&page=1&type=' + self.type + '&keyword=' + t + '")')
            self.close()
        elif self.cancel ==c:
            self.close()
        elif self.backspace == c:
            self.text = self.text[:-1]
            self.textbox.setText(self.text + "|")    
        elif self.caps == c:
            if self.templng == 1:
                self.change(lang1)
                self.templng = 4
                self.tempcaps = True
            elif  self.templng == 2:   
                self.change(lang2)
                self.templng = 5
                self.tempcaps = True
            elif self.templng == 4:
                self.change(lang3)
                self.templng = 1
                self.tempcaps = False
            elif self.templng == 5:
                self.change(lang4)
                self.templng = 2 
                self.tempcaps = False           
        elif self.lng == c:
            
            if self.templng == 1:
                self.change(lang4)
                self.templng = 2
                self.lng.setLabel("123")
            elif self.templng == 2:
                self.change(lang5)
                self.templng = 3
                self.caps.setEnabled(False)
                self.lng.setLabel("RUS")
            elif self.templng == 3:
                if self.tempcaps == True:
                    self.change(lang1)
                    self.templng = 4
                    self.lng.setLabel("ENG")
                    self.caps.setEnabled(True)
                else:
                    self.change(lang3)
                    self.templng = 1
                    self.lng.setLabel("ENG")
                    self.caps.setEnabled(True)
            elif self.templng == 4:
                self.change(lang2)
                self.templng = 2
                self.lng.setLabel("123")
                       
        elif self.space ==c:
            if len(self.text) <= 42:
                self.text = self.text + " "
                self.textbox.setText(self.text + "|")
                #self.text = self.text[:1]        
        else:
            if len(self.text) <= 42:
                self.text = self.text + c.getLabel()
                self.textbox.setText(self.text + "|")
                #self.text = self.text[:1]
    def change(self, tempmass):
        self.a.setLabel(tempmass[0])
        self.b.setLabel(tempmass[1])
        self.c.setLabel(tempmass[2])
        self.d.setLabel(tempmass[3])
        self.e.setLabel(tempmass[4])
        self.f.setLabel(tempmass[5])
        self.g.setLabel(tempmass[6])
        self.h.setLabel(tempmass[7])
        self.i.setLabel(tempmass[8])
        self.j.setLabel(tempmass[9])
        self.k.setLabel(tempmass[10])
        self.l.setLabel(tempmass[11])
        self.m.setLabel(tempmass[12])
        self.n.setLabel(tempmass[13])
        self.o.setLabel(tempmass[14])
        self.p.setLabel(tempmass[15])
        self.q.setLabel(tempmass[16])
        self.r.setLabel(tempmass[17])
        self.s.setLabel(tempmass[18])
        self.t.setLabel(tempmass[19])
        self.u.setLabel(tempmass[20])
        self.v.setLabel(tempmass[21])
        self.w.setLabel(tempmass[22])
        self.x.setLabel(tempmass[23])
        self.y.setLabel(tempmass[24])
        self.z.setLabel(tempmass[25])
        self.a1.setLabel(tempmass[26])
        self.b1.setLabel(tempmass[27])
        self.c1.setLabel(tempmass[28])
        self.d1.setLabel(tempmass[29])
        self.e1.setLabel(tempmass[30])
        self.f1.setLabel(tempmass[31])
        self.g1.setLabel(tempmass[32])


            
        