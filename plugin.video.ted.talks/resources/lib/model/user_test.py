import unittest
from user import User
import os
import fetcher
import tempfile
import sys

class TestUser(unittest.TestCase):
    
    def setUp(self):
        self.username = os.getenv("ted_username", None)
        self.password = os.getenv("ted_password", None)
        if (self.username == None or self.password == None):
            self.fail("Need to set ted_username and ted_password environment variables.")

    def test_login_success(self):
        cookieFile = tempfile.mkstemp()[1]
        try:
            os.remove(cookieFile)
            get_HTML = fetcher.Fetcher(lambda x: sys.stdout.write(x + '\n'), lambda x: cookieFile).getHTML
            user = User(get_HTML)
            # Weak assertions but don't want to tie to a particular user.
            userID, real_name = user.login(self.username, self.password)
            # Weak assertions but don't want to tie to a particular user.
            self.assertIsNotNone(userID)
            self.assertIsNotNone(real_name)
        finally:
            os.remove(cookieFile)

    def test_login_failure(self):
        cookieFile = tempfile.mkstemp()[1]
        try:
            os.remove(cookieFile)
            get_HTML = fetcher.Fetcher(lambda x: sys.stdout.write(x + '\n'), lambda x: cookieFile).getHTML
            user = User(get_HTML)
            userID, real_name = user.login(self.username, self.password + "not")
            self.assertIsNone(userID)
            self.assertIsNone(real_name)
        finally:
            os.remove(cookieFile)
        
    def test_no_credentials(self):
        user = User(get_HTML = None) # We won't try to get any HTML
        userID, real_name = user.login(None, None)
        self.assertIsNone(userID)
        self.assertIsNone(real_name)
