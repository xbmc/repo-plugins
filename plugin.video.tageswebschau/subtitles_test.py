#
# Copyright 2012 Henning Saul, Joern Schumacher 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import unittest
import xml.sax
from subtitles import SubtitlesContentHandler

class SubtitlesContentHandlerTest(unittest.TestCase):

    def setUp(self):
        self._parser = SubtitlesContentHandler()

    def test_parse_subtitles(self):
        ttmlfile = open('resources/test/subtitles_ttml.xml')
        xml.sax.parse(ttmlfile, self._parser)
        ttmlfile.close()
        # print self._parser.result()

       
if __name__ == "__main__":
    unittest.main()
