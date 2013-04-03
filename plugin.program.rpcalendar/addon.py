"""
    Plugin for Launching programs
"""

# -*- coding: UTF-8 -*-
# main imports
import calendar
import datetime
import sys
import os
import xbmc
import xbmcgui
import xbmcaddon

# plugin constants
__plugin__ = "rpcalendar"
__author__ = "RPiola"
__url__ = "http://pi.ilpiola.it/rpcalendar/"
__git_url__ = ""
__credits__ = ""
__version__ = "1.0.1"

class CalendarDialog(xbmcgui.WindowDialog):

    def __init__(self,m,y,nf):
        self.retval=0
        self.background=xbmcgui.ControlImage(0,0,self.getWidth(),self.getHeight(),os.path.join(addon.getAddonInfo('path'),'resources','media','background.jpg'),colorDiffuse='0xff777777')
        self.addControl(self.background)
        self.titlelabel1=xbmcgui.ControlLabel(70,70,self.getWidth()-40,30,addon.getLocalizedString(id=30000),textColor='0xffffffff',alignment=6)
        self.addControl(self.titlelabel1)
        self.titlelabel2=xbmcgui.ControlLabel(70,110,self.getWidth()-40,30,str(m)+'/'+str(y),textColor='0xffffffff',alignment=6)
        self.addControl(self.titlelabel2)
        self.weeklabel=xbmcgui.ControlLabel(70+(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30002),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weeklabel)
        self.weekday1=xbmcgui.ControlLabel(70+2*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30011),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday1)
        self.weekday2=xbmcgui.ControlLabel(70+3*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30012),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday2)
        self.weekday3=xbmcgui.ControlLabel(70+4*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30013),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday3)
        self.weekday4=xbmcgui.ControlLabel(70+5*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30014),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday4)
        self.weekday5=xbmcgui.ControlLabel(70+6*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30015),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday5)
        self.weekday6=xbmcgui.ControlLabel(70+7*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30016),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday6)
        self.weekday7=xbmcgui.ControlLabel(70+8*(self.getWidth()-40)/10,150,100,30,addon.getLocalizedString(id=30017),textColor='0xffc0c0ff',alignment=6)
        self.addControl(self.weekday7)
        self.cal=calendar.Calendar(0)
        self.rowno=0
        self.dayno=0
        self.daylabels=[ 0 ] * 31
        self.weeklabels=[ 0 ] * 7
        for self.week in self.cal.monthdayscalendar(y,m):
            self.firstday=1
            self.columnno=0
            self.rowno=self.rowno+1
            for self.day in self.week:
                self.columnno=self.columnno+1
                if self.day != 0:
                   if self.firstday == 1:
                       self.thedate=datetime.date(y,m,self.day)
                       self.weeklabels[self.rowno]=xbmcgui.ControlLabel(70+(self.getWidth()-40)/10,150+self.rowno*30,100,30,str(self.thedate.isocalendar()[1]),textColor='0xffc0c0ff',alignment=6)
                       self.addControl(self.weeklabels[self.rowno])
                       self.firstday=0
                   if m==currentmonth and y==currentyear and self.day==currentday:
                       self.tc='0xffff0000'
                   else:
                       self.tc='0xffffffff'
                   self.daylabels[self.dayno]=xbmcgui.ControlLabel(70+(self.columnno+1)*(self.getWidth()-40)/10,150+self.rowno*30,100,30,str(self.day),textColor=self.tc,alignment=6)
                   self.addControl(self.daylabels[self.dayno])
                   self.dayno=self.dayno+1
        self.buttonok=xbmcgui.ControlButton(self.getWidth()/2-100,self.getHeight()-80,200,30,addon.getLocalizedString(id=30003),alignment=6)
        self.addControl(self.buttonok)
        self.buttonprev=xbmcgui.ControlButton(self.getWidth()/2-350,self.getHeight()-80,200,30,addon.getLocalizedString(id=30004),alignment=6)
        self.addControl(self.buttonprev)
        self.buttonnext=xbmcgui.ControlButton(self.getWidth()/2+150,self.getHeight()-80,200,30,addon.getLocalizedString(id=30005),alignment=6)
        self.addControl(self.buttonnext)
        self.buttonprev.controlRight(self.buttonok)
        self.buttonok.controlLeft(self.buttonprev)
        self.buttonok.controlRight(self.buttonnext)
        self.buttonnext.controlLeft(self.buttonok)
        if nf == -1:
            self.setFocus(self.buttonprev)
        elif nf == 1:
            self.setFocus(self.buttonnext)
        else:
            self.setFocus(self.buttonok)

    def onAction(self, action):
        # action 7 (OK) will be intercepted by onclick; action 10 is standard back, 92 is the return key on my sony tv
        #print('onAction called on action '+str(int(action.getId())))
        if action == 10 or action == 92:
            self.retval=0
            self.close()

    def onControl(self, controlID):
        #print('onClick called on control '+str(controlID.getId()))
        if controlID == self.buttonok:
            self.retval=0
            self.close()
        elif controlID == self.buttonprev:
            self.retval=-1
            self.close()
        elif controlID == self.buttonnext:
            self.retval=1
            self.close()

addon = xbmcaddon.Addon(id='plugin.program.rpcalendar')
finished=0
nextfocus=0
today = datetime.datetime.today()
currentday=int(today.strftime('%d'))
currentmonth=int(today.strftime('%m'))
month=currentmonth
currentyear=int(today.strftime('%Y'))
year=currentyear
while finished == 0:
    dialog=CalendarDialog(month,year,nextfocus)
    dialog.doModal()
    if dialog.retval == 0:
        finished = 1
    elif dialog.retval == 1:
        month = month+1
        if month == 13:
            month = 1
            year = year + 1
        nextfocus=1
    elif dialog.retval == -1:
        month = month-1
        if month == 0:
            month = 12
            year = year - 1
        nextfocus=-1
    del dialog
del addon
