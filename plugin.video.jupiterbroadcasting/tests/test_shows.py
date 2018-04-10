"""
Test Shows Module
Tests various show functionality
"""
import sys
import os
import unittest

# local imports here
import jb_shows

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

class TestShows(unittest.TestCase):
    """
    Add show based test methods to this class
    """

    def setUp(self):
        pass

    def test_show_integrity(self):
        """
        Checks to ensure each show object contains
        required Fields and that they are not none
        """

        error_msg = ("show name should be an int from resorces/langauges/"
                     "language/Strings.xml")

        shows = jb_shows.get_all_shows()
        for show_name, show in shows.iteritems():

            show_name_str = str(show_name)
            # verify index is int
            self.assertTrue(isinstance(show_name, (int, long)), error_msg)
            self.assertTrue(isinstance(show['plot'], (int, long)), error_msg)

            # if archive show, skip some asserts
            if show_name != 30025:
                self.assertNotEquals(show['feed'], "", show_name_str + " must have a feed")
                self.assertNotEquals(show['feed-low'], "", "Show " + show_name_str + "must have a feed-low")
                self.assertNotEquals(show['feed-audio'], "", "Show " + show_name_str + "must have a feed-audio")

            self.assertNotEquals(show['image'], "", "Show " + show_name_str + "must have an image")
            self.assertNotEquals(show['genre'], "", "Show " + show_name_str + "must have a genre")
            self.assertNotEquals(show['archived'], "", "Show " + show_name_str + "must have an archived state")

    def test_active_shows(self):
        """
        Verifies all shows returned are considered active
        """

        error_msg = "Should only return active show"
        shows = jb_shows.get_active_shows()
        for show_name, active_show in shows.iteritems():
            self.assertFalse(active_show['archived'], error_msg + str(show_name))

    def test_archived_shows(self):
        """
        Verifies all shows returned are considered active
        """

        error_msg = "Should only return archived show"
        shows = jb_shows.get_archived_shows()
        for show_name, archived_show in shows.iteritems():
            self.assertTrue(archived_show['archived'], error_msg + str(show_name))




    def test_show_sorting(self):
        """
        Tests soring of shows
        Uses a bogus show list as the translations
        happend in the default.py script with xbmc modules
        """

        special_char_name = '[should be first show]'
        special_char_name2 = '[should be second show]'
        alphabet_chars_name = 'should be first alphabetized'
        alphabet_chars_name2 = 'should be second alphabetized'
        translated_shows = {}

        translated_shows[special_char_name] = {}
        translated_shows[alphabet_chars_name] = {}
        translated_shows[special_char_name2] = {}
        translated_shows[alphabet_chars_name2] = {}

        # assert out of order
        unorderd_shows = translated_shows.items()
        self.assertNotEquals(special_char_name, unorderd_shows[0][0])
        self.assertNotEquals(special_char_name2, unorderd_shows[1][0])
        self.assertNotEquals(alphabet_chars_name, unorderd_shows[2][0])
        self.assertNotEquals(alphabet_chars_name2, unorderd_shows[3][0])

        sorted_shows = jb_shows.sort_shows(translated_shows)
        self.assertEquals(special_char_name, sorted_shows[0][0])
        self.assertEquals(special_char_name2, sorted_shows[1][0])
        self.assertEquals(alphabet_chars_name, sorted_shows[2][0])
        self.assertEquals(alphabet_chars_name2, sorted_shows[3][0])


# allows test execution
if __name__ == '__main__':
    unittest.main()
