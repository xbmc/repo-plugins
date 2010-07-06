#!/usr/bin/env python
""" md5Hash_test.py
    Unit tests for md5Hash.py  (not the default python library!)
    MD5 defined in RFC 1321
"""

from   crypto.hash.md5Hash import MD5
import unittest
from binascii import a2b_hex

class MD5_TestCases(unittest.TestCase):
    """ MD5 tests from ..."""

    def testFIPS180_1_Appendix_A(self):
        """ APPENDIX A.  A SAMPLE MESSAGE AND ITS MESSAGE DIGEST """
        hashAlg = MD5()
        message        = 'abc'
        message_digest = '900150983cd24fb0d6963f7d28e17f72'
        md_string      = a2b_hex(message_digest)
        assert( hashAlg(message) == md_string ), 'md5 test Failed'

if __name__ == '__main__':
    # Run the tests from the command line
    unittest.main()


