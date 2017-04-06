import unittest
import util

class TestUtil(unittest.TestCase):

    def test_resizeImage(self):
        self.assertEqual('feefifofum_389x292.jpg', util.resizeImage('feefifofum_132x99.jpg'))
        self.assertEqual('feefifofum_389x292.jpg', util.resizeImage('feefifofum_123x321.jpg'))
