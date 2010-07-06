#!/usr/bin/env python
"""  crypto.keyedHash.prf_dot11_test
	 Tests of the IEEE 802.11 PRF functions
"""
from crypto.keyedHash.prf_dot11 import PRF
import unittest
from   binascii_plus import b2a_hex, a2b_hex, b2a_p, a2b_p

class prf_TestVectors(unittest.TestCase):
	""" PRF from IEEE 802.11 testing known values """
	def testKnowValues(self):
		""" Test vectors from 11-02-298r0-I-suggested-changes-to-RSN.doc
		Modified to show prefix and correct length.
		"""
		for [key,data,digest,prf_know_value] in prfTestVectors:
			# the 298r test vectors do not include the prefix  :-(
			prefix = 'prefix'
			# remove white spaces and convert to binary string
			prf_value = a2b_p(prf_know_value)
			lengthInBits=8*len(prf_value)
			a_prf = PRF(key,prefix,data,lengthInBits)

			print 'key	 = ', b2a_p(key)
			print 'prefix = ', '"'+prefix+'"'
			print 'data   = ', b2a_p(data)
			print 'PRF	  = ', b2a_p(a_prf)
			print 'PRF_v  = ', b2a_p(prf_value)
			print 'len prf= ', len(a_prf)* 8
			self.assertEqual(a_prf, prf_value)

""" -------------- (key, data, digest, prf_value) ------------------ """
prfTestVectors =((a2b_hex('0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b'),
		  'Hi There',
		  'b617318655057264e28bc0b6fb378c8ef146be00',
		  'bcd4c650b30b9684951829e0d75f9d54'),
		 ('Jefe',
		  'what do ya want for nothing?',
		  'effcdf6ae5eb2fa2d27416d5f184df9c259a7c79',
		  """51f4de5b33f249adf81aeb713a3c20f4fe631446fabdfa58
			 244759ae58ef9009a99abf4eac2ca5fa87e692c440eb40023e
			 7babb206d61de7b92f41529092b8fc"""),
		 (20*chr(0xaa),
		  50*chr(0xdd), 				   #0xdd repeated 50 times
		  '125d7342b9ac11cd91a39af48aa17b4f63f175d3',
		  """e1ac546ec4cb636f9976487be5c86be17a0252ca5d8d8df12c
			 fb0473525249ce9dd8d177ead710bc9b590547239107aef7b4ab
			 d43d87f0a68f1cbd9e2b6f7607"""))



# Make this test module runnable from the command prompt
if __name__ == "__main__":
	unittest.main()

