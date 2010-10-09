#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.keyedHash.pbkdf2_test

    Unit tests for crypto.keyedHash.pbkdf2

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""

from crypto.keyedHash.pbkdf2 import pbkdf2, dot11PassPhraseToPSK
import unittest
from binascii_plus import a2b_p, b2a_p, b2a_hex,b2a_pter

class PBDKDF22_KnowAnswerTests(unittest.TestCase):
    """  """
    def pbkdf2KAT(self,testDescription, password, salt, iterations, keySize, ka):
        """ Know Answer Tests from IEEE """
        knownAnswer = a2b_p(ka) # convert ascii 2 binary
        derivedKey = pbkdf2(password, salt, iterations, keySize)
        print "========== %s ==========" % testDescription
        print 'password    = "%s"' % password
        print "salt/ssid   = %s" % b2a_pter(salt, frnt='              ')[15:]
        print "iterations  =", iterations
        print "keySize     =", keySize
        print "derivedKey  =", b2a_p(derivedKey, frnt='              ')[15:]
        #print "knownAnswer =", b2a_p(knownAnswer, frnt='              ')[15:]
        self.assertEqual(derivedKey, knownAnswer), "KAT Failed-> %s "% testDescription


    def testKnownAnswerRFC3211_1(self):
        description = "RFC3211 KAT Test 1"
        password    = "password"
        salt        = a2b_p("12 34 56 78 78 56 34 12")
        iterations  = 5
        keySize     = 8
        knownAnswer = "D1 DA A7 86 15 F2 87 E6"
        self.pbkdf2KAT(description, password, salt, iterations, keySize, knownAnswer)

    def testknownAnswerTGi_1(self):
        description = "pbkdf2 IEEE 802.11 TGi Test 1"
        password    = "password"
        ssid        = "IEEE"
        iterations  = 4096   # IEEE 802.11 TGi spcification
        keySize     = 32     # 32 bytes, 256 bits
        knownAnswer = """f4 2c 6f c5 2d f0 eb ef  9e bb 4b 90 b3 8a 5f 90
                         2e 83 fe 1b 13 5a 70 e2  3a ed 76 2e 97 10 a1 2e"""
        self.pbkdf2KAT(description, password, ssid, iterations, keySize, knownAnswer)

    def testknownAnswerTGi_2(self):
        description = "pbkdf2 IEEE 802.11 TGi Test 2"
        password    = "ThisIsAPassword"
        ssid        = "ThisIsASSID"
        iterations  = 4096   # IEEE 802.11 TGi spcification
        keySize     = 32     # 32 bytes, 256 bits
        knownAnswer = """0d c0 d6 eb 90 55 5e d6  41 97 56 b9 a1 5e c3 e3
                         20 9b 63 df 70 7d d5 08  d1 45 81 f8 98 27 21 af"""
        self.pbkdf2KAT(description, password, ssid, iterations, keySize, knownAnswer)

    def testknownAnswerTGi_3(self):
        description =   "pbkdf2 IEEE 802.11 TGi Test 3"
        password    =   "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ssid        =   "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
        iterations  = 4096   # IEEE 802.11 TGi spcification
        keySize     = 32     # 32 bytes, 256 bits
        knownAnswer = """be cb 93 86 6b b8 c3 83  2c b7 77 c2 f5 59 80 7c
                         8c 59 af cb 6e ae 73 48  85 00 13 00 a9 81 cc 62"""
        self.pbkdf2KAT(description, password, ssid, iterations, keySize, knownAnswer)

    def testDot11PassPhraseToPSK(self):
        passPhrase  =   "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ssid        =   "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
        knownAnswer = """be cb 93 86 6b b8 c3 83  2c b7 77 c2 f5 59 80 7c
                         8c 59 af cb 6e ae 73 48  85 00 13 00 a9 81 cc 62"""

        key = dot11PassPhraseToPSK( passPhrase, ssid )

        self.assertEqual( a2b_p(knownAnswer), key )

if __name__ == '__main__':
    # Run the tests from the command line
    unittest.main()


