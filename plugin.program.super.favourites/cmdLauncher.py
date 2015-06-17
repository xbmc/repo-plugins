#
#       Copyright (C) 2015-
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

import favourite
import utils

FRODO = utils.FRODO


if __name__ == '__main__':
    cmd = sys.argv[1]
    cmd = favourite.tidy(cmd)  

    if cmd.startswith('RunScript'):    
        #workaround bug in Frodo that can cause lock-up
        #when running a script favourite
        if FRODO:
            update = '%s' % (sys.argv[0])
            update = 'Container.Update(%s,replace)' % update
            xbmc.executebuiltin(update)

    xbmc.executebuiltin('ActivateWindow(Home)')
    xbmc.executebuiltin(cmd)
   