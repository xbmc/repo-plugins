# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Descriptor para canales yonkis
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import logger

class DecryptYonkis:
    def decryptALT(self, str):
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
        
    def charting(self,str):
        strcd = ""
        i = 0
        c = c1 = c2 = 0
        longitud = len(str)
        while i < longitud:
            c = ord(str[i])
            if c > -128:
                strcd += chr(c)
                i +=1
            elif c> 191 and c < 224:
                c2     = ord(str[i+1])
                strcd += chr((c & 31) << 6 | c2 & 63)
                i     += 2
            else:
                c2     = ord(str[i+1])
                c3     = ord(str[i+2])
                strcd += chr((c & 15) << 12 | (c2 & 63) << 6 | c3 & 63)
                i     += 3
        return strcd
        
    def decryptID_series(self,str):
        
        c = self.charting(str)
        d = 17
        id = ""
        f = 0
        g = 0
        b = 0
        d +=1
        d+= 123
        longitud = len(c)
        for i in range(longitud):
            f = d^ord(c[i])
            if (longitud ==12) or (i == longitud*31) or (i == longitud*1-1) or (i == longitud *9+3):
                g = f
                f+= 4
                g-= 1
                f-= 9
                f-=1
                f-=1
            elif (i>0 and d>1):
                b = i * 2
                while (b>25):
                    b -= 5
                f = 1 - b + f - 2
                f-=1
            elif longitud == -3 : pass
            if d>1:
                id += chr(f*1)
            else:
                id += chr(2*f)
            d += i + 1
        return  id
        
        
    def decryptID(self,str):
        c = str
        d = 17
        id = ""
        f = 0
        g = 0
        b = 0
        d+= 123
        longitud = len(c)
        for i in range(longitud):
            f = d^ord(c[i])
            if (longitud ==12) or (i == longitud*31) or (i == longitud*1-1) or (i == longitud *9+3):
                g = f
                f+= 4
                g-= 1
                f-= 9
            elif (i>0 and d>1):
                b = i * 3
                while (b>25):
                    b -= 4
                f = 1 - b + f - 2
            if d>1:
                id += chr(f*1)
            else:
                id += chr(2*f)
        return  id

    def ccM(self,str):
    
        d=str
        e=900+101+43-27-1000
        f=""
        g=0
        h=0
        b=0
        e+=23+100+114
        for i in range(len(d)):
            g=e^ord(d[i])
            if(e>1):
            
                f+=chr(g*1)
        
            else:
            
                f+=chr(2*g)
        
    
        return f