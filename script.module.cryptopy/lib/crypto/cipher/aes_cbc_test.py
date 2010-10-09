#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.cbc_test

    Tests for cbc encryption, uses AES for base algorithm

    Copyright (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""

from crypto.cipher.aes_cbc import AES_CBC
from crypto.cipher.base import noPadding, padWithPadLen
import unittest
from binascii_plus import a2b_hex, b2a_hex, a2b_p

class AES_CBC_autoIV(unittest.TestCase):
    def testAutoIV(self):
        k   = a2b_hex('2b7e151628aed2a6abf7158809cf4f3c')
        alg = AES_CBC(key=k, padding=noPadding())
        pt  = a2b_hex('6bc1bee22e409f96e93d7e117393172a')
        ct  = alg.encrypt(pt)
        dct = alg.decrypt(ct)
        self.assertEqual( dct, pt )  # 'AES_CBC auto IV error'
    def testAutoIVandPadding(self):
        k   = a2b_hex('2b7e151628aed2a6abf7158809cf4f3c')
        alg = AES_CBC(key=k) # should default to padWithPadLen
        pt  = a2b_hex('6bc1bee22e409f96e93d7e117393172a')
        ct  = alg.encrypt(pt)
        dct = alg.decrypt(ct)
        self.assertEqual( dct, pt )  # 'AES_CBC auto IV and pad error'
    def testNonDupIV(self):
        """ Test to ensure that two instances of CBC don't get duplicate IV """
        k   = a2b_hex('2b7e151628aed2a6abf7158809cf4f3c')
        alg1 = AES_CBC(k)
        alg2 = AES_CBC(k)
        pt  = a2b_hex('6bc1bee22e409f96e93d7e117393172a')
        ct1  = alg1.encrypt(pt)
        ct2  = alg2.encrypt(pt)
        assert( ct1!= ct2 ), 'AES_CBC dup IV error'

class AES_CBC128_TestVectors(unittest.TestCase):
    """ Test AES_CBC128 algorithm using know values """
    def testKnowValues(self):
        """ Test using vectors from NIST """
        def CBCtestVector(key,iv,pt,kct):
            """ CBC test vectors using AES algorithm """
            key,iv,pt,kct = a2b_hex(key),a2b_hex(iv),a2b_p(pt),a2b_p(kct)
            alg = AES_CBC(key, padding=noPadding())

            self.assertEqual( alg.encrypt(pt,iv=iv), kct )
            self.assertEqual( alg.decrypt(iv+kct),   pt )

        # http://csrc.nist.gov/publications/nistpubs/800-38a/sp800-38a.pdf  page 34
        CBCtestVector( key = '2b7e151628aed2a6abf7158809cf4f3c',
                       iv  = '000102030405060708090a0b0c0d0e0f',
                       pt  = '6bc1bee22e409f96e93d7e117393172a',
                       kct = '7649abac8119b246cee98e9b12e9197d')
        # four blocks of data
        CBCtestVector( key =   '2b7e151628aed2a6abf7158809cf4f3c',
                       iv  =   '000102030405060708090a0b0c0d0e0f',
                       pt  = """6bc1bee22e409f96e93d7e117393172a
                                ae2d8a571e03ac9c9eb76fac45af8e51
                                30c81c46a35ce411e5fbc1191a0a52ef
                                f69f2445df4f9b17ad2b417be66c3710""",
                       kct = """7649abac8119b246cee98e9b12e9197d
                                5086cb9b507219ee95db113a917678b2
                                73bed6b8e3c1743b7116e69e22229516
                                3ff1caa1681fac09120eca307586e1a7""")



# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()


