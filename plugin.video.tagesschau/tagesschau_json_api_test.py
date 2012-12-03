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
import json
from tagesschau_json_api import VideoContentParser

class VideoContentParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = VideoContentParser()

    def load_json(self, filename):
        handle = open(filename, 'r');
        return json.loads(handle.read())

    def test_parse_video_missing_videos(self):
        jsonvideo = self.load_json('resources/test/video_missing_image_1.json')
        video = self.parser.parse_video(jsonvideo);
        self.assertIsNone(video.image_url(), 'Video JSON has no images, expected None as result')
        
if __name__ == "__main__":
    unittest.main()
