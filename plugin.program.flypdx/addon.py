"""
    Fly PDX KODI Addon
    Copyright (C) 2016 Troy Scott

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime, io, math, os, re, sys, urllib2, urllib
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, xbmcplugin

#import rpdb2
#rpdb2.start_embedded_debugger('pw')

class FlightInfo:

    def __init__(self,ad,rs):
        # Create individual lists for flight table column data
        self.schcol = []
        self.aircol = []
        self.typcol = []
        self.adecol = []
        self.stscol = []
        self.fltcol = []
        self.gtecol = []
        self.bagcol = []
        xbmc.log(msg='Fly PDX: FlightInfo __init__')

    def fixGate(self,ad,rs):
        # Updates flight list in cases when gate information is missing
        self.pattern = r"(\D+\d+)"
        self.endalldet = 0
        self.inc = 6
        while self.endalldet == 0:
            if self.inc > len(ad):
                self.endalldet = 1
                break
            else:
                self.match = re.match(self.pattern,ad[self.inc])
                if not self.match:
                    ad.insert(self.inc,' ')
                self.inc += 8
        xbmc.log(msg='Fly PDX: fixGate()')

    def assignCol(self,ad,rs):
        # Assign individual lists for flight table column data
        self.i = iter(ad)
        for self.inc in range(0,len(ad),rs):
            self.schcol.append(self.i.next())
            self.aircol.append(self.i.next())
            self.typcol.append(self.i.next())
            self.adecol.append(self.i.next())
            self.stscol.append(self.i.next())
            self.fltcol.append(self.i.next())
            self.gtecol.append(self.i.next())
            self.bagcol.append(self.i.next())
        xbmc.log(msg='Fly PDX: assignCol()')

class FlightTableDialog(xbmcgui.WindowDialog):
    def __init__(self,setairline,setfilter,setdate,setdelay,setflightno,setadcity,ad,schcol,aircol,typcol,adecol,stscol,fltcol,gtecol,bagcol,nf,rs,sr,er,mr):
        self.retval = 0
        self.w = 1280
        self.h = 720

        self.today = datetime.datetime.today()
        self.cleantime=self.today.strftime('%c')
        # Background and titles
        self.background  = xbmcgui.ControlImage(0,0,self.w,self.h,os.path.join(addon.getAddonInfo('path'),'resources','media','background.jpg'),colorDiffuse='0xff777777')
        self.addControl(self.background)
        self.titlelabel1 = xbmcgui.ControlLabel(70,25,self.w-140,30,addon.getLocalizedString(id=30000),textColor='0xff00cc77',alignment=6)
        self.addControl(self.titlelabel1)
        self.titlelabel2 = xbmcgui.ControlLabel(70,50,self.w-140,30,self.cleantime,textColor='0xffffffff',alignment=6)
        self.addControl(self.titlelabel2)
        self.titlelabel3 = xbmcgui.ControlLabel(50,75,self.w-140,30,'['+addon.getLocalizedString(id=30008)+': '+setdate+']  ['+addon.getLocalizedString(id=30011)+': '+setairline+']  ['+addon.getLocalizedString(id=30041)+': '+setfilter+']   ['+addon.getLocalizedString(id=30062)+' '+setflightno+']   ['+addon.getLocalizedString(id=30009)+': '+setadcity+']',textColor='0xffffffff',alignment=6)
        self.addControl(self.titlelabel3)
        if setdelay == 'true':
           self.titlelabel4 = xbmcgui.ControlLabel(70,100,self.w-140,30,addon.getLocalizedString(id=30007),textColor='0xffff5555',alignment=6)
           self.addControl(self.titlelabel4)
        #self.debuglabel1 = xbmcgui.ControlLabel(50,100,self.w-140,30,'[ len(ad)='+str(len(ad))+', recstep='+str(rs)+', strrow='+str(sr)+', endrow='+str(er)+', maxrow='+str(mr)+' ]',textColor='0xffff0000',alignment=6)
        #self.addControl(self.debuglabel1)
        #self.debuglabel2 = xbmcgui.ControlLabel(50,125,self.w-140,30,'[ setairline='+sa+', setfilter='+sf+', setdelay='+sl+' ]',textColor='0xffff0000',alignment=6)
        #self.addControl(self.debuglabel2)

        # Column headings
        self.schedule     = xbmcgui.ControlLabel(50,150,100,30,addon.getLocalizedString(id=30002),textColor='0xffc0c0ff')
        self.airline      = xbmcgui.ControlLabel(190,150,100,30,addon.getLocalizedString(id=30011),textColor='0xffc0c0ff')
        self.type         = xbmcgui.ControlLabel(315,150,100,30,addon.getLocalizedString(id=30012),textColor='0xffc0c0ff')
        self.arrivedepart = xbmcgui.ControlLabel(440,150,300,30,addon.getLocalizedString(id=30013),textColor='0xffc0c0ff')
        self.status       = xbmcgui.ControlLabel(815,150,100,30,addon.getLocalizedString(id=30014),textColor='0xffc0c0ff')
        self.flight       = xbmcgui.ControlLabel(940,150,100,30,addon.getLocalizedString(id=30015),textColor='0xffc0c0ff')
        self.gate         = xbmcgui.ControlLabel(1035,150,100,30,addon.getLocalizedString(id=30016),textColor='0xffc0c0ff')
        self.bag          = xbmcgui.ControlLabel(1140,150,200,30,addon.getLocalizedString(id=30017),textColor='0xffc0c0ff')
        self.addControl(self.schedule)
        self.addControl(self.airline)
        self.addControl(self.type)
        self.addControl(self.arrivedepart)
        self.addControl(self.status)
        self.addControl(self.flight)
        self.addControl(self.gate)
        self.addControl(self.bag)

        # Column data
        self.schlst = xbmcgui.ControlList(10,200,350,500)   # Schedule
        self.airlst = xbmcgui.ControlList(150,200,350,500)  # Airline
        self.typlst = xbmcgui.ControlList(275,200,350,500)  # Type
        self.adelst = xbmcgui.ControlList(400,200,500,500)  # Arriving-Departing
        self.stslst = xbmcgui.ControlList(775,200,350,500)  # Status
        self.fltlst = xbmcgui.ControlList(900,200,250,500)  # Flight#
        self.gtelst = xbmcgui.ControlList(1000,200,250,500) # Gate
        self.baglst = xbmcgui.ControlList(1100,200,250,500) # Bag Carousel
        self.addControl(self.schlst)
        self.addControl(self.airlst)
        self.addControl(self.typlst)
        self.addControl(self.adelst)
        self.addControl(self.stslst)
        self.addControl(self.fltlst)
        self.addControl(self.gtelst)
        self.addControl(self.baglst)

        # Populate table columns if flight information is available
        if len(ad) == 0:
            self.noflts    = xbmcgui.ControlLabel(300,200,750,30,addon.getLocalizedString(id=30006),textColor='0xffff5555')
            self.addControl(self.noflts)
        else:
            # Populate display lists with column data
            self.schlst.addItems(schcol[sr:er])
            self.airlst.addItems(aircol[sr:er])
            self.typlst.addItems(typcol[sr:er])
            self.adelst.addItems(adecol[sr:er])
            self.stslst.addItems(stscol[sr:er])
            self.fltlst.addItems(fltcol[sr:er])
            self.gtelst.addItems(gtecol[sr:er])
            self.baglst.addItems(bagcol[sr:er])

        # Navigation buttons
        self.buttonprev=xbmcgui.ControlButton(self.w/2-500,self.h-80,200,30,addon.getLocalizedString(id=30004),alignment=6)
        self.addControl(self.buttonprev)
        self.buttonnext=xbmcgui.ControlButton(self.w/2-250,self.h-80,200,30,addon.getLocalizedString(id=30005),alignment=6)
        self.addControl(self.buttonnext)
        self.buttonset=xbmcgui.ControlButton(self.w/2+0,self.h-80,200,30,addon.getLocalizedString(id=30010),alignment=6)
        self.addControl(self.buttonset)
        self.buttonok=xbmcgui.ControlButton(self.w/2+250,self.h-80,200,30,addon.getLocalizedString(id=30003),alignment=6)
        self.addControl(self.buttonok)
        self.buttonprev.controlRight(self.buttonnext)
        self.buttonnext.controlLeft(self.buttonprev)
        self.buttonnext.controlRight(self.buttonset)
        self.buttonset.controlLeft(self.buttonnext)
        self.buttonset.controlRight(self.buttonok)
        self.buttonok.controlLeft(self.buttonset)

        if nf == -1:
            self.setFocus(self.buttonprev)
        elif nf == 1:
            self.setFocus(self.buttonnext)
        else:
            self.setFocus(self.buttonok)

    def onAction(self, action):
        if action == 10 or action == 92:
            self.retval=0
            self.close()

    def onControl(self, controlID):
        self.schlst.reset()
        self.airlst.reset()
        self.typlst.reset()
        self.adelst.reset()
        self.stslst.reset()
        self.fltlst.reset()
        self.gtelst.reset()
        self.baglst.reset()
        if controlID == self.buttonok:
            self.retval=0
            self.close()
        elif controlID == self.buttonprev:
            self.retval=-1
            self.close()
        elif controlID == self.buttonnext:
            self.retval=1
            self.close()
        elif controlID == self.buttonset:
            self.retval=2
            self.close()

def setAircode(setairline):
    if setairline == 'All':          aircode = ''
    elif setairline == 'Air Canada':          aircode = 'Airline=AC'
    elif setairline == 'Alaska Airlines':     aircode = 'Airline=AS'
    elif setairline == 'American Airlines':   aircode = 'Airline=AA'
    elif setairline == 'Condor':              aircode = 'Airline=DE'
    elif setairline == 'Delta':               aircode = 'Airline=DL'
    elif setairline == 'Frontier':            aircode = 'Airline=F9'
    elif setairline == 'Hawaiian Airlines':   aircode = 'Airline=HA'
    elif setairline == 'Icelandair':          aircode = 'Airline=FI'
    elif setairline == 'jetBlue':             aircode = 'Airline=B6'
    elif setairline == 'PenAir':              aircode = 'Airline=KS'
    elif setairline == 'SeaPort':             aircode = 'Airline=K5'
    elif setairline == 'Southwest':           aircode = 'Airline=WN'
    elif setairline == 'Spirit':              aircode = 'Airline=NK'
    elif setairline == 'Suncountry Airlines': aircode = 'Airline=SY'
    elif setairline == 'United Airlines':     aircode = 'Airline=UA'
    elif setairline == 'Virgin America':      aircode = 'Airline=VX'
    elif setairline == 'Volaris':             aircode = 'Airline=Y4'
    else: aircode = ''
    xbmc.log(msg='Fly PDX: setAircode()')
    return aircode

def setFiltercode(setfilter):
    if setfilter   == 'Arrival':   filtercode = '&Type=A'
    elif setfilter == 'Departure': filtercode = '&Type=D'
    elif setfilter == 'All':       filtercode = ''
    else: filtercode = ''
    xbmc.log(msg='Fly PDX: setFiltercode()')
    return filtercode

def setDatecode(setdate):
    if setdate   == 'Today':     datecode = '&Day=Today'
    elif setdate == 'Tomorrow':  datecode = '&Day=Tomorrow'
    elif setdate == 'Yesterday': datecode = '&Day=Yesterday'
    else: datecode = '&Day=Today'
    xbmc.log(msg='Fly PDX: setDatecode()')
    return datecode

alldetails = []
finished  = 0
while finished == 0:
    xbmc.log(msg='Fly PDX: Starting...')

    addon = xbmcaddon.Addon(id='plugin.program.flypdx')

    setairline = xbmcaddon.Addon().getSetting('service1')
    setfilter  = xbmcaddon.Addon().getSetting('service2')
    setdate    = xbmcaddon.Addon().getSetting('service3')
    setdelay   = xbmcaddon.Addon().getSetting('service4')
    setflightno= xbmcaddon.Addon().getSetting('flightno')
    setadcity  = xbmcaddon.Addon().getSetting('adcity')

    aircode    = setAircode(setairline)
    filtercode = setFiltercode(setfilter)
    datecode   = setDatecode(setdate)
    if setflightno == '':
        flightcode = ''
    else:
        flightcode = '&FlightNum='+setflightno

    setadcity = re.sub(r" ", "+", setadcity)
    if setadcity == '':
        adcitycode = ''
    else:
        adcitycode = '&CityFromTo='+setadcity

    if setdelay=='true':
        url = 'http://www.flypdx.com/PDX/Flights?'+aircode+datecode+filtercode+flightcode+adcitycode+'&flightstatus=DL'
    else:
        url = 'http://www.flypdx.com/PDX/Flights?'+aircode+datecode+filtercode+flightcode+adcitycode

    try:
        req      = urllib2.Request(url)
    except TypeError as t:
        xbmc.log(msg='Fly PDX: urllib2.Request(url) failed')

    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response   = urllib2.urlopen(req)
    content    = response.read()
    response.close()

    content    = re.sub('&#39;','\'',content)

    search = r'<td>\s+?<a href=".+?Airlines/'
    content = re.sub(search,'<td>',content)
    search = r'">\s+?<img.+>'
    content = re.sub(search,'',content)
    search = r'\s+?</a>\s+?</td>'
    content = re.sub(search,'</td>',content)

    search = r'<td>\s+?<strong>'
    content = re.sub(search,'<td>',content)
    search = r'</strong>\s+?</td>'
    content = re.sub(search,'</td>',content)

    search = r'<td>\s+?<span>'
    content = re.sub(search,'<td>',content)
    search = r'</span>\s+?</td>'
    content = re.sub(search,'</td>',content)

    search = r'<td>\s+?<span class="text-danger">\s+?<strong>'
    content = re.sub(search,'<td>',content)
    search = r'</strong>'
    content = re.sub(search,'</td>',content)

    search = r'<td>(.+)</td>'
    alldetails.extend(re.compile(search).findall(content))

    recstep = 8

    adlength = int(len(alldetails)/recstep)

    info = FlightInfo(alldetails,recstep)
    info.fixGate(alldetails,recstep)
    info.assignCol(alldetails,recstep)
    schcol = info.schcol
    aircol = info.aircol
    typcol = info.typcol
    adecol = info.adecol
    stscol = info.stscol
    fltcol = info.fltcol
    gtecol = info.gtecol
    bagcol = info.bagcol

    newsettings = 0
    nextfocus = 0
    strrow    = 0
    maxrow    = 14
    if math.ceil(len(alldetails)/recstep) < maxrow:
        endrow = int(len(alldetails)/recstep)
    else:
        endrow = maxrow

    while newsettings == 0:
        #        def __init__(self,setairline,setfilter,setdate,setdelay,setflightno,setadcity,ad,schcol,aircol,typcol,adecol,stscol,fltcol,gtecol,bagcol,nf,rs,sr,er,mr):
        dialog = FlightTableDialog(setairline,setfilter,setdate,setdelay,setflightno,setadcity,alldetails,schcol,aircol,typcol,adecol,stscol,fltcol,gtecol,bagcol,nextfocus,recstep,strrow,endrow,maxrow)
        dialog.doModal()
        if dialog.retval == 0:
            finished = 1
            newsettings = 1
        elif dialog.retval == 1:
            nextfocus = 1
            strrow += maxrow
            endrow += maxrow
            if strrow > int(len(alldetails)/recstep):
                strrow = 0
                if maxrow > int(len(alldetails)/recstep):
                    endrow = int(len(alldetails)/recstep)
                else:
                    endrow = maxrow
        elif dialog.retval == -1:
            nextfocus = -1
            strrow -= maxrow
            endrow -= maxrow
            if strrow < 0:
                if maxrow > int(len(alldetails)/recstep):
                    strrow = 0
                    endrow = int(len(alldetails)/recstep)
                else:
                    if endrow > 0:
                        strrow = 0
                        endrow = maxrow
                    else:
                        strrow = int(len(alldetails)/recstep)-maxrow
                        endrow = int(len(alldetails)/recstep)
        elif dialog.retval == 2:
            newsettings = 1
            del alldetails[:]
            xbmcaddon.Addon(id='plugin.program.flypdx').openSettings()

        #del dialog
        #xbmc.log(msg='Fly PDX: del dialog')
del addon
