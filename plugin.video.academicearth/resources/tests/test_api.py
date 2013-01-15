import os
import sys
import unittest
# update path so we can import the addon.py file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from resources.lib.academicearth import api


class ITTests(unittest.TestCase):

    def test_youtube_parsing(self):
        KNOWN = (
            ('http://www.academicearth.org/lectures/utilities-endowments-and-equilibrium', 'VX4eYYmvQ78'),
            ('http://www.academicearth.org/lectures/origins-of-classical-utilitarianism', 'U0iS4Ax3LXc'),
        )
        for url, yt_id in KNOWN:
            lecture = api.Lecture.from_url(url)
            self.assertEqual(lecture.youtube_id, yt_id)
