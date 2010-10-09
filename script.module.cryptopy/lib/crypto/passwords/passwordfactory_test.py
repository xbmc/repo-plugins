#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
""" crypto.passwords.passwordfactory_test

    Test classes for password generation

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.
"""
import unittest
from   crypto.passwords.passwordfactory import *

class Password_Generation_Tests_Basic(unittest.TestCase):

     def testPasswordFactorySimple(self):
         """ Just print a few to see how they look for now """
         print "==== PasswordFactorySimple ===="
         makePassword = PasswordFactorySimple("factorySpecificSeed",minSize=6, maxSize=10)
         print "minSize=%d  maxSize=%d  entropy=%d"% (makePassword.minSize,makePassword.maxSize,makePassword.entropy())
         for i in range(10):
             print makePassword(chr(i))

     def testPasswordFactoryReadable_01(self):
         """ Examples of PasswordFactoryReadable_01 """
         print "======== PasswordFactoryReadable_01 ========"
         makePassword = PasswordFactoryReadable_01("factorySpecificSeed",minSize=6, maxSize=10)
         print "minSize=%d  maxSize=%d  entropy=%d"% (makePassword.minSize,makePassword.maxSize,makePassword.entropy())
         for i in range(10):
             print makePassword(chr(i))

# Make this test module runnable from the command prompt
if __name__ == "__main__":
    unittest.main()
