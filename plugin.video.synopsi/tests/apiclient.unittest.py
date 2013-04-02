# python standart lib
import os, sys
from unittest import *
import logging
import json
from copy import copy
import random
import string

# test helper
from common import connection

# application
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('fakeenv'))
from utilities import *
from apiclient import *

# test data
exampleEvents = [
	{
		"event": "start",
		"timestamp": '2012-10-08 16:54:34',
		"position": 1222
	},
	{
		"event": "pause",
		"timestamp": '2012-10-08 16:54:40',
		"position": 1359
	},
	{
		"event": "resume",
		"timestamp": '2012-10-08 16:55:10',
		"position": 1359
	},
	{
		"event": "pause",
		"timestamp": '2012-10-08 16:55:10',
		"position": 65535
	},
	{
		"event": "stop",
		"timestamp": '2012-10-08 16:55:15',
		"position": 1460
	},
]




class ApiTest(TestCase):
	def test_auth(self):
		client.getAccessToken()
		self.assertIsInstance(client, ApiClient)
		return client

	def test_auth_fail(self):
		c = copy(connection)
		c['password'] = 'aax'		# bad password
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])

		self.assertRaises(AuthenticationError, client.getAccessToken)
		self.assertTrue(client.isAuthenticated()==False)

	def test_unwatched_episodes(self):
		data = client.unwatchedEpisodes()

		self.assertTrue(data.has_key('lineup'))
		self.assertTrue(data.has_key('new'))
		self.assertTrue(data.has_key('top'))
		self.assertTrue(data.has_key('upcoming'))

	def test_title_identify(self):
		ident = {
			"file_name": "/Volumes/FLOAT/Film/_videne/Night_On_Earth/Night_On_Earth.avi",
			"stv_title_hash": "1defa7f69476e9ffca7b8ceb8c251275afc31ade",
			"os_title_hash": "486d1f7112f9749d",
			"imdb_id": "0102536",
			'title_property[]': ','.join(['name', 'cover_medium']),
			'type': 'movie'
		}

		stv_title = client.titleIdentify(**ident)

		self.assertTrue(stv_title.has_key('type'))

		ident2 = {
			'file_name': '/Volumes/FLOAT/Film/_videne/Notorious/Notorious.[2009self.Eng].TELESYNC.DivX-LTT.avi',
			'stv_title_hash': '8b05ff1ad4865480e4705a42b413115db2bf94db',
			'os_title_hash': '484e59acbfaf64e5',
			'imdb_id': ''
		}

		stv_title = client.titleIdentify(**ident2)
		self.assertTrue(stv_title.has_key('type'))

		ident3 = {
			'file_name': '_videne/Notorious/Notorious.[2009self.Eng].TELESYNC.DivX-LTT.avi',
		}

		stv_title = client.titleIdentify(**ident3)

		self.assertTrue(stv_title.has_key('type'))

		ident = {
			'file_name': '_videne/Notorious/Notorious.[2009self.Eng].TELESYNC.DivX-LTT.avi',
			'stv_title_hash': None,
			'os_title_hash': None
		}

		stv_title = client.titleIdentify(**ident)

		self.assertTrue(stv_title.has_key('type'))
		
		ident = {
			'file_name': '_videne/Notorious/Notorious.[2009self.Eng].TELESYNC.DivX-LTT.avi',
			'stv_title_hash': ''
		}

		stv_title = client.titleIdentify(**ident)

		self.assertTrue(stv_title.has_key('type'))

		ident = {
			'file_name': 'Avatar.avi',
			'stv_title_hash': ''
		}

		stv_title = client.titleIdentify(**ident)

		self.assertTrue(stv_title.has_key('type'))

		ident = {
			'file_name': 'Rambo.avi',
		}

		stv_title = client.titleIdentify(**ident)

		self.assertTrue(stv_title.has_key('type'))


	def test_library_add(self):
		client.getAccessToken()
		
		# change the device id, to use empty library
		randstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
		client.device_id = 'testing_' + randstr
		
		ident = {
			'file_name': '/Volumes/FLOAT/Film/_videne/Notorious/Notorious.[2009self.Eng].TELESYNC.DivX-LTT.avi',
			'stv_title_hash': '8b05ff1ad4865480e4705a42b413115db2bf94db',
			'os_title_hash': '484e59acbfaf64e5',
			'imdb_id': '0472198'
		}

		data = client.titleIdentify(**ident)

		stv_title_id = data['id']

		data = client.libraryTitleAdd(stv_title_id)

		#exampleEvents = []

		watched_data = {
			'rating': 1,
			'player_events': json.dumps(exampleEvents)
		}

		data = client.titleWatched(stv_title_id, **watched_data)

		data = client.libraryTitleRemove(stv_title_id)

	def test_titleWatched(self):
		client.getAccessToken()
		stv_title_id = 145948
		watched_data = {
			'rating': 1,
			'player_events': json.dumps(exampleEvents),
			'software_info': 'Test bullshit'
		}

		data = client.titleWatched(stv_title_id, **watched_data)
		

	def test_profile_recco(self):


		props = [ 'year', 'cover_small' ]
		data = client.profileRecco('movie', False, 5, props)

		self.assertTrue(data.has_key('recco_id'))
		self.assertTrue(data.has_key('titles'))
		self.assertTrue(len(data['titles']) > 0)


	def test_profile_recco_local(self):
		""" 
			To test local recco, we have to prepare a scenario for it:
			- create new client with origin library
			- get global recco
			- add some random titles from global recco to library
			- add titles not in global recco to library
			- test that first title is in local recco, and second not
		"""
		props = [ 'id', 'name', 'year', 'cover_small' ]

		device_id = ''.join([random.choice(string.hexdigits) for n in xrange(32)])
		new_client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], device_id, debugLvl = logging.DEBUG, rel_api_url=c['rel_api_url'])
		
		# get global recco
		reco_global = new_client.profileRecco('movie', False, 50, props)
		reco_global_ids = [i['id'] for i in reco_global['titles']]
		
		# pick five titles
		random_pick = list(set([random.choice(reco_global_ids) for i in xrange(0,5)]))
		
		# add them to library
		for i in random_pick:
			new_client.libraryTitleAdd(i)
		
		# wait a little !
		time.sleep(1)
		
		# get local recco
		reco_local = new_client.profileRecco('movie', True, 50, props)
		
		reco_local_ids = [i['id'] for i in reco_local['titles']]
		
		# check local recco		
		self.assertTrue(reco_local.has_key('recco_id'))
		self.assertTrue(reco_local.has_key('titles'))
		self.assertTrue(len(reco_local['titles']) > 0)
		
		# every picked movie should be in local recco
		for i in random_pick:
			self.assertTrue(i in reco_local_ids)
		

	def test_profile_recco_watched(self):
		props = [ 'id', 'year', 'cover_small' ]
		data = client.profileRecco('movie', False, 5, props)
		all_ids = [ i['id'] for i in data['titles'] ]

		self.assertTrue(data.has_key('recco_id'))
		self.assertTrue(data.has_key('titles'))
		self.assertTrue(len(data['titles']) > 0)

		check_id = data['titles'][0]['id']
		client.titleWatched(check_id, **{'rating': 1})

		new_data = client.profileRecco('movie', False, 5, props)
		all_ids = [ i['id'] for i in new_data['titles'] ]

		self.assertFalse(check_id in all_ids)



	def test_title_similar(self):
		# 1947362 "Ben-Hur (1959)"
		data_similar = client.titleSimilar(1947362)
		#print data_similar

	def test_title(self):
		title = client.title(1947362, cast_props=['name'])

		self.assertTrue(title.has_key('cover_full'))
		self.assertTrue(title.has_key('cast'))
		self.assertTrue(title['cast'][0]['name']=='Charlton Heston')

	def test_tvshow(self):
		title = client.tvshow(14335, cast_props=['name'], season_props=['id','season_number', 'episodes_count', 'watched_count'], season_limit=3)

		# print dump(title)

		self.assertTrue(title.has_key('cover_full'))
		self.assertTrue(title.get('type')=='tvshow')
		self.assertTrue(title.get('year')==2005)
		self.assertTrue(title['cast'][0]['name']=='Josh Radnor')

	def test_season(self):
		title = client.season(14376)

		self.assertTrue(title.has_key('episodes'))
		es = title['episodes']
		self.assertTrue(es[0].has_key('season_number'))
		self.assertTrue(es[0].has_key('episode_number'))
		self.assertTrue(es[0].has_key('watched'))
		self.assertTrue(es[0].has_key('id'))



	def test_unicode_input(self):
		data = {
			'key-one': u'Alfa - \u03b1',
			'key-dict': {
				'key-nested': u'Gama - \u03b3'
			}
		}

		enc_data = client._unicode_input(data)
		self.assertEquals(str(enc_data), r"{'key-one': 'Alfa - \xce\xb1', 'key-dict': {'key-nested': 'Gama - \xce\xb3'}}")

	def test_search(self):
		result = client.search('Adams aebler', 13)
		
		self.assertTrue(result.has_key('search_result'))
		self.assertTrue(result['search_result'][0]['id'] == 514461)


		result = client.search('Love', 13)
		self.assertTrue(len(result['search_result']) == 13)

	def test_identify_correct(self):
		result = client.title_identify_correct(1947362, '8b05ff1ad4865480e4705a42b413115db2bf94db')
		#~ print dump(result)
		self.assertTrue(result['status']=='ok')

	@skip('this needs deeper work')
	def test_identify_correct_library(self):
		TITLE_CORRECTION_TARGET = 1947362
		CORRECTION_FILE_HASH = '52b6f00222cdb3631d9914aee6b662961e924aa5'	# hash of my "three times" file

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

		# let the service know about our hash. without this it would not be possible to do correction
		stv_title = client.titleIdentify(**ident)

		# make sure that this unreal id is in library
		SOME_ID_IN_LIBRARY = 100
		result = client.title_identify_correct(SOME_ID_IN_LIBRARY, CORRECTION_FILE_HASH)
		self.assertTrue(result.get('status')=='ok')

		library = client.library(['id', 'type', 'name'])
		lib_ids = [i['id'] for i in library['titles']]
		#~ print lib_ids

		# the id should already be there after correction, but we can let this code here
		if SOME_ID_IN_LIBRARY not in lib_ids:
			print 'adding %d into library' % SOME_ID_IN_LIBRARY
			client.libraryTitleAdd(SOME_ID_IN_LIBRARY)

		# remove the target id if it is in the library
		if TITLE_CORRECTION_TARGET in lib_ids:
			print 'removing %d from library' % TITLE_CORRECTION_TARGET
			client.libraryTitleRemove(TITLE_CORRECTION_TARGET)

		library = client.library(['id', 'type', 'name'])
		lib_ids = [i['id'] for i in library['titles']]
		#~ print lib_ids

		self.assertTrue(TITLE_CORRECTION_TARGET not in lib_ids, "The test should start without this id")

		# test the correction

		#	get recco
		recco = client.profileRecco('movie', True)
		lib_ids = [i['id'] for i in recco['titles']]
		print 'recco:' + dump(lib_ids)

		result = client.title_identify_correct(TITLE_CORRECTION_TARGET, CORRECTION_FILE_HASH)
		self.assertTrue(result.get('status')=='ok')

		library = client.library(['id', 'type', 'name'])
		lib_ids = [i['id'] for i in library['titles']]
		self.assertTrue(TITLE_CORRECTION_TARGET in lib_ids, "The correction target id is not in library")
		self.assertTrue(SOME_ID_IN_LIBRARY not in lib_ids, "The corrected id is still in library")


		recco = client.profileRecco('movie', True)
		lib_ids = [i['id'] for i in recco['titles']]
		print 'recco:' + dump(lib_ids)


		# correct back to stv_id = SOME_ID_IN_LIBRARY
		result = client.title_identify_correct(SOME_ID_IN_LIBRARY, CORRECTION_FILE_HASH)
		self.assertTrue(result.get('status')=='ok')

		library = client.library(['id', 'type', 'name'])
		lib_ids = [i['id'] for i in library['titles']]
		self.assertTrue(TITLE_CORRECTION_TARGET not in lib_ids)
		self.assertTrue(SOME_ID_IN_LIBRARY in lib_ids)

	@skip('this needs deeper work')
	def test_correction_recco(self):
		TITLE_CORRECTION_TARGET = 1947362
		CORRECTION_FILE_HASH = '52b6f00222cdb3631d9914aee6b662961e924aa5'	# hash of my "three times" file

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
		stv_title = client.titleIdentify(**ident)

		# make sure that this unreal id in library
		SOME_ID_IN_LIBRARY = 100
		result = client.title_identify_correct(SOME_ID_IN_LIBRARY, CORRECTION_FILE_HASH)
		self.assertTrue(result.get('status')=='ok')

		# remove the target id if it is in the library
		if TITLE_CORRECTION_TARGET in lib_ids:
			print 'removing %d from library' % TITLE_CORRECTION_TARGET
			client.libraryTitleRemove(TITLE_CORRECTION_TARGET)

    
	def test_library(self):
		result = client.library(['date', 'genres', 'cover_small'])
		self.assertTrue(result.get('created'))
		self.assertTrue(result.get('device_id'))
		self.assertTrue(result.get('name'))
		self.assertTrue(result.get('titles'))
		self.assertTrue(type(result['titles']) is list)
		
		result2 = client.library(['id', 'cover_full', 'cover_large', 'cover_medium', 'cover_small', 'cover_thumbnail', 'date', 'genres', 'url', 'name', 'plot', 'released', 'trailer', 'type', 'year', 'runtime', 'directors', 'writers', 'cast', 'watched'])
		self.assertTrue(result2.get('created'))
		self.assertTrue(result2.get('device_id'))
		self.assertTrue(result2.get('name'))
		self.assertTrue(result2.get('titles'))
		self.assertTrue(type(result2['titles']) is list)

	def test_profileCreate(self):
		device_id = ''.join([random.choice(string.hexdigits) for n in xrange(32)])
		new_client = ApiClient(c['base_url'], c['key'], c['secret'], None, None, device_id, debugLvl = logging.DEBUG, rel_api_url=c['rel_api_url'])
		
		# bad request
		result = new_client.profileCreate('Real \;\"\\"Name', '"select 1\".smid\"@gmail.com')		
		print result
		
		# good request, but repeated
		result = new_client.profileCreate('Real Second Name', 'martin.smid@gmail.com')		
		print result
		
		# good request, unique
		result = new_client.profileCreate('Real Third Name', 'martin.smid+%s@gmail.com' % device_id)		
		print result
		
		#~ self.assertEqual(result.get('status'), 'created')

if __name__ == '__main__':
	c = connection
	client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl = logging.DEBUG, rel_api_url=c['rel_api_url'])

	logger = logging.getLogger()


	if len(sys.argv) < 2:
		suite = TestLoader().loadTestsFromTestCase(ApiTest)
	else:
		suite = TestLoader().loadTestsFromName('ApiTest.' + sys.argv[1], sys.modules[__name__])

	TextTestRunner(verbosity=2).run(suite)


