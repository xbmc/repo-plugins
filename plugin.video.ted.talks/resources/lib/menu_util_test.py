import unittest
import menu_util

getLS = lambda x: x

class TestNewTalksRss(unittest.TestCase):

    def test_create_context_menu(self):
        context_menu = menu_util.create_context_menu(getLS)
        self.assertEquals([
            (30097, 'Action(queue)'),
            ('Toggle watched', 'Action(ToggleWatched)'),
            ], context_menu)
