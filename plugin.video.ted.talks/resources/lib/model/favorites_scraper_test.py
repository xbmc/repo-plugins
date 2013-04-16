import unittest
from favorites_scraper import Favorites
import os
import sys
import tempfile
from fetcher import Fetcher
from user import User


class TestFavorites(unittest.TestCase):

    def setUp(self):
        self.username = os.getenv("ted_username", None)
        self.password = os.getenv("ted_password", None)
        if (self.username == None or self.password == None):
            self.fail("Need to set ted_username and ted_password environment variables.")
        # Use Fetcher and User to set up logged in cookie
        log_stdout = lambda x: sys.stdout.write(x + '\n')
        self.cookieFile = tempfile.mktemp()[1]
        get_HTML = Fetcher(log_stdout, lambda x: self.cookieFile).getHTML
        self.user = User(get_HTML)
        self.faves = Favorites(log_stdout, get_HTML)

    def tearDown(self):
        os.remove(self.cookieFile)
        unittest.TestCase.tearDown(self)

    def test_smoke(self):
        userID, realName = self.user.login(self.username, self.password)

        favorites_1 = list(self.faves.getFavoriteTalks(userID))
        self.assertTrue(len(favorites_1) > 0)
        # Relies on there being some favorites to start with
        titles_1 = [x[0] for x in favorites_1]

        talk_id = '1368'
        talk_title = 'Tan Le: My immigration story'
        if talk_title in titles_1:
            # Confusing out of sequence assertion but better this than running in a bad state.
            self.assertTrue(self.faves.removeFromFavorites(talk_id))
            # Assume it worked proper rather than hitting on TED __yet again__.
            titles_1.remove(talk_title)

        # Add to faves.
        self.assertTrue(self.faves.addToFavorites(talk_id))
        # moreginger: It works ATM but the favorites page only updates tardily,
        # so this step will fail. At some point the talk will appear on the page. Hmm.
        favorites_2 = list(self.faves.getFavoriteTalks(userID))
        titles_2 = [x[0] for x in favorites_2]
        self.assertEquals(titles_1 + ['Tan Le: My immigration story'], titles_2)

        # Remove from faves.
        self.assertTrue(self.faves.removeFromFavorites(talk_id))
        favorites_3 = list(self.faves.getFavoriteTalks(userID))
        titles_3 = [x[0] for x in favorites_3]
        self.assertEquals(titles_1, titles_3)
