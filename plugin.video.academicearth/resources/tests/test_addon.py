#!/usr/bin/env python
'''
    This module contains unit tests and integration tests.
'''
import os
import sys
import unittest
# update path so we can import the addon.py file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import addon
from resources.lib.academicearth import api


class TestViews(unittest.TestCase):

    def test_show_index(self):
        items = addon.show_index()
        self.assertEqual(len(items), 3)

        item = items[0]
        self.assertEqual(item['label'], 'Subjects')
        self.assertEqual(item['path'],
                         'plugin://plugin.video.academicearth/subjects/')

    def test_show_subjects(self):
        items = addon.show_subjects()

        # Sanity check, the exact number of subjects could change. Currently
        # there are 67 subjects.
        self.assertTrue(len(items) > 60)

        url_ptn = ('plugin://plugin.video.academicearth/subjects/'
                   'http%3A%2F%2Fwww.academicearth')
        for item in items:
            self.assertTrue(item['label'] is not None)
            self.assertTrue(len(item['label']) > 0)
            self.assertTrue(item['path'].startswith(url_ptn))

    def test_show_subject_info(self):
        url = 'http://www.academicearth.org/subjects/programming'
        items = addon.show_info(url, api.Subject)
        self.assertTrue(len(items) > 30)

        for item in items:
            if item['path'].startswith(
                    'plugin://plugin.video.academicearth/lectures'):
                self.assertTrue(item['is_playable'])
                label = item['label']
                self.assertTrue(label is not None and len(label) > 0
                                and label.startswith('Lecture: '))
            elif item['path'].startswith(
                    'plugin://plugin.video.academicearth/courses'):
                #validate course
                label = item['label']
                self.assertTrue(label is not None and len(label) > 0)
            else:
                raise Exception('Item path appears to be incorrect')

    def test_show_course_info(self):
        url = 'http://www.academicearth.org/courses/introduction-to-algorithms'
        items = addon.show_course_info(url)

        # currently 21 lectures, perhaps this check is too brittle?
        self.assertTrue(len(items) == 21)

        for item in items:
            self.assertTrue(item['is_playable'])
            label = item['label']
            self.assertTrue(label is not None and len(label) > 0
                            and label.startswith('Lecture: '))
            self.assertTrue(item['path'].startswith(
                'plugin://plugin.video.academicearth/lectures'))

    # TODO: This test relies on the addon being intialized since there is a
    # call to plugin.set_resolved_url() within the play_lecture view.
    #def test_play_lecture(self):
        #url = ('http://www.academicearth.org/lectures'
                #'/dynamic-programming-leiserson')
        #youtube_id = 'V5hZoJ6uK-s'
        #youtube_addon_url = ('plugin://plugin.video.youtube/'
                               #'?action=play_video&videoid=V5hZoJ6uK-s')

        #item = addon.play_lecture(url)[0]

        # verify item.set_played()
        # verify item url


if __name__ == '__main__':
    unittest.main()
