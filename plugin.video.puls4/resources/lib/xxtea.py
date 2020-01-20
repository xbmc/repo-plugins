#/**********************************************************\
#|                                                          |
#| XXTEA.java                                               |
#|                                                          |
#| XXTEA encryption algorithm library for Java.             |
#|                                                          |
#| Encryption Algorithm Authors:                            |
#|      David J. Wheeler                                    |
#|      Roger M. Needham                                    |
#|                                                          |
#| Code Authors: Ma Bingyao <mabingyao@gmail.com>           |
#| LastModified: Mar 10, 2015                               |
#|                                                          |
#\**********************************************************/
# The MIT License (MIT)
#
# Copyright (c) 2008-2016 Ma Bingyao mabingyao@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

import base64
import sys

class Int32(int):
    def __init__(self, num=0): # initialising
        self.num = self.cap(num)
    def __str__(self):
        return str(self.num)
    def __repr__(self):
        return "Int32(" + self.__str__(delf) + ")"

    def __lt__(self, other):
        return self.num < other.num
    def __le__(self, other):
        return self.num <= other.num
    def __eq__(self, other):
        return self.num == other.num
    def __ne__(self, other):
        return self.num != other.num
    def __gt__(self, other):
        return self.num > other.num
    def __ge__(self, other):
        return self.num >= other.num

    def __add__(self, other):
        return Int32(self.cap(self.num + other.num))
    def __sub__(self, other):
        return Int32(self.cap(self.num - other.num))
    def __mul__(self, other):
        return Int32(self.cap(self.num * other.num))
    def __floordiv__(self, other):
        return Int32(self.cap(self.num // other.num))
    def __mod__(self, other):
        return Int32(self.cap(self.num % other.num))
    def __divmod__(self, other):
        return NotImplemented
    def __pow__(self, other):
        return Int32(self.cap(self.num ** other.num))
    def __lshift__(self, other):
        return Int32(self.cap(self.num << other.num))
    def __rshift__(self, other):
        if self.num < 0:
            return Int32(self.cap(((self.num & 2147483647)+2147483648) >> other.num))
        else:
            return Int32(self.cap(self.num >> other.num))
    def __and__(self, other):
        return Int32(self.cap(self.num & other.num))
    def __xor__(self, other):
        return Int32(self.cap(self.num ^ other.num))
    def __or__(self, other):
        return Int32(self.cap(self.num | other.num))
    @staticmethod
    def cap(num): # a method that handles an overflow/underflow
        if num > 2147483647 or num < -2147483648:
            if (num & 2147483648) == 2147483648:
                #negative
                leftover = num & 2147483647
                return -2147483648 + leftover#~(2147483648)
            else:
                #positv
                return num & 2147483647
        return num

#DELTA = b'/x9E3779B9'
DELTA = Int32(-1640531527)

# int MX(int sum, int y, int z, int p, int e, int[] k)
def MX(sum, y, z, p, e, k):
    return (z >> Int32(5) ^ y << Int32(2)) + (y >> Int32(3) ^ z << Int32(4)) ^ (sum ^ y) + (k[p & Int32(3) ^ e] ^ z)

# byte[] encryptbb(byte[] data, byte[] key)
def encryptbb(data, key):
    if (len(data) == 0):
        return data
    return toByteArray(encryptii(toIntArray(data, True), toIntArray(fixKey(key), False)), False)

# byte[] encryptsb(String data, byte[] key)
def encryptsb(data, key):
    return encryptbb(bytearray(data, 'utf-8'), key)

# byte[] encryptbs(byte[] data, String key)
def encryptbs(data, key):
    return encryptbb(data, bytearray(key, 'utf-8'))

# byte[] encryptss(String data, String key)
def encryptss(data, key):
    return encryptbb(bytearray(data, 'utf-8'), bytearray(key, 'utf-8'))

# String encryptToBase64Stringbb(byte[] data, byte[] key)
def encryptToBase64Stringbb(data, key):
    bytes = encryptbb(data, key)
    if (bytes == None):
        return None
    return base64.b64encode(bytes)

# String encryptToBase64Stringsb(String data, byte[] key)
def encryptToBase64Stringsb(data, key):
    bytes = encryptsb(data, key)
    if (bytes == None):
        return None
    return base64.b64encode(bytes)

# String encryptToBase64Stringbs(byte[] data, String key)
def encryptToBase64Stringbs(data, key):
    bytes = encryptbs(data, key)
    if (bytes == None):
        return None
    return base64.b64encode(bytes)

# String encryptToBase64Stringss(String data, String key)
def encryptToBase64Stringss(data, key):
    bytes = encryptss(data, key)
    if (bytes == None):
        return None
    return base64.b64encode(bytes)

# byte[] decryptbb(byte[] data, byte[] key)
def decryptbb(data,  key):
    if (len(data) == 0):
        return data
    return toByteArray(decryptii(toIntArray(data, False), toIntArray(fixKey(key), False)), True)

# byte[] decryptbs(byte[] data, String key)
def decryptbs(data, key):
    return decryptbb(data, bytearray(key, 'utf-8'))

# byte[] decryptBase64Stringsb(String data, byte[] key)
def decryptBase64Stringsb(data, key):
    return decryptbb(bytearray(base64.b64decode(data)), key)

# byte[] decryptBase64Stringss(String data, String key)
def decryptBase64Stringss(data, key):
    return decrypt(bytearray(base64.b64decode(data)), bytearray(key, 'utf-8'))

# String decryptToStringbb(byte[] data, byte[] key)
def decryptToStringbb(data, key):
    bytes = decryptbb(data, key)
    if (bytes == None):
        return None
    return str(bytes, "UTF-8")

# String decryptToStringbs(byte[] data, String key)
def decryptToStringbs(data, key):
    bytes = decryptbs(data, key)
    if (bytes == None):
        return None
    return str(bytes, "UTF-8")

# String decryptBase64StringToStringsb(String data, byte[] key)
def decryptBase64StringToStringsb(data, key):
    bytes = decryptbb(bytearray(base64.b64decode(data)), key)
    if (bytes == None):
        return None
    return str(bytes, "UTF-8")

# String decryptBase64StringToString(String data, String key)
def decryptBase64StringToStringss(data, key):
    bytes = decryptbs(bytearray(base64.b64decode(data)), key)
    if (bytes == None):
        return None
    return bytes.decode("utf-8")

# int[] encryptii(int[] v, int[] k)
def encryptii(v, k):
    n = Int32(len(v) - 1);
    if (n < Int32(1)):
        return v
    p = Int32(0)
    q = Int32(6) + Int32(52) // (n + Int32(1));
    z = v[n]
    y = Int32(0)
    sum = Int32(0)
    e = Int32(0)

    while (q > Int32(0)):
        q -= Int32(1)
        sum = sum + DELTA
        e = sum >> Int32(2) & Int32(3)
        for p in range(0, n.num):
            y = v[Int32.cap(p + 1)]
            #z = v[p] += MX(sum, y, z, p, e, k)
            v[p] += MX(sum, y, z, Int32(p), e, k)
            z = v[p]
        p = n.num
        y = v[0]
        #z = v[n] += MX(sum, y, z, p, e, k)
        v[n] += MX(sum, y, z, Int32(p), e, k)
        z = v[n]
    return v

# int[] decryptii(int[] v, int[] k)
def decryptii(v, k):
    n = Int32(len(v) - 1)
    if (n < Int32(1)):
        return v
    p = Int32(0)
    q = Int32(6) + (Int32(52) // (n + Int32(1)))
    z = Int32(0)
    y = v[0]
    sum = q * DELTA
    e = Int32(0)

    while (sum != Int32(0)):
        e = sum >> Int32(2) & Int32(3)

        for p in range(n.num, 0, -1):
            z = v[p - 1]
            #y = v[p] -= MX(sum, y, z, p, e, k)
            v[p] -= MX(sum, y, z, Int32(p), e, k)
            y = v[p]
        p = 0
        z = v[n]
        #y = v[0] -= MX(sum, y, z, p, e, k)
        v[0] -= MX(sum, y, z, Int32(p), e, k)
        y = v[0]
        sum = sum - DELTA
    return v

# byte[] fixKey(byte[] key)
def fixKey(key):
    if (len(key) == 16):
        return key
    fixedkey = bytearray(16)
    if (len(key) < 16):
        for b in range(len(key)):
            fixedkey[b] = key[b]
    else:
        fixedkey = key[0:16]
    return fixedkey

# int[] toIntArray(byte[] data, boolean includeLength)
def toIntArray(data, includeLength):
    n = Int32(0)
    if (Int32(len(data)) & Int32(3)) == Int32(0):
        n = Int32(len(data)) >> Int32(2)
    else:
            n = Int32((len(data)) >> Int32(2)) + Int32(1)
    result = []# []int

    if (includeLength):
        result = [Int32(0)]*(Int32.cap(n.num+1))
        result[n.num] = Int32(len(data))
    else:
        result = [Int32(0)]*n.num
    n = Int32(len(data))
    for i in range(0, n.num):
        # result[i >>> 2] |= (0x000000ff & data[i]) << ((i & 3) << 3)
        result[Int32(i) >> Int32(2)] |= (Int32(255) & Int32(data[i])) << ((Int32(i) & Int32(3)) << Int32(3))
    return result

# byte[] toByteArray(int[] data, boolean includeLength)
def toByteArray(data, includeLength):
    n = Int32(len(data)) << Int32(2)
    if (includeLength):
        m = data[len(data) - 1]
        n -= Int32(4)
        if ((m < n - Int32(3)) or (m > n)):
            return None
        n = m
    result = bytearray(n.num)
    for i in range(0, n.num):
        # result[i] = bytes([(data[i >>> 2] >>> ((i & 3) << 3))])
        temp = data[i >> 2] >> Int32((i & 3) << 3)
        result[i] = temp.num & 255
    return result
