# -*- coding: utf8 -*-
"""
Todo : Due to performance reasons RDF data is parsed by string functions. 
       Perhaps there is a fast xml parser library?
"""

import os,sys,re
from os.path import join
import CharsetDecoder as decoder
from HTMLParser import HTMLParser

tag_set = {'persons' : 'MPReg:PersonDisplayName',
           'Iptc4xmpCore:Location' : 'Iptc4xmpCore:Location',
           'xmp:Label' : 'xmp:Label',
           'Image Rating' : 'xmp:Rating',
           'City' : 'photoshop:City',
           'country/primary location name' : 'photoshop:Country',
           'photoshop:DateCreated' : 'photoshop:DateCreated',
           'photoshop:Headline' : 'photoshop:Headline',
           'photoshop:State' : 'photoshop:State',
           #'MicrosoftPhoto:LastKeywordXMP' : 'MicrosoftPhoto:LastKeywordXMP',
           #'MicrosoftPhoto:LastKeywordIPTC' : 'MicrosoftPhoto:LastKeywordIPTC',
           'dc:creator' : 'dc:creator',
           'dc:description' : 'dc:description',
           'dc:rights' : 'dc:rights',
           'dc:subject' : 'dc:subject',
           'dc:title' : 'dc:title' }



class XMP_Tags(object):
    get_xmp_dirname = ''
    get_xmp_picfile = ''
    get_xmp_inner = ''
        
    def __get_xmp_metadata(self, dirname, picfile):
        
        #xmptag = 'x:xmpmeta'
        xmptag = 'rdf:RDF'

        self.get_xmp_dirname = dirname
        self.get_xmp_picfile = picfile
        
        try:
            f = open(join(dirname,picfile), 'rb')
        except:
            path = join(dirname.encode('utf-8'),picfile.encode('utf-8'))
            path = decoder.smart_unicode(path).encode('utf-8')
            f = open(path, 'rb')
        content = f.read()
        f.close()

        start = content.find("<" + xmptag)
        end   = content.rfind("</" + xmptag) + 4 + len(xmptag)
        inner = content[start:end]
        self.get_xmp_inner = inner
        """   
        if start != -1:
            end   = content.rfind("</" + xmptag) + 4 + len(xmptag)
            inner = content[start:end]
            self.get_xmp_inner = inner
        else:
            xmptag = 'x:xapmeta'
            start = content.find("<" + xmptag)
            end   = content.rfind("</" + xmptag) + 4 + len(xmptag)
            inner = content[start:end]
            self.get_xmp_inner = inner
         """

            
    def get_xmp(self, dirname, picfile):
        ###############################
        #    getting  XMP   infos     #
        ###############################
        xmp = {}
        for storedtag, tagname in tag_set.iteritems():
            #print "Tag: " + tagname + " for " + picfile
            if self.get_xmp_dirname != dirname or self.get_xmp_picfile != picfile:
                self.__get_xmp_metadata(dirname, picfile)

            start = self.get_xmp_inner.find("<" + tagname)
            end   = self.get_xmp_inner.rfind("</" + tagname) + 4 + len(tagname)
            inner = self.get_xmp_inner[start:end]
            
            #print "Innertag : " + inner
            
            j = 0
            people=''
            if start != -1 and end != -1:
                end = inner.find("</" + tagname)
                while end != -1:

                    start = inner.find(">")+1
                    if start == 0:
                        break

                    tag_found = inner[start:end]
                    i = 0
                    people = ''
                    while i < len(tag_found):
                        if ord(tag_found[i])!=0:
                            people += tag_found[i]
                        i += 1

                    if len(people):
                        try:
                            value = unicode(people, encoding='utf-8', errors='strict')
                        except:
                            value = unicode(people, encoding="cp1252", errors='replace')

                        #print "Value: " + value
                          
                        # find inner tags and delete them  <rdf:li[^>]*?>(.*?)</rdf:li>
                        matchouter=re.compile('<rdf:Alt[^>]*?>(.*?)</rdf:Alt>',re.DOTALL).findall(value)

                        if len(matchouter) == 0:
                            matchouter=re.compile('<rdf:Seq[^>]*?>(.*?)</rdf:Seq>',re.DOTALL).findall(value)
                        if len(matchouter) == 0:
                            matchouter=re.compile('<rdf:Bag[^>]*?>(.*?)</rdf:Bag>',re.DOTALL).findall(value)
                            
                        key = ''
                        
                        for outer in matchouter:
                            matchinner=re.compile('<rdf:li[^>]*?>(.*?)</rdf:li>',re.DOTALL).findall(outer)
                            for inner in matchinner:
                                inner = inner.strip(' \t\n\r')
                                if len(inner) > 0:
                                    if len(key) > 0:
                                        #print "1: " + inner
                                        key += '||' + inner
                                    else:
                                        #print "2: " + inner
                                        key = inner
                                    
                                value = key
                                
                        #print "3: " + value
                        if len(value) > 0:
                            value = HTMLParser().unescape(value)
                            if xmp.has_key(storedtag):
                                xmp[storedtag] += '||' + value
                            else:
                                xmp[storedtag] = value

                    inner = inner[end+1:]
                    start = inner.find("<" + tagname)
                    inner = inner[start:]
                    end = inner.find("</" + tagname)
                    j = j+ 1

        return xmp