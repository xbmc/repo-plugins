# -*- coding: utf-8 -*-
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
from cache import OfflineStvList, DuplicateStvIdException


class CacheTest(TestCase):
	def setUp(self):
		cache.clear()

	def test_save_load(self):

		cache.put(test_item1)
		cache.put(test_item3)
		cache.put(test_item_tvshow)
		cache.save()

		cache.load()

		self.assertEqual(cache.getByTypeId('movie', '10'), test_item1)

		# check if the items are correctly referenced
		self.assertEqual(id(cache.getByTypeId('movie', '10')), id(cache.getByFilename('/var/log/virtual.ext')))
		self.assertEqual(id(cache.getByTypeId('movie', '10')), id(cache.getByStvId(10009)))

		# check the items encoding
		self.assertEqual(cache.getByTypeId('episode', '10')['file'], u'/var/log/tvshow/Čučoriedky žužlavé.avi')



	def test_addorupdate_stack(self):
		stack_ident = {
			"file_name": "stack:///Volumes/FLOAT/Film/cache ceske titulky/Cache - CD1.avi , /Volumes/FLOAT/Film/cache ceske titulky/Cache - CD2.avi",
			"stv_title_hash": 'FF00FF00',
			"os_title_hash": 'FF00FF00',
			"imdb_id": "0109362"
		}

	def test_put(self):
		movie1 = { 'type': u'movie', 'id': 1, 'file': 'xxx' }
		cache.put(movie1)

		episode1 = { 'type': u'episode', 'id': 2, 'file': 'episode.s02e22.avi' }
		cache.put(episode1)

		movie2 = { 'type': u'movie', 'id': 3, 'file': 'xxx', 'stvId': 9876543 }
		cache.put(movie2)

	def test_get_path(self):
		movie = {
			'file': "stack:///Volumes/FLOAT/Film/cache ceske titulky/Cache - CD1.avi , /Volumes/FLOAT/Film/cache ceske titulky/Cache - CD2.avi",
		}

		#print cache.get_path(movie)
		self.assertEqual(cache.get_path(movie), '/Volumes/FLOAT/Film/cache ceske titulky/Cache - CD1.avi')

	def test_correction(self):
		NEW_STV_ID = 1234567
		OLD_STV_ID = 9876543
		FILENAME = 'asodfhaoherfoahdfs.avi'

		test_item = { 'type': u'movie', 'id': 3, 'file': FILENAME, 'stvId': OLD_STV_ID }

		movies = [
			{ 'type': u'movie', 'id': 1, 'file': 'movie1.avi', 'stvId': 1111 }		,
			{ 'type': u'movie', 'id': 2, 'file': 'movie2.avi', 'stvId': 1112 }      ,
			test_item,
			{ 'type': u'movie', 'id': 4, 'file': 'movie4.avi', 'stvId': 1113 }      ,
			{ 'type': u'movie', 'id': 5, 'file': 'movie5.avi', 'stvId': 1114 }      ,
			{ 'type': u'episode', 'id': 1, 'file': 'episode1.avi', 'stvId': 9991 }  ,
			{ 'type': u'episode', 'id': 2, 'file': 'episode2.avi', 'stvId': 9992 }  ,
			{ 'type': u'episode', 'id': 3, 'file': 'episode3.avi', 'stvId': 9993 }  ,
			{ 'type': u'episode', 'id': 4, 'file': 'episode4.avi', 'stvId': 9994 } ]

		for movie in movies:
			cache.put(movie)

		cache.list()

		old_title = { 'type': 'movie', 'xbmc_id': 3 }
		new_title = { 'type': 'movie', 'id': NEW_STV_ID }

		new_item = cache.correct_title(old_title, new_title)

		# check if old item is removed
		self.assertFalse(cache.hasStvId(OLD_STV_ID))
		self.assertFalse(cache.hasItem(test_item))

		# check if new item is in the right place
		self.assertEqual(cache.byTypeId['movie--3']['stvId'], NEW_STV_ID)
		self.assertEqual(cache.byStvId[NEW_STV_ID]['file'], FILENAME)
		self.assertEqual(cache.byFilename[FILENAME], new_item)

		cache.list()

	def test_update_title(self):
		cache.put(test_item1)

		# title is a synopsi title, where title['id'] is a stvId
		title_01 = { 'id': test_item1['stvId'], 'stv_title_hash': 'should be overwritten', 'type': 'TODO: should stay?',  }

		cache.updateTitle(title_01)

		self.assertEquals(title_01['file'], test_item1['file'])
		self.assertEquals(title_01['stv_title_hash'], test_item1['stv_title_hash'])
		self.assertEquals(title_01['id'], test_item1['stvId'])

	def test_disallow_duplicate_stvid(self):
		with self.assertRaises(DuplicateStvIdException):
			cache.put(test_item1)
			cache.put(test_item2)

	def test_get_items(self):
		cache.clear()
		cache.put(test_item1)
		cache.put(test_item3)
		i = cache.getItems()
		self.assertEquals(i[0]['stv_title_hash'], 'ba7c6a7bc6a7b6c')
		self.assertEquals(i[0]['file'], '/var/log/virtual.ext')

	def test_show_saved_cache(self):
		cache = OfflineStvList('xyz_test', '/home/smid/.xbmc/userdata/addon_data/plugin.video.synopsi/cache.dat')
		cache.load()
		cache.dump()
		

if __name__ == '__main__':
	test_item1 = {
		'type': 'movie',
		'id': 10,
		'file': '/var/log/virtual.ext',
		'stvId': 10009,
		'stv_title_hash': 'ba7c6a7bc6a7b6c',
	}

	test_item2 = {
		'type': 'movie',
		'id': 11,
		'file': '/var/log/002.avi',
		'stvId': 10009,
		'stv_title_hash': 'ba7c6a7bc6a7b6cb8ac8bc',
	}

	test_item3 = {
		'type': 'episode',
		'id': 10,
		'file': u'/var/log/tvshow/Čučoriedky žužlavé.avi',
		'stvId': 10011,
		'stv_title_hash': 'c34t66627bc6a7b6cb8ac8bc',
	}

	test_item_tvshow = {
		'type': 'tvshow',
		'id': 1,
		'stvId': 901,
	}

	c = connection
	#~ apiClient = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.ERROR, rel_api_url=c['rel_api_url'])
	cwd = os.path.join(os.getcwd(), 'cache.dat')

	cache = OfflineStvList(c['device_id'], cwd)

	logger = logging.getLogger()

	if len(sys.argv) < 2:
		suite = TestLoader().loadTestsFromTestCase(CacheTest)
	else:
		suite = TestLoader().loadTestsFromName('CacheTest.' + sys.argv[1], sys.modules[__name__])

	TextTestRunner(verbosity=2).run(suite)


