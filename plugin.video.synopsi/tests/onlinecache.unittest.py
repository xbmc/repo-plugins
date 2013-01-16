# -*- coding: utf-8 -*-
# python standart lib
import os, sys
from unittest import *
import logging
import json
import string
import random
import time

# test helper
from common import connection

# application
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('fakeenv'))
from utilities import *
from apiclient import *
from cache import OnlineStvList, DuplicateStvIdException

def pprint(data):
	global logger

	if data is dict and data.has_key('_db_queries'):
		del data['_db_queries']
	msg = dump(data)
	# print msg
	logger.debug(msg)


class OnlineCacheTest(TestCase):
	def setUp(self):
		print '=' * 50
		cache.clear()

	def test_save_load(self):

		cache.put(test_item1)
		cache.put(test_item3)
		cache.save()

		cache.load()

		self.assertEqual(cache.getByTypeId('movie', '10'), test_item1)

		# check if the items are correctly referenced
		self.assertEqual(id(cache.getByTypeId('movie', '10')), id(cache.getByFilename('/var/log/virtual.ext')))
		self.assertEqual(id(cache.getByTypeId('movie', '10')), id(cache.getByStvId(10009)))

		# check the items encoding
		self.assertEqual(cache.getByTypeId('episode', '10')['file'], u'/var/log/tvshow/Čučoriedky žužlavé.avi')

	def test_put(self):
		movie1 = { 'type': u'movie', 'id': 1, 'file': 'xxx' }
		cache.put(movie1)

		episode1 = { 'type': u'episode', 'id': 2, 'file': 'episode.s02e22.avi' }
		cache.put(episode1)

		movie2 = { 'type': u'movie', 'id': 3, 'file': 'xxx', 'stvId': 9876543 }
		cache.put(movie2)

	def test_correction(self):

		CORRECTION_FILE_HASH = 'abcdefgh1234567890'

		# prepare apiClient with new library

		c = dict(connection)
		c['device_id'] = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(16))
		print 'device_id: ' + c['device_id']
		apiClient = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.ERROR, rel_api_url=c['rel_api_url'])
		cache = OnlineStvList(c['device_id'], apiClient, cwd)


		CORRECTION_TARGET = 654591
		CORRECTION_SOURCE = 16813

		FILENAME = 'asodfhaoherfoahdfs.avi'

		test_item = { 'type': u'movie', 'id': 3, 'file': FILENAME, 'stvId': CORRECTION_SOURCE }

		movies = [
			{ 'type': u'movie', 'id': 1, 'file': 'movie1.avi', 'stvId': 1483669 }	,
			{ 'type': u'movie', 'id': 2, 'file': 'movie2.avi', 'stvId': 45, 'name': 'The Lord of the Rings: The Two Towers' },
			test_item,
			{ 'type': u'movie', 'id': 4, 'file': 'movie4.avi', 'stvId': 408316, 'name': 'Out of Africa' },
			{ 'type': u'episode', 'id': 1, 'file': 'episode1.avi', 'stvId': 602923, 'name': 'I.F.T.' }  ,
			{ 'type': u'episode', 'id': 2, 'file': 'episode2.avi', 'stvId': 1812663, 'name': 'Cat\'s in the Bag...'} ,
			{ 'type': u'episode', 'id': 3, 'file': 'episode3.avi', 'stvId': 2069156, 'name': 'Founder\'s Day' } ]


		# prepare the library
		# do the identification to put the hash into api
		ident = {
			"file_name": "three times.avi",
			"stv_title_hash": CORRECTION_FILE_HASH,
			"os_title_hash": "486d1f7112f9749d",
			"imdb_id": "0102536",
			'title_property[]': ','.join(['name', 'cover_medium']),
			'type': 'movie'
		}

		# let the service know about our hash. withou this it would not be possible to do correction
		identified_title = apiClient.titleIdentify(**ident)

		print 'IDENTIFIED: ' + dump(filtertitles(identified_title))

		#	if the identified title is not our correction source
		#	this should run only first time
		if identified_title['id'] != CORRECTION_SOURCE:
			apiClient.title_identify_correct(CORRECTION_SOURCE, CORRECTION_FILE_HASH, replace_library_item=False)

		# put the correction source title into library + some random items
		for movie in movies:
			cache.put(movie)

		old_title = { 'type': 'movie', 'xbmc_id': 3, 'stv_title_hash': CORRECTION_FILE_HASH }
		new_title = { 'type': 'movie', 'id': CORRECTION_TARGET }

		# this the correction test
		new_item = cache.correct_title(old_title, new_title)

		# rollback correction on api
		apiClient.title_identify_correct(CORRECTION_SOURCE, CORRECTION_FILE_HASH)

		# check if old item is removed
		self.assertTrue(not cache.hasStvId(CORRECTION_SOURCE))
		self.assertTrue(not cache.hasItem(test_item))

		# check if new item is in the right place
		self.assertEqual(cache.byTypeId['movie--3']['stvId'], CORRECTION_TARGET)
		self.assertEqual(cache.byStvId[CORRECTION_TARGET]['file'], FILENAME)
		self.assertEqual(cache.byFilename[FILENAME], new_item)


	def test_correction_recco(self):
		CORRECTION_FILE_HASH = 'abcdefgh1234567890'
		FILENAME = 'asodfhaoherfoahdfs.avi'

		# prepare apiClient with new library
		c = dict(connection)
		c['device_id'] = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(16))
		#~ print 'device_id: ' + c['device_id']
		apiClient = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.ERROR, rel_api_url=c['rel_api_url'])
		cache = OnlineStvList(c['device_id'], apiClient, cwd)

		# choose CORRECTION_TARGET from global_recco, in order to appear in local recco
		glob_recco = apiClient.profileRecco('movie')
		lib_ids = [i['id'] for i in glob_recco['titles']]
		#~ print 'global_recco:' + dump(lib_ids)

		CORRECTION_TARGET = lib_ids[0]
		print 'CORRECTION_TARGET: %d' % CORRECTION_TARGET

		#~ test_item = { 'type': u'movie', 'id': 3, 'file': FILENAME, 'stvId': CORRECTION_SOURCE }
		test_item2 = { 'type': u'movie', 'id': 2, 'file': FILENAME, 'stvId': 74112, 'name': 'noname1' }

		movies = [
			{ 'type': u'movie', 'id': 1, 'file': 'movie1.avi', 'stvId': 69907 }	,
			test_item2,
			#~ test_item,
			{ 'type': u'movie', 'id': 4, 'file': 'movie4.avi', 'stvId': 279256, 'name': 'noname2' },
			{ 'type': u'episode', 'id': 1, 'file': 'episode1.avi', 'stvId': 1910795, 'name': 'noname3' }  ,
			{ 'type': u'episode', 'id': 2, 'file': 'episode2.avi', 'stvId': 807111, 'name': 'noname4'} ,
			{ 'type': u'episode', 'id': 3, 'file': 'episode3.avi', 'stvId': 2444806, 'name': 'noname5' } ]

		# prepare the library
		# do the identification to put the hash into api
		ident = {
			"file_name": "three times.avi",
			"stv_title_hash": CORRECTION_FILE_HASH,
			"os_title_hash": "486d1f7112f9749d",
			"imdb_id": "0102536",
			'title_property[]': ','.join(['name', 'cover_medium']),
			'type': 'movie'
		}

		# let the service know about our hash. withou this it would not be possible to do correction
		identified_title = apiClient.titleIdentify(**ident)

		print 'IDENTIFIED: ' + dump(filtertitles(identified_title))

		# put files from global recco into library
		for movie in movies:
			cache.put(movie)

		# wait
		#~ time.sleep(3)

		recco = apiClient.profileRecco('movie', True)
		lib_ids = [i['id'] for i in recco['titles']]
		print 'recco before:' + dump(lib_ids)

		# pick the first item from recco as correction source
		CORRECTION_SOURCE = lib_ids[0]
		print 'CORRECTION_SOURCE: %d' % CORRECTION_SOURCE

		#	make sure that our CORRECTION_SOURCE is remembered in API as CORRECTION_FILE_HASH
		#	this should run only first time, next time the identified title should be the one from recco
		if identified_title['id'] != CORRECTION_SOURCE:
			apiClient.title_identify_correct(CORRECTION_SOURCE, CORRECTION_FILE_HASH, replace_library_item=False)

		# old title is test_item2
		old_title = { 'type': 'movie', 'xbmc_id': 2, 'stv_title_hash': CORRECTION_FILE_HASH }
		new_title = { 'type': 'movie', 'id': CORRECTION_TARGET }

		# do the correction
		new_item = cache.correct_title(old_title, new_title)

		# wait
		#~ time.sleep(3)

		# get recco
		recco = apiClient.profileRecco('movie', True)
		lib_ids = [i['id'] for i in recco['titles']]
		print 'recco after:' + dump(lib_ids)

		# rollback correction on api
		apiClient.title_identify_correct(CORRECTION_SOURCE, CORRECTION_FILE_HASH)

		# -- test evaluation --
		# check if recco changed
		self.assertTrue(CORRECTION_TARGET in lib_ids)
		self.assertFalse(CORRECTION_SOURCE in lib_ids)

		# check if old item is removed in local cache
		self.assertTrue(not cache.hasStvId(CORRECTION_SOURCE))
		self.assertTrue(not cache.hasItem(test_item2))

		# check if new item is in the right place
		self.assertEqual(cache.byTypeId['movie--2']['stvId'], CORRECTION_TARGET)
		self.assertEqual(cache.byStvId[CORRECTION_TARGET]['file'], FILENAME)
		self.assertEqual(cache.byFilename[FILENAME], new_item)


	def test_get_items(self):
		cache.clear()
		cache.put(test_item1)
		cache.put(test_item3)
		i = cache.getItems()
		self.assertEquals(i[0]['stv_title_hash'], 'ba7c6a7bc6a7b6c')
		self.assertEquals(i[0]['file'], '/var/log/virtual.ext')

