#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.tkip_fake_crc_test

	This module tests the creation of TKIP data that passes
	the WEP crc, but would fail the Michael MIC check.
	The IEEE TGi specification mandates a 60 second
	dissassociation of all sessions when two of these
	malicious packets are recieved in a 60 second period.

	Copyright © (c) 2003 by Paul A. Lambert.
	See LICENSE.txt for license terms of this software.
"""
import unittest
from crypto.cipher.tkip_encr import TKIP_encr
from crypto.common import xor
from binascii_plus import *
from zlib import crc32
from struct import pack, unpack

class TKIP_tkip_fake_crc_test(unittest.TestCase):
	""" Create TKIP encrypted data, modifiy it and patch the crc32 """
	def testTKIP_crc_modify(self):
		""" TKIP crc modification test """
		key = a2b_p( "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f" ) # the PMK
		ta	= a2b_p( "10 22 33 44 55 66" ) # the TK (key) is created from the iv and ta
		keyID = 0
		alg = TKIP_encr(key, ta, keyID)  # this is just the encryption algorithm with no Michael MIC
		plainText  = ''.join([chr(i) for i in range(20)]) # 20 octets (0 t 19)
		iv = a2b_p( "01 00 00 00 00 00" ) # the little-endian encoded PacketNumber
		cipherText = alg.encrypt(plainText, iv)

		ctHeader	   = cipherText[0:8]  # encoded iv and keyId
		ctData		   = cipherText[8:-4]
		ctCrcEncrypted = cipherText[-4:]  # just the encrypted crc fields

		# lets change the first octet of the data from 0x00 to 0x01
		base	= (len(ctData))*chr(0)
		baseCrc = crc32(base)
		bitMask = chr(1)+(len(ctData)-1)*chr(0)
		maskCrc = crc32(bitMask)

		maskedCt	 = xor(bitMask,ctData)
		maskedCtCrc  = crc32(maskedCt)

		print "--------------- make a modified packet and MIC ------------"
		print "plainText = %s "  % b2a_hex(plainText)
		print "cipherText= %s "  % b2a_hex(cipherText)
		print "ctData	 = %s "  % b2a_hex(ctData)
		print "ctxtCrc	 = %s "  % b2a_hex(ctCrcEncrypted)
		print "base 	 = %s " % b2a_hex(base)
		print "baseCrc	 = %0X" % baseCrc
		print "mask 	 = %s " % b2a_hex(bitMask)
		print "maskCrc	 = %0X" % maskCrc
		print "maskedCt = %s " % b2a_hex(maskedCt)
		print "maskCtCrc= %0X" % maskedCtCrc
		maskDiff = maskCrc ^ baseCrc
		newCtCrc = pack('<I', (maskDiff ^ unpack('<I',ctCrcEncrypted)[0]) )
		newCt = ctHeader + maskedCt + newCtCrc
		newPt = alg.decrypt(newCt)	 # this will raise an exception if the crc is 'bad'!
		print "newPt	 = %s " % b2a_hex(newPt)

	def test_TKIP_MIC_Analysis(self):
		""" Simple analysis of TKIP CRC attacks based on
			given Michael strength of 2^20
		"""
		michaelStrength = 2.**20   # probability of MIC attack from N.F.
		secondsPerHour	= 60.*60.
		secondsPerDay  = 24.*secondsPerHour
		secondsPerYear = 365.*secondsPerDay
		attacksPerSecond = 1.
		attacksPerYear	 = attacksPerSecond * secondsPerYear
		print "\n\n----  Michael Attack Analysis w/wo Countermeasures  ----"
		print "%s"%"Attacks  Number   Counter	 Mean"
		print "%s"%"  per	   of	  Measure	Success"
		print "%s"%"Second	  STAs	   Type 	 Time"
		print	   "------------------------------------"
		print	   "   1	   1	   none 	 %3d days" % (michaelStrength/secondsPerDay/attacksPerSecond)
		attacksPerSecond = 100
		print	   " 100	   1	   none 	 %3d hours" % (michaelStrength/secondsPerHour/attacksPerSecond)
		print	   " .016	   1  60sec/session 	 %3d year" % (michaelStrength/secondsPerYear/(1/60.))
		print	   " 100/60   100 60sec/session 	 %3d days" % (michaelStrength/secondsPerDay/(100./60.) )
		print	   " 100	   1	   none 	 %3d hours" % (michaelStrength/secondsPerHour/attacksPerSecond)



if __name__ == '__main__':
	# Run the tests from the command line
	unittest.main()

