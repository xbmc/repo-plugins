#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.icedoll_test

    Tests for icedoll encryption algorithm

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""
from crypto.cipher.icedoll  import Icedoll
from crypto.cipher.base     import noPadding
from binascii               import a2b_hex
from binascii_plus          import b2a_p, a2b_p
import unittest

class Icedoll_Basic_Tests(unittest.TestCase):
    """ Test Icedoll algorithm """

    def testDctEqPt(self):
        """ test of plaintext = decrypt(encrypt(plaintext)) """
        alg = Icedoll( 16*chr(0), padding=noPadding())
        pt  = 16*4*'a'             # block aligned
        ct  = alg.encrypt(pt)
        print 'ct  = ',b2a_p(ct)
        dct = alg.decrypt(ct)
        print 'dct = ',b2a_p(dct)
        assert(pt == dct), 'pt != dct'

        alg = Icedoll( 16*chr(0))  # autoPad
        pt  = 17*4*'a'             # non-block aligned
        ct  = alg.encrypt(pt)
        print 'ct  = ',b2a_p(ct)
        dct = alg.decrypt(ct)
        print 'dct = ',b2a_p(dct)
        assert(pt == dct), 'pt != dct'

    def testEncrcptDecryptMultiSizesPt(self):
        """ Encrypt decrypt multiple sizes """
        alg = Icedoll( 16*chr(0))
        for size in range(100):
            pt = size*'a'
            ct = alg.encrypt(pt)
            #print 'ct  = ',b2a_p(ct)
            dct = alg.decrypt(ct)
            #print 'dct = ',b2a_p(dct)
            assert(pt == dct), 'pt != dct'

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()


