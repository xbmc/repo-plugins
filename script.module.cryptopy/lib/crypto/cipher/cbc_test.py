#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.cbc_test

    Tests for cbc encryption, uses AES for base algorithm

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""

from crypto.cipher.cbc      import CBC
from crypto.cipher.aes      import AES
from crypto.cipher.rijndael import Rijndael
from crypto.cipher.base     import noPadding
import unittest
from binascii_plus          import b2a_hex, a2b_p, b2a_p

class CBC_AES128_TestVectors(unittest.TestCase):
    """ Test CBC with AES128 algorithm using know values """
    def testKnowValues(self):
        """ Test using vectors from NIST cbc_e_m.txt"""
        def CBCtestVector(key,iv,pt,kct):
            """ CBC test vectors using AES algorithm """
            key,iv,pt,kct = a2b_p(key),a2b_p(iv),a2b_p(pt),a2b_p(kct)
            alg = CBC(AES(key), padding=noPadding())

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

class CBC_Rijndael_Test(unittest.TestCase):
    """ CBC test with Rijndael """
    def testCBC_Rijndael_256(self):
        """  Rijndael CBC 256 """
        key =   '2b7e151628aed2a6abf7158809cf4f3c'
        iv  =   '000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f'
        pt  = """6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e51
                 30c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710"""
        key,iv,pt = a2b_p(key),a2b_p(iv),a2b_p(pt)
        alg = CBC(Rijndael(key, blockSize=32))
        ct = alg.encrypt(pt,iv=iv)
        self.assertEqual( alg.decrypt(iv+ct), pt )
    def testCBC_Rijndael_variable_data(self):
        """  Rijndael CBC 256 """
        key =   '2b7e151628aed2a6abf7158809cf4f3c'
        iv  =   '000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f'
        key,iv = a2b_p(key),a2b_p(iv)
        alg = CBC(Rijndael(key, blockSize=32))
        for i in range(100):
            pt = i*'a'
            ct = alg.encrypt(pt,iv=iv)
            self.assertEqual( alg.decrypt(iv+ct), pt )


class CBC_Auto_IV_Test(unittest.TestCase):
    """ CBC IV tests"""
    def testIVuniqueness(self):
        """  Test that two different instances have different IVs """
        key =   a2b_p('2b7e151628aed2a6abf7158809cf4f3c')
        pt  = "This is a test case"
        alg1 = CBC(Rijndael(key, blockSize=32))
        alg2 = CBC(Rijndael(key, blockSize=32))
        ct1 = alg1.encrypt(pt)
        ct2 = alg2.encrypt(pt)
        self.assertNotEqual( ct1,ct2 )
    def testIVmultencryptUnique(self):
        """  Test that two different encrypts have different IVs """
        key =   a2b_p('2b7e151628aed2a6abf7158809cf4f3c')
        pt  = "This is yet another test case"
        alg1 = CBC(Rijndael(key, blockSize=32))
        ct1 = alg1.encrypt(pt)
        ct2 = alg1.encrypt(pt)
        self.assertNotEqual( ct1, ct2 )
        self.assertEqual( alg1.decrypt(ct1), pt )
        self.assertEqual( alg1.decrypt(ct1), alg1.decrypt(ct2) )


class CBC_multipart_tests(unittest.TestCase):
    """ Test mulitple calls to encrypt/decrypt with moreData set """
    def testMultipassEncrypt(self):
        """ Test moreData usage """
        alg = CBC(Rijndael(16*chr(0), blockSize=32))
        ct1 = ''
        for i in range(129):
            ct1 += alg.encrypt('a',more=1)
        ct1 += alg.encrypt('')      # flush any remaining
        ct2 = alg.encrypt(129*'a')
        self.assertNotEqual( ct1, ct2 )
        pt1 = alg.decrypt(ct1)
        pt2 = alg.decrypt(ct2)
        self.assertEqual(pt1,pt2)

        pt3 = alg.decrypt('',more=1)
        for i in range(len(ct2)):
            pt3 += alg.decrypt(ct2[i], more=1)
        pt3 += alg.decrypt('')

class CBC_another_Simple_Test(unittest.TestCase):
    """ Test simple encrypt decrypt """
    def test(self):
        aes_cbc = CBC(AES())
        aes_cbc.setKey('aaaaaaaaaaaaaaaa')
        ct1 = aes_cbc.encrypt('test')
        ct2 = aes_cbc.encrypt('test') # note - auto iv, reslt is different ths time
        # text below from cli usage that failed :-(  ... bad sized message
        #aes_cbc.decrypt('U+f)f\xfb\x96\xc8vu\xbb\xff7BJ}')

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()


