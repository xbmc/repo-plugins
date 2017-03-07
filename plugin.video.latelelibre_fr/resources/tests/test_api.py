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

import resources.lib.ltl_api as api

class ITTests(unittest.TestCase):

    def test_1_create_index(self):
        menu_list = api.get_create_index()
        self.assertTrue(menu_list is not None and len(menu_list) > 5)
        self.assertTrue(menu_list[0]['ctype'] == 'all')
        self.assertTrue(menu_list[1]['ctype'] == 'reportage')
        self.assertTrue(len(menu_list[0]['themes'].split('¡')) > 4)
        self.assertTrue(len(menu_list[0]['sorting'].split('¡')) > 3)
        self.assertTrue(len(menu_list[2]['menus'].split('¡')) > 6)
        self.assertTrue(len(menu_list[3]['menus'].split('¡')) > 6)
        self.assertTrue(len(menu_list[4]['menus'].split('¡')) > 6)
        self.assertTrue(menu_list[5]['action'] == 'video_docs')
        self.assertTrue(menu_list[6]['action'] == 'search_videos')

    def test_2_video_docs(self):
        doc_list = api.get_video_docs()
        self.assertTrue(doc_list is not None and len(doc_list) > 10)

    def test_3_video_items(self):
        video_items = api.get_video_items()
        self.assertTrue(len(video_items.get('video_list', '')) > 10)

    def test_4_video_sec(self):
        menu_url = 'http://latelelibre.fr/emissions/thibault-o-tour-du-monde/'
        video_list = api.get_video_sec(menu_url)
        self.assertTrue(video_list is not None and len(video_list) > 8)

    def test_5_video_hackaround(self):
        menu_url = 'http://latelelibre.fr/series/une-bien-belge-histoire/'
        video_list = api.get_video_sec(menu_url)
        self.assertTrue(video_list is not None and len(video_list) > 4)


if __name__ == '__main__':
        unittest.main()
