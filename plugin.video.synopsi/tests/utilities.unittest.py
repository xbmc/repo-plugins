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
	
	def test_xml_sources(self):
		sources = get_movie_sources()
		sources.sort(key=len, reverse=True)
		print sources
		
	def test_rel_path(self):
		path1 = '/home/smid/Videos/_testset/TVShows/xxx/the/movie/file.avi'
		rel1 = rel_path(path1)
		self.assertEqual(rel1, 'the/movie/file.avi')
		path2 = '/home/smid/Videos/_testset/TVShows/the/movie/file.avi'
		rel2 = rel_path(path2)
		self.assertEqual(rel2, 'the/movie/file.avi')
		path3 = '/home/smid/Videos/_testset/the/movie/file.avi'
		rel3 = rel_path(path3)
		self.assertEqual(rel3, '/home/smid/Videos/_testset/the/movie/file.avi')

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


