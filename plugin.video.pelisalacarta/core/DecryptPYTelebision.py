# -*- coding: utf-8 -*-

import logger

class DecryptPYTelebision:
    __module__ = __name__

    def decrypt(self, str):
        strdcd = ''
        for letra in str:
            strdcd = (strdcd + chr((254 ^ ord(letra))))

        return strdcd



    def unescape(self, str):
        logger.info('decode %s' % str)
        strdcd = ''
        letras = str.split('%')
        letras.pop(0)
        for letra in letras:
            strdcd = (strdcd + chr(int(letra, 16)))

        return strdcd

