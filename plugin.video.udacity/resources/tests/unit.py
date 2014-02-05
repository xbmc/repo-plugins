import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from resources.lib.udacity import Udacity
from resources.lib.utils import widgets_to_answer


class MockWidget():
    def getContent(self):
        return True


class UnitTests(unittest.TestCase):
    def test_return_answer_data_from_list_of_widgets(self):
        mock_1 = MockWidget()
        mock_2 = MockWidget()
        widgets = [
            {'data': {'marker': True},
             'obj': mock_1},
            {'data': {'marker': True},
             'obj': mock_2},
        ]
        result = widgets_to_answer(widgets)
        self.assertTrue('submission' in result)
        self.assertTrue(result['submission']['parts'][0]['content'])

    def test_dont_fail_when_answer_data_empty(self):
        data = {
            '382888632': {
                'quiz_ref': {
                    'ref': 'Node',
                    'key': '381838603'
                },
                'answer_ref': None,
                'lecture_ref': None,
                'model': 'Exercise',
            },
            '313947755': {
                'steps_refs': [{
                    'key': '382888632'
                }],
            },
            '381838603': {'model': 'Quiz'},
        }
        udacity = Udacity(None)
        results = udacity.process_lesson_contents(data, '313947755')
        self.assertTrue(not results[0]['answer_ref'])

    def test_dont_fail_when_no_image_data(self):
        data = {
            'st101': {
                'title': 'Test 1',
                'catalog_entry': {
                    'subtitle': 'Making Decisions Based on Data',
                    'level': 'beginner',
                    '_image': None,
                    'short_summary': 'Summary!',
                },
                'model': 'Lesson',
                '_available': True
            }
        }
        udacity = Udacity(None)
        results = udacity.process_courses(data)
        # Check that the thumbnail field in the tuple is None
        self.assertTrue(results[0][3] is None)

    def test_only_include_available_courses(self):
        data = {
            'st101': {
                'title': 'Test 1',
                'catalog_entry': {
                    'subtitle': 'Making Decisions Based on Data',
                    'level': 'beginner',
                    '_image': None,
                    'short_summary': 'Summary!',
                },
                'model': 'Lesson',
                '_available': False
            }
        }
        udacity = Udacity(None)
        results = udacity.process_courses(data)
        # Check that the thumbnail field in the tuple is None
        self.assertTrue(len(results) == 0)

if __name__ == '__main__':
    unittest.main()
