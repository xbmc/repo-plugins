import json
import os
import unittest

from resources.lib.content.items import convert_to_items

__author__ = 'bromix'


class TestItems(unittest.TestCase):
    def test_missing_key_kind(self):
        working_path = os.getcwd()
        json_filename = os.path.join(working_path, 'result.json')
        json_file = open(json_filename)
        json_data = json.load(json_file, encoding='utf-8')
        json_file.close()

        convert_to_items(json_data)
        pass

    pass
