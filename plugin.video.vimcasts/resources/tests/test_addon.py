#!/usr/bin/env python
import sys, os
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from addon import  plugin, strip_tags, unescape_html, clean, get_json_feed, index


class TestNonViews(unittest.TestCase):

    def test_strip_tags(self):
        known_values = [
            ('<b>Hello</b>', 'Hello'),
            ('Hello', 'Hello'),
            ('<b>', ''),
            ('<b><a href="#">Hello</a></b>', 'Hello'),
        ]
        for inp, expected in known_values:
            self.assertEqual(strip_tags(inp), expected)

    def test_unescape_html(self):
        known_values = [
            ('&gt;jon&dave', '>jon&dave'),
        ]
        for inp, expected in known_values:
            self.assertEqual(unescape_html(inp), expected)

    def test_clean(self):
        known_values = [
            ('<b>jon &amp; dave</b>', 'jon & dave'),
        ]
        for inp, expected in known_values:
            self.assertEqual(clean(inp), expected)


class ITTests(unittest.TestCase):

    def test_api(self):
        resp = get_json_feed()
        self.assertTrue('episodes' in resp.keys())
        self.assertTrue(len(resp['episodes']) > 35)

    def test_index(self):
        items = index()
        self.assertTrue(len(items) > 35)
        expected = {
            'info': {
            'plot': u'Vim\u2019s list feature can be used to reveal hidden characters, such as tabstops and newlines. In this episode, I demonstrate how to customise the appearance of these characters by tweaking the listchars setting. I go on to show how to make these invisible characters blend in with your colortheme.\n'},
             'is_playable': True,
             'label': u'#1 Show invisibles',
             'path': u'http://media.vimcasts.org/videos/1/show_invisibles.m4v',
             'thumbnail': u'http://vimcasts.org/images/posters/show_invisibles.png'
        }
        self.assertEqual(items[0], expected)


# TODO: Get this working...
#class ViewTests(unittest.TestCase):

    #def test_index(self):
        #resp = plugin.run()
        #import pdb; pdb.set_trace()


if __name__ == '__main__':
    unittest.main()
