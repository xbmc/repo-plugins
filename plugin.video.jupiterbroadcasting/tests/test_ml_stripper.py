"""
Test Feed Parser
"""
import sys
import os
import unittest

# local imports
import ml_stripper

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

class TestFeedParser(unittest.TestCase):
    """
    Add ml stripper test methods to this class
    """


    def setUp(self):
        pass

    def test_strip_paragraph_tag(self):
        """
        Verify <p> tags are removed from a string
        """

        expected_string = 'test description here'
        paragraph_string = '<p>' + expected_string + '</p>'

        self.assertEquals(expected_string, ml_stripper.html_to_text(paragraph_string))

    def test_no_tags_to_strip(self):
        """
        Verify content without html tags do not throw expection
        """

        expected_string = 'no html tags here'
        paragraph_string = expected_string

        self.assertEquals(expected_string, ml_stripper.html_to_text(paragraph_string))

    def test_unicode_character(self):
        """
        Verify a unicode character does not cause the html_to_text method to throw an error
        """

        unicode_string =  u'\u0420\u0024'
        ml_stripper.html_to_text(unicode_string)
