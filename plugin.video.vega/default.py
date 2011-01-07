'''
    VEGA concerts player for XBMC
    Copyright (C) 2010 Jeppe Toustrup

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
'''

from resources.lib import getter, printer


# Plugin constants
__plugin__ = 'VEGA Concerts'
__author__ = 'Jeppe Toustrup'
__url__ = 'http://github.com/Tenzer/plugin.video.vega/'
__version__ = '1.0.1'


if(sys.argv[2].startswith('?concert=')):
	# Print the track listing for a concert
	import re
	info = re.search('\?concert=([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})', sys.argv[2])
	printer.printConcertInfo(info.group(1), getter.getConcertInfo(info.group(1)))
elif(sys.argv[2].startswith('?track=')):
	# Play a concert from the track number provided
	import re
	info = re.search('\?track=(\d+)&concert=([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})', sys.argv[2])
	printer.playTrack(info.group(1), getter.getConcertInfo(info.group(2)))
else:
	# Print the concert listing
	concerts = getter.getConcerts()
	printer.printConcerts(concerts)
