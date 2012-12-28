# -*- coding: UTF-8 -*-
# coding: utf-8
'''
Created on 24 d�c. 2012

@author: DellDARMed
'''
from BeautifulSoup import BeautifulSoup
import HTMLParser
import htmlentitydefs
import random
import re
import string
import urllib
import urllib2
import urlparse

class Medi1Utils:    

    @staticmethod
    def unescape_page(text):
        text = text.decode('utf-8')
        text = HTMLParser.HTMLParser().unescape(text)
        text = text.encode('utf-8')
        return text

    @staticmethod
    def clear_html_tags(htmlElement):
        return ''.join(BeautifulSoup(htmlElement).findAll(text=True))
    @staticmethod
    def direct_thumb_link(imageurl):
        return imageurl.replace('..', 'http://www.medi1tv.com')

    @staticmethod
    def direct_thumb_link_large(imageurl):
        return Medi1Utils.direct_thumb_link(imageurl).replace("s.jpg", "l.jpg")

    # This method to generate random strings
    @staticmethod
    def id_generator(size=6, chars=string.ascii_letters):
        return ''.join(random.choice(chars) for x in range(size))

    # From "werkzeug" module : https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/urls.py
    @staticmethod
    def url_fix(s, charset='utf-8'):
        """Sometimes you get an URL by a user that just isn't a real
        URL because it contains unsafe characters like ' ' and so on.  This
        function can fix some of the problems in a similar way browsers
        handle data entered by the user:
    
        >>> url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
        'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'
    
        :param charset: The target charset for the URL if the url was
                        given as unicode string.
        """
        if isinstance(s, unicode):
            s = s.encode(charset, 'ignore')
        scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
        path = urllib.quote(path, '/%')
        qs = urllib.quote_plus(qs, ':&=')
        return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))
    
    import re, htmlentitydefs
    
   
    # #
    # Removes HTML or XML character references and entities from a text string.
    #
    # @param text The HTML (or XML) source text.
    # @return The plain text, as a Unicode string, if necessary.
    @staticmethod
    def unescape_page2(text):
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text  # leave as is
        return re.sub("&#?\w+;", fixup, text)
