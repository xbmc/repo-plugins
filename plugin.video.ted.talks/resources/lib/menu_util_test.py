import unittest
import menu_util
import re

getLS = lambda x: x

class TestNewTalksRss(unittest.TestCase):

    def test_create_context_menu_fallback(self):
        context_menu = menu_util.create_context_menu(getLS)
        self.assertEquals([(30097, 'Action(queue)')], context_menu)

    def test_create_context_menu_url(self):
        context_menu = menu_util.create_context_menu(getLS, 'invalid://nowhere/nothing.mp4')
        self.assertTrue(len(context_menu) == 2)
        self.assertEquals((30097, 'Action(queue)'), context_menu[0])
        self.assertEquals(30096, context_menu[1][0])
        download_re = re.compile('RunPlugin\(.+?mode=downloadVideo&url=invalid://nowhere/nothing\.mp4\)')
        self.assertTrue(download_re.match(context_menu[1][1]))

    def test_create_context_menu_add_favorite(self):
        context_menu = menu_util.create_context_menu(getLS, favorites_action = "add", talkID = "42")
        self.assertTrue(len(context_menu) == 2)
        self.assertEquals((30097, 'Action(queue)'), context_menu[0])
        self.assertEquals(30090, context_menu[1][0])
        download_re = re.compile('RunPlugin\(.+?mode=addToFavorites&talkID=42\)')
        self.assertTrue(download_re.match(context_menu[1][1]))

        