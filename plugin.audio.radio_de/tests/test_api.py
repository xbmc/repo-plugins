# -*- coding: utf-8 -*-
import unittest
from unittest import mock

from tests import helpers  # noqa: F401  (stubs the Kodi modules)
from resources.lib.api import RadioApi, RadioApiError
from resources.lib.radiobrowser_client import RadioBrowserError

STATION = {
    'stationuuid': 'uuid-1',
    'name': 'Test FM',
    'favicon': 'https://example.invalid/logo.png',
    'tags': 'rock,pop',
    'url': 'http://example.invalid/stream',
    'url_resolved': 'https://example.invalid/resolved.mp3',
    'bitrate': 128,
    'votes': 5,
    'homepage': 'https://example.invalid',
}


class RadioApiTest(unittest.TestCase):

    def setUp(self):
        self.api = RadioApi()
        self.api.log = lambda text: None
        self.client = mock.Mock()
        self.api.client = self.client

    def test_station_lookup_uses_resolved_url_and_formats_fields(self):
        self.client.get_station_by_uuid.return_value = dict(STATION)

        station = self.api.get_station_by_station_id('uuid-1')

        self.assertEqual(station['id'], 'uuid-1')
        self.assertEqual(station['name'], 'Test FM')
        self.assertEqual(station['thumbnail'], 'https://example.invalid/logo.png')
        self.assertEqual(station['genre'], 'rock,pop')
        self.assertEqual(station['stream_url'], 'https://example.invalid/resolved.mp3')

    def test_station_lookup_without_stream_returns_none(self):
        self.client.get_station_by_uuid.return_value = dict(STATION, url='', url_resolved='')
        self.assertIsNone(self.api.get_station_by_station_id('uuid-1'))

    def test_unknown_station_returns_none(self):
        self.client.get_station_by_uuid.return_value = None
        self.assertIsNone(self.api.get_station_by_station_id('missing'))

    def test_playlist_urls_are_resolved(self):
        self.client.get_station_by_uuid.return_value = dict(STATION, url_resolved='http://example.invalid/list.m3u')
        with mock.patch.object(RadioApi, '_RadioApi__urlopen',
                               return_value=b'#EXTM3U\nhttp://example.invalid/real\n'):
            station = self.api.get_station_by_station_id('uuid-1')
        self.assertEqual(station['stream_url'], 'http://example.invalid/real')

    def test_client_errors_become_radio_api_errors(self):
        self.client.get_tags.side_effect = RadioBrowserError('boom')
        with self.assertRaises(RadioApiError):
            self.api.get_genres()

    def test_paging_counts_the_next_page(self):
        self.client.search_stations.return_value = (True, [dict(STATION)])
        pages, stations = self.api.get_stations_by_genre('rock', 'STATION_NAME', 10, 2)
        self.assertEqual(pages, 3)
        self.assertEqual(len(stations), 1)
        self.assertEqual(self.client.search_stations.call_args[1]['tag'], 'rock')

        self.client.search_stations.return_value = (False, [dict(STATION)])
        pages, _ = self.api.get_stations_by_genre('rock', 'STATION_NAME', 10, 2)
        self.assertEqual(pages, 2)


class StationCacheTest(unittest.TestCase):

    def setUp(self):
        self.api = RadioApi()
        self.api.log = lambda text: None
        self.client = mock.Mock()
        self.api.client = self.client
        self.cache = {}

    def test_successful_lookup_is_cached(self):
        self.client.get_station_by_uuid.return_value = dict(STATION)

        station = self.api.get_station_cached('uuid-1', self.cache)

        self.assertEqual(station['name'], 'Test FM')
        self.assertEqual(set(self.cache['uuid-1']), set(RadioApi.CACHED_FIELDS))
        self.assertEqual(self.cache['uuid-1']['stream_url'], 'https://example.invalid/resolved.mp3')

    def test_cache_is_used_when_the_lookup_fails(self):
        self.client.get_station_by_uuid.return_value = dict(STATION)
        self.api.get_station_cached('uuid-1', self.cache)

        self.client.get_station_by_uuid.side_effect = RadioBrowserError('connection reset')
        station = self.api.get_station_cached('uuid-1', self.cache)

        self.assertEqual(station['name'], 'Test FM')
        self.assertEqual(station['stream_url'], 'https://example.invalid/resolved.mp3')
        self.assertEqual(station['current_track'], '')

    def test_error_is_raised_for_a_station_that_was_never_cached(self):
        self.client.get_station_by_uuid.side_effect = RadioBrowserError('connection reset')
        with self.assertRaises(RadioApiError):
            self.api.get_station_cached('uuid-1', self.cache)

    def test_lookup_without_station_keeps_the_cache_untouched(self):
        self.client.get_station_by_uuid.return_value = dict(STATION)
        self.api.get_station_cached('uuid-1', self.cache)
        before = dict(self.cache['uuid-1'])

        self.client.get_station_by_uuid.return_value = None
        self.assertIsNone(self.api.get_station_cached('uuid-1', self.cache))
        self.assertEqual(self.cache['uuid-1'], before)

    def test_fresh_lookup_replaces_the_cached_stream(self):
        self.client.get_station_by_uuid.return_value = dict(STATION)
        self.api.get_station_cached('uuid-1', self.cache)

        self.client.get_station_by_uuid.return_value = dict(STATION, url_resolved='https://example.invalid/new.mp3')
        self.api.get_station_cached('uuid-1', self.cache)

        self.assertEqual(self.cache['uuid-1']['stream_url'], 'https://example.invalid/new.mp3')


if __name__ == '__main__':
    unittest.main()
