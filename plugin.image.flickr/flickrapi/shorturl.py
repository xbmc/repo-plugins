# -*- coding: utf-8 -*-

'''Helper functions for the short http://fli.kr/p/... URL notation.

Photo IDs can be converted to and from Base58 short IDs, and a short
URL can be generated from a photo ID.

The implementation of the encoding and decoding functions is based on
the posts by stevefaeembra and Kohichi on
http://www.flickr.com/groups/api/discuss/72157616713786392/

'''

__all__ = ['encode', 'decode', 'url', 'SHORT_URL']

ALPHABET = u'123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
ALPHALEN = len(ALPHABET)
SHORT_URL = u'http://flic.kr/p/%s'


def encode(photo_id):
    '''encode(photo_id) -> short id
    
    >>> encode(u'4325695128')
    u'7Afjsu'
    >>> encode(u'2811466321')
    u'5hruZg'
    '''

    photo_id = int(photo_id)

    encoded = u''
    while photo_id >= ALPHALEN:
        div, mod = divmod(photo_id, ALPHALEN)
        encoded = ALPHABET[mod] + encoded
        photo_id = int(div)

    encoded = ALPHABET[photo_id] + encoded

    return encoded

def decode(short_id):
    '''decode(short id) -> photo id
    
    >>> decode(u'7Afjsu')
    u'4325695128'
    >>> decode(u'5hruZg')
    u'2811466321'
    '''

    decoded = 0
    multi = 1

    for i in xrange(len(short_id)-1, -1, -1):
        char = short_id[i]
        index = ALPHABET.index(char)
        decoded = decoded + multi * index
        multi = multi * len(ALPHABET)

    return unicode(decoded)

def url(photo_id):
    '''url(photo id) -> short url
    
    >>> url(u'4325695128')
    u'http://flic.kr/p/7Afjsu'
    >>> url(u'2811466321')
    u'http://flic.kr/p/5hruZg'
    '''

    short_id = encode(photo_id)
    return SHORT_URL % short_id



