from __future__ import absolute_import, unicode_literals
import unittest
from resources.lib.listing.listitem import PlayItem


class TestListItemModule(unittest.TestCase):

    def test_missing_title_raise_error(self):
        title = ""
        id = "1234"
        item_type = PlayItem.VIDEO_ITEM
        with self.assertRaises(ValueError):
            play_item = PlayItem(title, id, item_type) #pylint: disable=unused-variable

    def test_missing_id_raise_error(self):
        title = "Foo"
        id = ""
        item_type = PlayItem.VIDEO_ITEM
        with self.assertRaises(ValueError):
            play_item = PlayItem(title, id, item_type) #pylint: disable=unused-variable