#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.tkip_encr_test

	Tests for tkip encryption (mpdu only, no Michael)
	Copyright © (c) 2002 by Paul A. Lambert
	Read LICENSE.txt for license information.

	January 2003	   May have broken key mixing ...need to validate
	November 21, 2002
"""
import unittest
from crypto.cipher.tkip_encr import TKIP_encr
from crypto.keyedHash.tkip_key_mixing import TKIP_Mixer
from binascii_plus import a2b_p, b2a_p
from struct import pack

class TKIP_encr_TestVectors(unittest.TestCase):
	""" Test TKIP_encr algorithm using know values """

	def checkTKIPtestVector(self, description, key, ta, iv, plainText, cipherText):
		""" Process TKIP encryption test vectors (no MIC) """
		print '%s %s %s'%('='*((54-len(description))/2),description,'='*((54-len(description))/2))
		# Convert from octet lists to string
		key = a2b_p(key)
		ta	= a2b_p(ta)
		iv	= a2b_p(iv)
		pt	= a2b_p(plainText)
		kct = a2b_p(cipherText)
		mixer = TKIP_Mixer(key,ta)
		rc4key = mixer.newKey(iv)

		alg = TKIP_encr(key)
		alg.setTA(ta)

		print 'key:    %s'%b2a_p(key)[9:]
		print 'rc4Key  %s'%b2a_p(rc4key)[9:]  # calculated
		print 'ta:	%s'%b2a_p(ta)[9:]
		print 'iv:	%s'%b2a_p(iv)[9:]
		print 'pt:	%s'%b2a_p(pt)[9:]
		print 'kct:    %s'%b2a_p(kct)[9:]

		ct	= alg.encrypt(pt, iv)
		print 'ct:	%s'%b2a_p(ct)[9:]

		cpt = alg.decrypt(kct)
		print 'cpt:    %s'%b2a_p(cpt)[9:]

		print '========================================================'
		self.assertEqual( ct, kct )
		alg.setKey(key)
		dct = alg.decrypt( ct )
		self.assertEqual( dct, pt )

	def testTKIP_KnownAnswer_01(self):
		""" TKIP Known Answer #1
		   Hand created from GC example 1 to include MIC in plaintext
		   note - iv==0 """
		description  = "TKIP encr test 1 - all zero pn "
		key 		 = "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f"
		ta			 = "10 22 33 44 55 66"
		iv			 = "00 00 00 00 00 00"
		plainText  = """08 09 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17
						18 19 1a 1b
									9c 12 11 62  08 e9 a0 83"""
		cipherText = """00 20 00 20 00 00 00 00
						06 60 91 dc 37 82 31 ca 75 84 82 b6 54 b7 c5 3a
						81 4a cb bd 31 1e cc 3b 5c f7 df 69 53 0f c5 1b"""
		self.checkTKIPtestVector(description, key, ta, iv, plainText, cipherText)

	def XtestTKIP_KnownAnswer_02(self):
		""" TKIP Known Answer #2 """
		description  = "TKIP encr test 2"
		key 		 = "36 23 0f 41 40 20 c9 e3 02 cb 5d 5d 28 d5 ff bf"
		ta			 = "01 02 03 04 05 06"
		iv			 = b2a_p(pack('<Q',0x123456785BA0)[:6])
		rc4key			= "5b 7b a0 31 a1 b0 60 55 f3"
		plainText	 = """aa aa 03 00 00 00 08 00 45 00 00 4e 66 1a 00 00
						  80 11 be 64 0a 00 01 22 0a ff ff ff 00 89 00 89
						  00 3a 00 00 80 a6 01 10 00 01 00 00 00 00 00"""
		cipherText	 = """58 11 A0 20 78 56 34 12
						  12 86 13 90 94 44 88 49 a3 9f e1 48 e0 f4 f3 8f
						  78 ee de 66 c4 a2 8c a1 bd 39 00 7f 88 9b 95 c6
						  e6 9d cd 19 31 dc 25 61 c3 e1 9a d4 a6 4d 22
						  13 9b fa 26"""
		protectedMPDU = """08 41 23 01 01 02 03 04 05 06 01 02 03 04 05 06
				   01 22 33 44 55 66 00 00 a0 7b 5b 20 78 56 34 12
				   b8 2c 10 90 94 44 80 49 e6 9f e1 06 86 ee f3 8f
				   f8 ff 60 02 ce a2 8d 83 b7 c6 ff 80 88 12 95 4f
				   e6 a7 cd 19 b1 7a 24 71 c3 e0 9a d4 a6 4d 22 13
				   9b fa 26"""
		self.checkTKIPtestVector(description, key, ta, iv, plainText, cipherText)

if __name__ == '__main__':
	# Run the tests from the command line
	unittest.main()


