#
#       Copyright (C) 2014-
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#


import xbmc
import xbmcgui
import os
import utils


def nmrCached():
    nCached = xbmcgui.Window(10000).getProperty('SF_CACHED')

    try:    return int(nCached)
    except: return 0


def exists(path):
    found = (len(find(path)) > 0)
    return found


def add(path, period = 0):
    clear(path)
    if period == 0:
        return

    index = 0

    while True:
        property = 'SF_CACHED_%d' % index
        prop     = xbmcgui.Window(10000).getProperty(property)
        index   += 1

        if len(prop) == 0:
            xbmcgui.Window(10000).setProperty(property, path)
            setTimer(property, period)
            incrementCount()

            return


def clear(path):
    property = find(path)
    clearProperty(property)


def clearProperty(property):
    if len(property) > 0:
        xbmcgui.Window(10000).clearProperty(property)
        decrementCount()


def incrementCount():
    count = nmrCached()
    xbmcgui.Window(10000).setProperty('SF_CACHED', str(count+1))


def decrementCount():
    count = nmrCached()
    if count > 0: 
        xbmcgui.Window(10000).setProperty('SF_CACHED', str(count-1))


def find(path):
    nCached = nmrCached()

    index = 0
    
    while nCached > 0:
        property = 'SF_CACHED_%d' % index
        index    += 1

        prop = xbmcgui.Window(10000).getProperty(property)
        if len(prop) > 0:
            if prop == path:
                return property
            nCached -=1

    return ''


def setTimer(property, period):
    name   =  property
    script =  os.path.join(utils.HOME, 'timer.py')
    args   =  property
    cmd    = 'AlarmClock(%s,RunScript(%s,%s),%d,True)' % (name, script, args, period)

    xbmc.executebuiltin('CancelAlarm(%s,True)' % name)        
    xbmc.executebuiltin(cmd)