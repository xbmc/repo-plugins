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
        self.assertEquals(['Tan Le: My immigration story'], titles_1);

