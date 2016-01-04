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
        self.assertTrue(menu_list is not None and len(menu_list) == 4)
        self.assertTrue(menu_list[0]['action'] == 'menu_sec')
        self.assertTrue(menu_list[1]['action'] == 'menu_sec')
        self.assertTrue(len(menu_list[0]['args'].split('¡')) > 10)
        self.assertTrue(len(menu_list[0]['args'].split('¡')[0].split('¿')) == 2)
        self.assertTrue(len(menu_list[1]['args'].split('¡')) == 6)
        self.assertTrue(len(menu_list[1]['args'].split('¡')[0].split('¿')) == 2)
        self.assertTrue(menu_list[2]['action'] == 'program_list')
        self.assertTrue(menu_list[3]['action'] == 'menu_direct')

    def test_2_program_list(self):
        programs = api.get_program_list('http://www.rtve.es/alacarta/programas/rne/todos/1/')
        self.assertTrue(programs is not None and len(programs['program_list']) > 30)
        self.assertTrue(programs['program_list'][0]['title'] != '')
        self.assertTrue(programs['program_list'][0]['url'].startswith('http'))
        self.assertTrue(programs['program_list'][0]['action'] == 'audio_list')
        self.assertTrue(programs['program_list'][-1]['title'] != '')
        self.assertTrue(programs['program_list'][-1]['url'].startswith('http'))
        self.assertTrue(programs['program_list'][-1]['action'] == 'program_list')

    def test_3_audio_list(self):
        audios = api.get_audio_list('http://www.rtve.es/alacarta/audios/jazz-porque-si/')
        self.assertTrue(audios is not None and len(audios['audio_list']) > 10)
        self.assertTrue(audios['audio_list'][0]['title'] != '')
        self.assertTrue(audios['audio_list'][0]['url'].startswith('http'))
        self.assertTrue(audios['audio_list'][0]['action'] == 'play_audio')
        self.assertTrue(audios['audio_list'][0]['duration'] != '')
        self.assertTrue(audios['audio_list'][-1]['title'] != '')
        self.assertTrue(audios['audio_list'][-1]['url'].startswith('http'))
        self.assertTrue(audios['audio_list'][-1]['action'] == 'audio_list')

    def test_4_audio_search(self):
        url_search = api.get_search_url('malikian')
        audios = api.get_search_list(url_search)
        self.assertTrue(audios is not None and len(audios['search_list']) > 2)
        self.assertTrue(audios['search_list'][0]['title'] != '')
        self.assertTrue(audios['search_list'][0]['url'].startswith('http'))
        self.assertTrue(audios['search_list'][0]['action'] == 'play_audio')
        self.assertTrue(audios['search_list'][0]['duration'] != '')
        self.assertTrue(audios['search_list'][-1]['title'] != '')
        self.assertTrue(audios['search_list'][-1]['url'].startswith('http'))
        self.assertTrue(audios['search_list'][-1]['action'] == 'search_list')


if __name__ == '__main__':
        unittest.main()
