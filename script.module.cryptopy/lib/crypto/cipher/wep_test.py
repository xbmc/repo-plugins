#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.wep_test

    Tests for wep encryption

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.

    2002-11-05
"""
import unittest
from crypto.cipher.wep import WEP
from binascii_plus import a2b_p, b2a_p
from zlib import crc32
from struct import pack

class WEP_TestVectors(unittest.TestCase):
    """ Test WEP algorithm using know values """
    def testKnowValues(self):
        """ Test using vectors from..."""
        def WEPtestVector(testCase,plainText,iv,key,keyId,cipherText):
            """ Process WEP test vectors from RFCxxxx"""
            print '%s %s %s'%('='*((54-len(testCase))/2),testCase,'='*((54-len(testCase))/2))
            # Convert from octet lists to string
            pt  = a2b_p(plainText)
            iv  = a2b_p(iv)
            key = a2b_p(key)
            kct = a2b_p(cipherText)

            alg = WEP(key,keyId=keyId)

            print 'key:    %s'%b2a_p(key)[9:]
            print 'keyId:  %x'%keyId
            print 'iv:     %s'%b2a_p(iv)[9:]
            print 'pt:     %s'%b2a_p(pt)[9:]
            print 'kct:    %s'%b2a_p(kct)[9:]

            ct  = alg.encrypt(pt, iv, keyId)
            print 'ct:     %s'%b2a_p(ct)[9:]
            print 'crc:    %s'%b2a_p(pack('<I',crc32(plainText)))[9:]

            print '========================================================'
            self.assertEqual( ct, kct )
            alg.setKey(key,keyId=keyId)
            dct = alg.decrypt( ct )
            self.assertEqual( dct, pt )

        WEPtestVector(
            testCase   = "Test Vectors from IEEE 802.11 TGi D2.x",
            plainText  = """aa aa 03 00 00 00 08 00 45 00 00 4e 66 1a 00 00
                            80 11 be 64 0a 00 01 22 0a ff ff ff 00 89 00 89
                            00 3a 00 00 80 a6 01 10 00 01 00 00 00 00 00 00
                            20 45 43 45 4a 45 48 45 43 46 43 45 50 46 45 45
                            49 45 46 46 43 43 41 43 41 43 41 43 41 43 41 41
                            41 00 00 20 00 01 """,
            iv         = "fb 02 9e",
            key        = "30 31 32 33 34",
            keyId      = 2,
            cipherText = """fb 02 9e 80
                            f6 9c 58 06 bd 6c e8 46 26 bc be fb 94 74 65 0a
                            ad 1f 79 09 b0 f6 4d 5f 58 a5 03 a2 58 b7 ed 22
                            eb 0e a6 49 30 d3 a0 56 a5 57 42 fc ce 14 1d 48
                            5f 8a a8 36 de a1 8d f4 2c 53 80 80 5a d0 c6 1a
                            5d 6f 58 f4 10 40 b2 4b 7d 1a 69 38 56 ed 0d 43
                            98 e7 ae e3 bf 0e 2a 2c a8 f7 """)

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()


