import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from resources.lib.udacity import Udacity, UdacityAuth

class OfflineTest(unittest.TestCase):
    def test_return_true_when_cookies_and_token_are_set(self):
        auth = UdacityAuth(
            {'xsrf_token': 'SOMEVALUE',
             'cookies': 'ANOTHERVALUE'})
        self.assertTrue(auth.authenticate('test', 'pass'))


class ApiTests(unittest.TestCase):
    def test_get_lesson_contents(self):
        ud = Udacity(None)
        contents = ud.get_lesson_contents('308873795')
        self.assertTrue(type(contents) == list)
        self.assertTrue(type(contents[0]) == dict)

    def test_get_courses(self):
        ud = Udacity(None)
        courses = ud.get_courses(None)
        self.assertTrue(type(courses) == list)

    def test_get_courses_filters_results(self):
        level = 'Beginner'
        ud = Udacity(None)
        courses = ud.get_courses(level)
        self.assertTrue(all([c[2] == level for c in courses]))

    def test_get_course_contents(self):
        ud = Udacity(None)
        courses = ud.get_course_contents('cs215')
        self.assertTrue(type(courses) == list)
        self.assertTrue(len(courses[0]) == 3)


if __name__ == '__main__':
    unittest.main()
