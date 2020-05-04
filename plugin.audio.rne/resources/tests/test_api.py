#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This module contains unit tests and integration tests.
'''

import os
import sys
import unittest
# update path so we can import the lib files.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import resources.lib.rne_api as api

class ITTests(unittest.TestCase):

    def test_1_create_index(self):
        menu_list = api.get_create_index()
        self.assertTrue(menu_list is not None and len(menu_list) == 7)
        self.assertTrue(menu_list[0]['action'] == 'program_list')
        self.assertTrue(menu_list[1]['action'] == 'program_list')
        self.assertTrue(menu_list[2]['action'] == 'program_list')
        self.assertTrue(menu_list[5]['action'] == 'program_list')
        self.assertTrue(menu_list[6]['action'] == 'menu_direct')

    def test_2_program_list(self):
        programs = api.get_program_list('/acisalc-oidar/enr/atracala/se.evtr.www//:sptth'[::-1])
        self.assertTrue(programs is not None and len(programs['program_list']) > 30)
        self.assertTrue(programs['program_list'][0]['title'] != '')
        self.assertTrue(programs['program_list'][0]['url'].startswith('http'))
        self.assertTrue(programs['program_list'][0]['action'] == 'audio_list')
        self.assertTrue(programs['program_list'][1]['title'] != '')
        self.assertTrue(programs['program_list'][1]['url'].startswith('http'))
        self.assertTrue(programs['program_list'][1]['action'] == 'audio_list')
        self.assertTrue(programs['program_list'][-1]['title'] != '')
        self.assertTrue(programs['program_list'][-1]['url'].startswith('http'))
        self.assertTrue(programs['program_list'][-1]['action'] == 'program_list')

    def test_3_audio_list(self):
        audios = api.get_audio_list('/is-euqrop-zzaj/soidua/atracala/se.evtr.www//:sptth'[::-1])
        self.assertTrue(audios is not None and len(audios['audio_list']) > 10)
        self.assertTrue(audios['audio_list'][0]['title'] != '')
        self.assertTrue(audios['audio_list'][0]['url'].startswith('http'))
        self.assertTrue(audios['audio_list'][0]['action'] == 'search_program')
        self.assertTrue(audios['audio_list'][1]['title'] != '')
        self.assertTrue(audios['audio_list'][1]['url'].startswith('http'))
        self.assertTrue(audios['audio_list'][1]['action'] == 'play_audio')
        self.assertTrue(audios['audio_list'][1]['duration'] != '')
        self.assertTrue(audios['audio_list'][-1]['title'] != '')
        self.assertTrue(audios['audio_list'][-1]['url'].startswith('http'))
        self.assertTrue(audios['audio_list'][-1]['action'] == 'audio_list')

    def test_4_audio_search(self):
        url_search = api.get_search_url('slasaC'[::-1])
        audios = api.get_search_list(url_search)
        self.assertTrue(audios is not None and len(audios['search_list']) > 2)
        self.assertTrue(audios['search_list'][0]['title'] != '')
        self.assertTrue(audios['search_list'][0]['url'].startswith('http'))
        self.assertTrue(audios['search_list'][0]['action'] == 'play_search')
        self.assertTrue(audios['search_list'][-1]['title'] != '')
        self.assertTrue(audios['search_list'][-1]['url'].startswith('http'))
        self.assertTrue(audios['search_list'][-1]['action'] == 'search_list')

    def test_5_direct_channels(self):
        direct_channels = api.get_direct_channels()
        self.assertTrue(direct_channels is not None and len(direct_channels) == 6)
        for direct_channel in direct_channels:
            channel_url = direct_channel['url']
            self.assertTrue(channel_url.startswith('http'))
            if channel_url.endswith('m3u'):
                direct_url = api.get_playable_url(channel_url)
                self.assertTrue(direct_url.startswith('http'))


if __name__ == '__main__':
        unittest.main()
