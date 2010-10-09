#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.keyedHash.michael_test

    Tests of the Michael Message Integrity Check Algorithm

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""
from crypto.keyedHash.michael import Michael
from binascii import *
import unittest

class Michael_TestVectors(unittest.TestCase):
    """ Test MIC algorithm using know values """
    def testIEEE_BaseKnowValues(self):
        """ Test using vectors from IEEE P802.11i/D2.0 """
        def runSingleTest(key,data,micResult):
            print "============================="
            key = a2b_hex(key)
            knownMICResult = a2b_hex(micResult)
            print "key:      ",b2a_hex(key)
            print "data:     ",b2a_hex(data)
            print "knownMIC: ", b2a_hex(knownMICResult)
            micAlg = Michael(key)
            calculatedMIC = micAlg.hash(data)
            print "CalcMIC:  ", b2a_hex(calculatedMIC)
            self.assertEqual( calculatedMIC, knownMICResult )

            # alternate calling sequence
            micAlg = Michael()
            micAlg.setKey(key)
            calculatedMIC = micAlg.hash(data)
            self.assertEqual( calculatedMIC, knownMICResult )

            # yet another way to use algorithm
            calculatedMIC = micAlg(data)
            self.assertEqual( calculatedMIC, knownMICResult )

        runSingleTest( "0000000000000000", ""         , "82925c1ca1d130b8" )
        runSingleTest( "82925c1ca1d130b8", "M"        , "434721ca40639b3f" )
        runSingleTest( "434721ca40639b3f", "Mi"       , "e8f9becae97e5d29" )
        runSingleTest( "e8f9becae97e5d29", "Mic"      , "90038fc6cf13c1db" )
        runSingleTest( "90038fc6cf13c1db", "Mich"     , "d55e100510128986" )
        runSingleTest( "d55e100510128986", "Michael"  , "0a942b124ecaa546" )

class Michael_Check_Corners(unittest.TestCase):            
    def testShortKey(self):
        """ Check for assertion on short key """
        pass
    def testLongKey(self):
        """ Check for assertion on too long key """
        pass

if __name__ == '__main__':
    unittest.main()  # run all the tests


