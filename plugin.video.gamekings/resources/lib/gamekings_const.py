#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import xbmc
import xbmcaddon
from bs4 import BeautifulSoup


#
# Constants
# 
ADDON = "plugin.video.gamekings"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources')
BASE_URL_GAMEKINGS_TV = "https://www.gamekings.tv/"
TWITCH_URL_GAMEKINGS_TV = "https://player.twitch.tv/?channel=gamekings"
PREMIUM_ONLY_VIDEO_TITLE_PREFIX = '* '
LOGIN_URL = 'https://www.gamekings.tv/wp-login.php'
NUMBER_OF_ENCODED_DIGITS_FOR_ONE_DECRYPTED_DIGIT = 2
MASTER_DOT_M3U8 = "master.m3u8"
VQ4K = '4k'
VQ1080P = '1080p'
VQ720P = '720p'
VQ480P = '480p'
VQ360P = '360p'
VQ1080N = '1080n'
VQ720N = '720n'
VQ480N = '480n'
VQ360N = '360n'
HTTPSCOLONSLASHSLASH_ENCODED = "8647470737a3f2f27"
END_TAG = "</"
STREAM = "STREAM"
STOPDECODINGNOW = "STOPDECODINGNOW"
DATE = "2023-03-12"
VERSION = "1.2.23"


if sys.version_info[0] > 2:
    unicode = str


def convertToUnicodeString(s, encoding='utf-8'):
    """Safe decode byte strings to Unicode"""
    if isinstance(s, bytes):  # This works in Python 2.7 and 3+
        s = s.decode(encoding)
    return s


def convertToByteString(s, encoding='utf-8'):
    """Safe encode Unicode strings to bytes"""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def log(name_object, object):
    try:
        # Let's try and remove any non-ascii stuff first
        object = object.encode('ascii', 'ignore')
    except:
        pass

    try:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html,default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup


def decodeString(encoded_string):
    chunks = len(encoded_string)//NUMBER_OF_ENCODED_DIGITS_FOR_ONE_DECRYPTED_DIGIT
    chunk_size = NUMBER_OF_ENCODED_DIGITS_FOR_ONE_DECRYPTED_DIGIT
    decoded_string = ""
    for i in range(0, chunks * NUMBER_OF_ENCODED_DIGITS_FOR_ONE_DECRYPTED_DIGIT, chunk_size):
        encoded_chunk = encoded_string[i:i+chunk_size]

        decoded_digit = decryptEncodedDigit(encoded_chunk)

        # log("decoded_digit", decoded_digit)

        if decoded_digit == STOPDECODINGNOW:
            # exit the loop
            break

        decoded_string = decoded_string + str(decoded_digit)

        # log("decoded_string", decoded_string)

    # log("final decoded_string", decoded_string)

    return decoded_string


# No idea what kinda magic the encoding is.
# This is the encoding that should work for the m3u8 url part in the encoded container.
# It won't work on the rest of the container.
def decryptEncodedDigit(encoded_digit):
    key_value = {}
    key_value['16'] = 'a'
    key_value['26'] = 'b'
    key_value['36'] = 'c'
    key_value['46'] = 'd'
    key_value['56'] = 'e'
    key_value['66'] = 'f'
    key_value['76'] = 'g'
    key_value['86'] = 'h'
    key_value['96'] = 'I'
    key_value['A6'] = 'j'
    key_value['B6'] = 'k'
    key_value['C6'] = 'l'
    key_value['D6'] = 'm'
    key_value['E6'] = 'n'
    key_value['F6'] = 'o'
    key_value['07'] = 'p'
    key_value['17'] = 'q'
    key_value['27'] = 'r'
    key_value['37'] = 's'
    key_value['47'] = 't'
    key_value['57'] = 'u'
    key_value['67'] = 'v'
    key_value['77'] = 'w'
    key_value['87'] = 'x'
    key_value['97'] = 'y'
    key_value['A7'] = 'z'

    key_value['14'] = 'A'
    key_value['24'] = 'B'
    key_value['34'] = 'C'
    key_value['44'] = 'D'
    key_value['54'] = 'E'
    key_value['64'] = 'F'
    key_value['74'] = 'G'
    key_value['84'] = 'H'
    key_value['94'] = 'I'
    key_value['A4'] = 'J'
    key_value['B4'] = 'K'
    key_value['C4'] = 'L'
    key_value['D4'] = 'M'
    key_value['E4'] = 'N'
    key_value['F4'] = 'O'
    key_value['05'] = 'P'
    key_value['15'] = 'Q'
    key_value['25'] = 'R'
    key_value['35'] = 'S'
    key_value['45'] = 'T'
    key_value['55'] = 'U'
    key_value['65'] = 'V'
    key_value['75'] = 'W'
    key_value['85'] = 'X'
    key_value['95'] = 'Y'
    key_value['A5'] = 'Z'

    key_value['03'] = '0'
    key_value['13'] = '1'
    key_value['23'] = '2'
    key_value['33'] = '3'
    key_value['43'] = '4'
    key_value['53'] = '5'
    key_value['63'] = '6'
    key_value['73'] = '7'
    key_value['83'] = '8'
    key_value['93'] = '9'

    key_value['A3'] = ':'
    key_value['E2'] = '.'
    key_value['F2'] = '/'
    key_value['F5'] = '_'

    encoded_digit = str(encoded_digit).capitalize()

    # log("encoded_digit", encoded_digit)

    try:
        decoded_digit = key_value[encoded_digit]

        # log("decoded_digit", decoded_digit)

    # Only the encoded m3u8 url part in the container, can be decoded.
    # When we get a decoding error, we assume (ulp!) that we are past the m3u8 part and can quit decoding.
    except:

        log("exception while decoding this digit", encoded_digit)

        decoded_digit = STOPDECODINGNOW

    return decoded_digit