if __name__ == '__main__':
	test_item1 = {
		'type': 'movie',
		'id': 10,
		'file': '/var/log/virtual.ext',
		'stvId': 80962,
		'name': 'District 9',
		'stv_title_hash': 'ba7c6a7bc6a7b6c',
	}

	test_item2 = {
		'type': 'movie',
		'id': 11,
		'file': '/var/log/002.avi',
		'stvId': 612160,
		'name': 'Stander',
		'stv_title_hash': 'ba7c6a7bc6a7b6cb8ac8bc',
	}

	test_item3 = {
		'type': 'episode',
		'id': 10,
		'file': u'/var/log/tvshow/Čučoriedky žužlavé.avi',
		'stvId': 3538511,
		'name': 'The Santa Simulation',
		'stv_title_hash': 'c34t66627bc6a7b6cb8ac8bc',
	}

	c = connection
	apiClient = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.ERROR, rel_api_url=c['rel_api_url'])
	cwd = os.path.join(os.getcwd(), 'data', 'cache.dat')

	cache = OnlineStvList(c['device_id'], apiClient, cwd)

	logger = logging.getLogger()

	if len(sys.argv) < 2:
		suite = TestLoader().loadTestsFromTestCase(OnlineCacheTest)
	else:
		suite = TestLoader().loadTestsFromName('OnlineCacheTest.' + sys.argv[1], sys.modules[__name__])

	TextTestRunner(verbosity=2).run(suite)


