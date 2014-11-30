#/*
# *      Copyright (C) 2014 Erwin Junge
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

try:
  import xbmcplugin
  import xbmcgui
except:
  pass
import sys


def addDir(name, module):
  u=sys.argv[0]+"?module="+module
  liz=xbmcgui.ListItem(name)
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


def run(params):
  addDir('Videos', 'wk_2014_videos')
  addDir('Duel gemist', 'wk_2014_gemist')
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
