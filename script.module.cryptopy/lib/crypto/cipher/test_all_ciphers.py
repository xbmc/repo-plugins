#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.cipher.test_all_ciphers

    All unit tests in the cipher package

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""
import unittest
import crypto.cipher.aes_cbc_test
import crypto.cipher.aes_test
import crypto.cipher.arc4_test
import crypto.cipher.cbc_test
import crypto.cipher.ccm_test
import crypto.cipher.icedoll_test
import crypto.cipher.rijndael_test
import crypto.cipher.tkip_encr_test
import crypto.cipher.tkip_fake_crc_test
import crypto.cipher.wep_test

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()



