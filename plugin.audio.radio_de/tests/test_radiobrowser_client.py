# -*- coding: utf-8 -*-
import io
import json
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError

from tests import helpers  # noqa: F401  (stubs the Kodi modules)
from resources.lib.radiobrowser_client import RadioBrowserClient, RadioBrowserError


class FakeResponse(io.BytesIO):
    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode('utf-8'))


def http_error(code):
    return HTTPError('https://example.invalid', code, 'error', {}, io.BytesIO(b''))


@mock.patch('resources.lib.radiobrowser_client.time.sleep', lambda seconds: None)
class RadioBrowserClientTest(unittest.TestCase):

    def setUp(self):
        self.client = RadioBrowserClient(user_agent='test-agent')

    def test_returns_parsed_json_and_sends_user_agent_and_query(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen',
                        return_value=FakeResponse([{'name': 'Station'}])) as urlopen:
            result = self.client.search_stations(10, 1, name='rock')

        self.assertEqual(result, (False, [{'name': 'Station'}]))
        request = urlopen.call_args[0][0]
        self.assertEqual(request.get_header('User-agent'), 'test-agent')
        self.assertIn('/stations/search?', request.full_url)
        self.assertIn('name=rock', request.full_url)
        self.assertIn('hidebroken=true', request.full_url)

    def test_retries_on_connection_errors_and_rotates_servers(self):
        responses = [URLError('connection reset'), URLError('connection reset'), FakeResponse([{'name': 'ok'}])]
        with mock.patch('resources.lib.radiobrowser_client.urlopen', side_effect=responses) as urlopen:
            result = self.client.get_station_by_uuid('abc')

        self.assertEqual(result, {'name': 'ok'})
        self.assertEqual(urlopen.call_count, 3)
        urls = [call[0][0].full_url for call in urlopen.call_args_list]
        self.assertEqual(len({url.split('/json')[0] for url in urls}), 3)
        self.assertTrue(all(call[1]['timeout'] == RadioBrowserClient.TIMEOUT
                            for call in urlopen.call_args_list))

    def test_retries_on_server_errors(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen',
                        side_effect=[http_error(503), FakeResponse([])]) as urlopen:
            self.assertEqual(self.client.get_tags(), [])
        self.assertEqual(urlopen.call_count, 2)

    def test_client_errors_are_not_retried(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen', side_effect=http_error(404)) as urlopen:
            with self.assertRaises(RadioBrowserError):
                self.client.get_tags()
        self.assertEqual(urlopen.call_count, 1)

    def test_gives_up_after_all_attempts(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen',
                        side_effect=URLError('connection reset')) as urlopen:
            with self.assertRaises(RadioBrowserError):
                self.client.get_countries()
        self.assertEqual(urlopen.call_count, RadioBrowserClient.ATTEMPTS)

    def test_invalid_json_is_an_error_and_not_retried(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen',
                        return_value=io.BytesIO(b'<html>')) as urlopen:
            with self.assertRaises(RadioBrowserError):
                self.client.get_languages()
        self.assertEqual(urlopen.call_count, 1)

    def test_station_by_uuid_returns_none_when_unknown(self):
        with mock.patch('resources.lib.radiobrowser_client.urlopen', return_value=FakeResponse([])):
            self.assertIsNone(self.client.get_station_by_uuid('missing'))

    def test_search_reports_whether_there_is_another_page(self):
        stations = [{'name': str(i)} for i in range(4)]
        with mock.patch('resources.lib.radiobrowser_client.urlopen', return_value=FakeResponse(stations)) as urlopen:
            has_more, page = self.client.search_stations(3, 2, tag='rock')

        self.assertTrue(has_more)
        self.assertEqual(len(page), 3)
        url = urlopen.call_args[0][0].full_url
        self.assertIn('offset=3', url)
        self.assertIn('limit=4', url)


if __name__ == '__main__':
    unittest.main()
