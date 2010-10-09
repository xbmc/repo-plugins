# -*- coding: iso-8859-1 -*-
""" crypto.passwords.passwordfactory

    Python classes to create and recover passwords.  Currently contains
    simple password generation.  <need to merge the dictionary based pws>

    Copyright © (c) 2002 by Paul A. Lambert
    Read LICENSE.txt for license information.

    August 14, 2002
"""

from random import Random
from sha import sha    # the SHA1 algorithm for cryptographic hashing
from math import log, ceil
#from binascii_plus import b2a_p

class PasswordFactory:
    """ Make passwords using pseudo random seeds.
        Also used to recover passwords by using same pwSeed.
        If the seed is not saved, the password can not be recovered!!
    """
    def __init__(self, pwFactorySeed, minSize=10, maxSize=10 ):
        """ An abstract class to create passwords """
        self._factorySeed = pwFactorySeed
        self.minSize = minSize
        self.maxSize = maxSize
        self.rand = Random( self._factorySeed )

    def getPassword(self, pwSeed):
        raise "MUST be overloaded"

    def __call__(self, pwSeed):
        """ Create a new password as a 'call' """
        return self.getPassword(pwSeed)

    def entropy(self):
        """ Calculate the security of the password generation as a power of 2 """
        total = 0
        for pwSize in range(self.minSize, self.maxSize+1):
            total = total + self.passwordsForSize(pwSize)
        return powof2( total )

def powof2(x):
    """ Convert x to a power of 2 """
    return  log(x)/log(2)

class PasswordFactorySimple(PasswordFactory):
    """ This class implements a very secure but simple selection of numbers and letters.
        Some characters have been removed to prevent confusion between similar shapes
        The removed characters are: (O,0,o), (l,1,I) , (u,v),(U,V)
    """
    def __init__(self, pwFactorySeed, minSize=10, maxSize=10 ):
        """ Initialize password generation """
        PasswordFactory.__init__(self, pwFactorySeed, minSize, maxSize )
        self.lettersReduced    = 'abcdefghijkmnpqrstwxyzABCDEFGHJKLMNPQRSTWXYZ'
        self.digitsReduced     = '23456789'
        self.specialCharacters = '#%*+$'

    def getPassword(self, pwSeed):
        """ Create a new password from pwSeed. """
        self.rand.seed( pwSeed + 'getPassword' + self._factorySeed )   # reset prf sequence
        self.passwordSize = self.rand.randrange(self.minSize, self.maxSize+1)
        password = ''
        for i in range(self.passwordSize):
                password = password + self.rand.choice(self.lettersReduced+self.digitsReduced)
        return password

    def passwordsForSize(self,pwSize):
        return (len(self.lettersReduced)+len(self.digitsReduced))**pwSize

consonants_01 = 'bcdfghjklmnpqrstvwxz'
vowels_01 = 'aeiouy'
class PasswordFactoryReadable_01(PasswordFactory):
    """ Readable passwords created by alternating consonate/vowel/consonate ... etc.
    """
    def getPassword(self, pwSeed):
        """ Create a new password. Also used to recover passwords by using same pwSeed """
        #self.rand.seed( 'getPassword'+self.__factorySeed+pwSeed )   # reset prf sequence
        self.passwordSize = self.rand.randrange(self.minSize, self.maxSize+1)
        password = ''
        for i in range(self.passwordSize):
            if i == 0 :
                password = password + self.rand.choice(consonants_01)
            else:
                if password[-1] in consonants_01 :
                    password = password + self.rand.choice(vowels_01)
                else:
                    password = password + self.rand.choice(consonants_01)
        return password

    def passwordsForSize(self,pwSize):
        return (len(vowels_01)**(pwSize/2))*(len(consonants_01)**ceil(pwSize/2))


