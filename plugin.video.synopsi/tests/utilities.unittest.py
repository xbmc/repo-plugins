# python standart lib
import os, sys
from unittest import *
import logging
import json

# test helper
from common import connection

# application
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('fakeenv'))
from utilities import *
from apiclient import *
from cache import StvList

class UtilitiesTest(TestCase):
	def test_hashes(self):
		def gethash(path):
			movie = {}
			movie['stv_title_hash'] = stv_hash(path)
			movie['os_title_hash'] = hash_opensubtitle(path)
			return movie
		
		print gethash(hash_path)


if __name__ == '__main__':
	test_item1 = {
		'type': 'movie',
		'id': 10,
		'file': '/var/log/virtual.ext',
		'stvId': 10009
	}		

	#~ hash_path = '/media/sdb1/Movies/Jeff.Who.Lives.at.Home.2011.LIMITED.DVDRip.XviD-AMIABLE/Jeff.Who.Lives.at.Home.2011.LIMITED.DVDRip.XviD-AMIABLE.avi'		
	hash_path = '/media/VESMIR/Film/Movies/Pioneer.One.S01E02.720p.x264-VODO/Pioneer.One.S01E02.720p.x264-VODO.mkv'
	#~ hash_path = '/media/VESMIR/Film/Movies/\[ UsaBit.com \] - Life.in.a.Day.2011.DVDRiP.XViD-TASTE/Life in a day.avi'

	logger = logging.getLogger()

	if len(sys.argv) < 2:
		suite = TestLoader().loadTestsFromTestCase(UtilitiesTest)
	else:
		suite = TestLoader().loadTestsFromName('UtilitiesTest.' + sys.argv[1], sys.modules[__name__])
		
	TextTestRunner(verbosity=2).run(suite)


