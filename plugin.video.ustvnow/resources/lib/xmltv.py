"""
xmltv.py - Python interface to XMLTV format, based on XMLTV.pm

Copyright (C) 2001 James Oakley <jfunk@funktronics.ca>

This library is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this software; if not, see <http://www.gnu.org/licenses/>.
"""

import re, sys, types

if sys.hexversion >= 0x2050000:
    from xml.etree.cElementTree import ElementTree, Element, SubElement, tostring
else:
    try:
        from cElementTree import ElementTree, Element, SubElement, tostring
    except ImportError:
        from elementtree.ElementTree import ElementTree, Element, SubElement, tostring

# The Python-XMLTV version
VERSION = "1.4.3"

# The date format used in XMLTV (the %Z will go away in 0.6)
date_format = '%Y%m%d%H%M%S %Z'
date_format_notz = '%Y%m%d%H%M%S'


def set_attrs(dict, elem, attrs):
    """
    set_attrs(dict, elem, attrs) -> None

    Add any attributes in 'attrs' found in 'elem' to 'dict'
    """
    for attr in attrs:
        if attr in elem.keys():
            dict[attr] = elem.get(attr)

def set_boolean(dict, name, elem):
    """
    set_boolean(dict, name, elem) -> None

    If element, 'name' is found in 'elem', set 'dict'['name'] to a boolean
    from the 'yes' or 'no' content of the node
    """
    node = elem.find(name)
    if node is not None:
        if node.text.lower() == 'yes':
            dict[name] = True
        elif node.text.lower() == 'no':
            dict[name] = False

def append_text(dict, name, elem, with_lang=True):
    """
    append_text(dict, name, elem, with_lang=True) -> None

    Append any text nodes with 'name' found in 'elem' to 'dict'['name']. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is appended
    """
    for node in elem.findall(name):
        if not dict.has_key(name):
            dict[name] = []
        if with_lang:
            dict[name].append((node.text, node.get('lang', '')))
        else:
            dict[name].append(node.text)

def set_text(dict, name, elem, with_lang=True):
    """
    set_text(dict, name, elem, with_lang=True) -> None

    Set 'dict'['name'] to the text found in 'name', if found under 'elem'. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is set
    """
    node = elem.find(name)
    if node is not None:
        if with_lang:
            dict[name] = (node.text, node.get('lang', ''))
        else:
            dict[name] = node.text

def append_icons(dict, elem):
    """
    append_icons(dict, elem) -> None

    Append any icons found under 'elem' to 'dict'
    """
    for iconnode in elem.findall('icon'):
        if not dict.has_key('icon'):
            dict['icon'] = []
        icond = {}
        set_attrs(icond, iconnode, ('src', 'width', 'height'))
        dict['icon'].append(icond)


def elem_to_channel(elem):
    """
    elem_to_channel(Element) -> dict

    Convert channel element to dictionary
    """
    d = {'id': elem.get('id'),
         'display-name': []}

    append_text(d, 'display-name', elem)
    append_icons(d, elem)
    append_text(d, 'url', elem, with_lang=False)

    return d

def read_channels(fp=None, tree=None):
    """
    read_channels(fp=None, tree=None) -> list

    Return a list of channel dictionaries from file object 'fp' or the
    ElementTree 'tree'
    """
    if fp:
        et = ElementTree()
        tree = et.parse(fp)
    return [elem_to_channel(elem) for elem in tree.findall('channel')]


def elem_to_programme(elem):
    """
    elem_to_programme(Element) -> dict

    Convert programme element to dictionary
    """
    d = {'start': elem.get('start'),
         'channel': elem.get('channel'),
         'title': []}

    set_attrs(d, elem, ('stop', 'pdc-start', 'vps-start', 'showview',
                        'videoplus', 'clumpidx'))

    append_text(d, 'title', elem)
    append_text(d, 'sub-title', elem)
    append_text(d, 'desc', elem)

    crednode = elem.find('credits')
    if crednode is not None:
        creddict = {}
        # TODO: actor can have a 'role' attribute
        for credtype in ('director', 'actor', 'writer', 'adapter', 'producer',
                         'presenter', 'commentator', 'guest', 'composer',
                         'editor'):
            append_text(creddict, credtype, crednode, with_lang=False)
        d['credits'] = creddict

    set_text(d, 'date', elem, with_lang=False)
    append_text(d, 'category', elem)
    set_text(d, 'language', elem)
    set_text(d, 'orig-language', elem)

    lennode = elem.find('length')
    if lennode is not None:
        lend = {'units': lennode.get('units'),
                'length': lennode.text}
        d['length'] = lend

    append_icons(d, elem)
    append_text(d, 'url', elem, with_lang=False)
    append_text(d, 'country', elem)

    for epnumnode in elem.findall('episode-num'):
        if not d.has_key('episode-num'):
            d['episode-num'] = []
        d['episode-num'].append((epnumnode.text,
                                 epnumnode.get('system', 'xmltv_ns')))

    vidnode = elem.find('video')
    if vidnode is not None:
        vidd = {}
        for name in ('present', 'colour'):
            set_boolean(vidd, name, vidnode)
        for videlem in ('aspect', 'quality'):
            venode = vidnode.find(videlem)
            if venode is not None:
                vidd[videlem] = venode.text
        d['video'] = vidd

    audnode = elem.find('audio')
    if audnode is not None:
        audd = {}
        set_boolean(audd, 'present', audnode)
        stereonode = audnode.find('stereo')
        if stereonode is not None:
            audd['stereo'] = stereonode.text
        d['audio'] = audd

    psnode = elem.find('previously-shown')
    if psnode is not None:
        psd = {}
        set_attrs(psd, psnode, ('start', 'channel'))
        d['previously-shown'] = psd

    set_text(d, 'premiere', elem)
    set_text(d, 'last-chance', elem)

    if elem.find('new') is not None:
        d['new'] = True

    for stnode in elem.findall('subtitles'):
        if not d.has_key('subtitles'):
            d['subtitles'] = []
        std = {}
        set_attrs(std, stnode, ('type',))
        set_text(std, 'language', stnode)
        d['subtitles'].append(std)

    for ratnode in elem.findall('rating'):
        if not d.has_key('rating'):
            d['rating'] = []
        ratd = {}
        set_attrs(ratd, ratnode, ('system',))
        set_text(ratd, 'value', ratnode, with_lang=False)
        append_icons(ratd, ratnode)
        d['rating'].append(ratd)

    for srnode in elem.findall('star-rating'):
        if not d.has_key('star-rating'):
            d['star-rating'] = []
        srd = {}
        set_attrs(srd, srnode, ('system',))
        set_text(srd, 'value', srnode, with_lang=False)
        append_icons(srd, srnode)
        d['star-rating'].append(srd)

    for revnode in elem.findall('review'):
        if not d.has_key('review'):
            d['review'] = []
        rd = {}
        set_attrs(rd, revnode, ('type', 'source', 'reviewer',))
        set_text(rd, 'value', revnode, with_lang=False)
        d['review'].append(rd)

    return d

def read_programmes(fp=None, tree=None):
    """
    read_programmes(fp=None, tree=None) -> list

    Return a list of programme dictionaries from file object 'fp' or the
    ElementTree 'tree'
    """
    if fp:
        et = ElementTree()
        tree = et.parse(fp)
    return [elem_to_programme(elem) for elem in tree.findall('programme')]


def read_data(fp=None, tree=None):
    """
    read_data(fp=None, tree=None) -> dict

    Get the source and other info from file object fp or the ElementTree
    'tree'
    """
    if fp:
        et = ElementTree()
        tree = et.parse(fp)

    d = {}
    set_attrs(d, tree, ('date', 'source-info-url', 'source-info-name',
                        'source-data-url', 'generator-info-name',
                        'generator-info-url'))
    return d


def indent(elem, level=0):
    """
    Indent XML for pretty printing
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Writer:
    """
    A class for generating XMLTV data

    **All strings passed to this class must be Unicode, except for dictionary
    keys**
    """
    def __init__(self, encoding="UTF-8", date=None,
                 source_info_url=None, source_info_name=None,
                 generator_info_url=None, generator_info_name=None):
        """
        Arguments:

          'encoding' -- The text encoding that will be used.
                        *Defaults to 'UTF-8'*

          'date' -- The date this data was generated. *Optional*

          'source_info_url' -- A URL for information about the source of the
                               data. *Optional*

          'source_info_name' -- A human readable description of
                                'source_info_url'. *Optional*

          'generator_info_url' -- A URL for information about the program
                                  that is generating the XMLTV document.
                                  *Optional*

          'generator_info_name' -- A human readable description of
                                   'generator_info_url'. *Optional*

        """
        self.encoding = encoding
        self.data = {'date': date,
                     'source_info_url': source_info_url,
                     'source_info_name': source_info_name,
                     'generator_info_url': generator_info_url,
                     'generator_info_name': generator_info_name}

        self.root = Element('tv')
        for attr in self.data.keys():
            if self.data[attr]:
                self.root.set(attr, self.data[attr])

    def setattr(self, node, attr, value):
        """
        setattr(node, attr, value) -> None

        Set 'attr' in 'node' to 'value'
        """
        node.set(attr, value)

    def settext(self, node, text, with_lang=True):
        """
        settext(node, text) -> None

        Set 'node's text content to 'text'
        """
        if with_lang:
            if text[0] == None:
                node.text = None
            else:
                node.text = text[0]
            if text[1]:
                node.set('lang', text[1])
        else:
            if text == None:
                node.text = None
            else:
                node.text = text

    def seticons(self, node, icons):
        """
        seticon(node, icons) -> None

        Create 'icons' under 'node'
        """
        for icon in icons:
            if not icon.has_key('src'):
                raise ValueError("'icon' element requires 'src' attribute")
            i = SubElement(node, 'icon')
            for attr in ('src', 'width', 'height'):
                if icon.has_key(attr):
                    self.setattr(i, attr, icon[attr])


    def set_zero_ormore(self, programme, element, p):
        """
        set_zero_ormore(programme, element, p) -> None

        Add nodes under p for the element 'element', which occurs zero
        or more times with PCDATA and a 'lang' attribute
        """
        if programme.has_key(element):
            for item in programme[element]:
                e = SubElement(p, element)
                self.settext(e, item)

    def set_zero_orone(self, programme, element, p):
        """
        set_zero_ormore(programme, element, p) -> None

        Add nodes under p for the element 'element', which occurs zero
        times or once with PCDATA and a 'lang' attribute
        """
        if programme.has_key(element):
            e = SubElement(p, element)
            self.settext(e, programme[element])


    def addProgramme(self, programme):
        """
        Add a single XMLTV 'programme'

        Arguments:

          'programme' -- A dict representing XMLTV data
        """
        p = SubElement(self.root, 'programme')

        # programme attributes
        for attr in ('start', 'channel'):
            if programme.has_key(attr):
                self.setattr(p, attr, programme[attr])
            else:
                raise ValueError("'programme' must contain '%s' attribute" % attr)

        for attr in ('stop', 'pdc-start', 'vps-start', 'showview', 'videoplus', 'clumpidx'):
            if programme.has_key(attr):
                self.setattr(p, attr, programme[attr])

        for title in programme['title']:
            t = SubElement(p, 'title')
            self.settext(t, title)

        # Sub-title and description
        for element in ('sub-title', 'desc'):
            self.set_zero_ormore(programme, element, p)

        # Credits
        if programme.has_key('credits'):
            c = SubElement(p, 'credits')
            for credtype in ('director', 'actor', 'writer', 'adapter',
                             'producer', 'presenter', 'commentator', 'guest'):
                if programme['credits'].has_key(credtype):
                    for name in programme['credits'][credtype]:
                        cred = SubElement(c, credtype)
                        self.settext(cred, name, with_lang=False)

        # Date
        if programme.has_key('date'):
            d = SubElement(p, 'date')
            self.settext(d, programme['date'], with_lang=False)

        # Category
        self.set_zero_ormore(programme, 'category', p)

        # Language and original language
        for element in ('language', 'orig-language'):
            self.set_zero_orone(programme, element, p)

        # Length
        if programme.has_key('length'):
            l = SubElement(p, 'length')
            self.setattr(l, 'units', programme['length']['units'])
            self.settext(l, programme['length']['length'], with_lang=False)

        # Icon
        if programme.has_key('icon'):
            self.seticons(p, programme['icon'])

        # URL
        if programme.has_key('url'):
            for url in programme['url']:
                u = SubElement(p, 'url')
                self.settext(u, url, with_lang=False)

        # Country
        self.set_zero_ormore(programme, 'country', p)

        # Episode-num
        if programme.has_key('episode-num'):
            for epnum in programme['episode-num']:
                e = SubElement(p, 'episode-num')
                self.setattr(e, 'system', epnum[1])
                self.settext(e, epnum[0], with_lang=False)

        # Video details
        if programme.has_key('video'):
            e = SubElement(p, 'video')
            for videlem in ('aspect', 'quality'):
                if programme['video'].has_key(videlem):
                    v = SubElement(e, videlem)
                    self.settext(v, programme['video'][videlem], with_lang=False)
            for attr in ('present', 'colour'):
                if programme['video'].has_key(attr):
                    a = SubElement(e, attr)
                    if programme['video'][attr]:
                        self.settext(a, 'yes', with_lang=False)
                    else:
                        self.settext(a, 'no', with_lang=False)

        # Audio details
        if programme.has_key('audio'):
            a = SubElement(p, 'audio')
            if programme['audio'].has_key('stereo'):
                s = SubElement(a, 'stereo')
                self.settext(s, programme['audio']['stereo'], with_lang=False)
            if programme['audio'].has_key('present'):
                p = SubElement(a, 'present')
                if programme['audio']['present']:
                    self.settext(p, 'yes', with_lang=False)
                else:
                    self.settext(p, 'no', with_lang=False)

        # Previously shown
        if programme.has_key('previously-shown'):
            ps = SubElement(p, 'previously-shown')
            for attr in ('start', 'channel'):
                if programme['previously-shown'].has_key(attr):
                    self.setattr(ps, attr, programme['previously-shown'][attr])

        # Premiere / last chance
        for element in ('premiere', 'last-chance'):
            self.set_zero_orone(programme, element, p)

        # New
        if programme.has_key('new'):
            n = SubElement(p, 'new')

        # Subtitles
        if programme.has_key('subtitles'):
            for subtitles in programme['subtitles']:
                s = SubElement(p, 'subtitles')
                if subtitles.has_key('type'):
                    self.setattr(s, 'type', subtitles['type'])
                if subtitles.has_key('language'):
                    l = SubElement(s, 'language')
                    self.settext(l, subtitles['language'])

        # Rating
        if programme.has_key('rating'):
            for rating in programme['rating']:
                r = SubElement(p, 'rating')
                if rating.has_key('system'):
                    self.setattr(r, 'system', rating['system'])
                v = SubElement(r, 'value')
                self.settext(v, rating['value'], with_lang=False)
                if rating.has_key('icon'):
                    self.seticons(r, rating['icon'])

        # Star rating
        if programme.has_key('star-rating'):
            for star_rating in programme['star-rating']:
                sr = SubElement(p, 'star-rating')
                if star_rating.has_key('system'):
                    self.setattr(sr, 'system', star_rating['system'])
                v = SubElement(sr, 'value')
                self.settext(v, star_rating['value'], with_lang=False)
                if star_rating.has_key('icon'):
                    self.seticons(sr, rating['icon'])

        # Review
        if programme.has_key('review'):
            for review in programme['review']:
                r = SubElement(p, 'review')
                for attr in ('type', 'source', 'reviewer'):
                    if review.has_key(attr):
                        self.setattr(r, attr, review[attr])
                v = SubElement(r, 'value')
                self.settext(v, review['value'], with_lang=False)

    def addChannel(self, channel):
        """
        add a single XMLTV 'channel'

        Arguments:

          'channel' -- A dict representing XMLTV data
        """
        c = SubElement(self.root, 'channel')
        self.setattr(c, 'id', channel['id'])

        # Display Name
        for display_name in channel['display-name']:
            dn = SubElement(c, 'display-name')
            self.settext(dn, display_name)

        # Icon
        if channel.has_key('icon'):
            self.seticons(c, channel['icon'])

        # URL
        if channel.has_key('url'):
            for url in channel['url']:
                u = SubElement(c, 'url')
                self.settext(u, url, with_lang=False)

    def write(self, file, pretty_print=False):
        """
        write(file, pretty_print=False) -> None

        Write XML to filename of file object in 'file'. If pretty_print is
        True, the XML will contain whitespace to make it human-readable.
        """
        if pretty_print:
            indent(self.root)
        et = ElementTree(self.root)
        et.write(file, self.encoding, xml_declaration=True)

if __name__ == '__main__':
# Tests
    from pprint import pprint
    from StringIO import StringIO
    import sys

    # An example file
    xmldata = StringIO("""<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE tv SYSTEM "xmltv.dtd">
<tv date="20030811003608 -0300" source-info-url="http://www.funktronics.ca/python-xmltv" source-info-name="Funktronics" generator-info-name="python-xmltv" generator-info-url="http://www.funktronics.ca/python-xmltv">
  <channel id="C10eltv.zap2it.com">
    <display-name>Channel 10 ELTV</display-name>
    <url>http://www.eastlink.ca/</url>
  </channel>
  <channel id="C11cbht.zap2it.com">
    <display-name lang="en">Channel 11 CBHT</display-name>
    <icon src="http://tvlistings2.zap2it.com/tms_network_logos/cbc.gif"/>
  </channel>
  <programme start="20030702000000 ADT" channel="C23robtv.zap2it.com" stop="20030702003000 ADT">
    <title>This Week in Business</title>
    <category>Biz</category>
    <category>Fin</category>
    <date>2003</date>
    <audio>
      <stereo>stereo</stereo>
    </audio>
  </programme>
  <programme start="20030702000000 ADT" channel="C36wuhf.zap2it.com" stop="20030702003000 ADT">
    <title>Seinfeld</title>
    <sub-title>The Engagement</sub-title>
    <desc>In an effort to grow up, George proposes marriage to former girlfriend Susan.</desc>
    <category>Comedy</category>
    <country>USA</country>
    <language>English</language>
    <orig-language>English</orig-language>
    <premiere lang="en">Not really. Just testing</premiere>
    <last-chance>Hah!</last-chance>
    <credits>
      <actor>Jerry Seinfeld</actor>
      <producer>Larry David</producer>
      <composer>Jonathan Wolff</composer>
    </credits>
    <date>1995</date>
    <length units="minutes">22</length>
    <episode-num system="xmltv_ns">7 . 1 . 1/1</episode-num>
    <video>
      <colour>yes</colour>
      <present>yes</present>
      <aspect>4:3</aspect>
      <quality>standard</quality>
    </video>
    <audio>
      <stereo>stereo</stereo>
    </audio>
    <previously-shown start="19950921103000 ADT" channel="C12whdh.zap2it.com"/>
    <new/>
    <subtitles type="teletext">
      <language>English</language>
    </subtitles>
    <rating system="VCHIP">
      <value>PG</value>
      <icon src="http://some.ratings/PGicon.png" width="64" height="64"/>
    </rating>
    <star-rating>
      <value>4/5</value>
      <icon src="http://some.star/icon.png" width="32" height="32"/>
    </star-rating>
    <review type="url">
      <value>http://some.review/</value>
    </review>
    <url>http://www.nbc.com</url>
  </programme>
</tv>
""")
    pprint(read_data(xmldata))
    xmldata.seek(0)
    pprint(read_channels(xmldata))
    xmldata.seek(0)
    pprint(read_programmes(xmldata))

    # Test the writer
    programmes = [{'audio': {'stereo': u'stereo'},
                   'category': [(u'Biz', u''), (u'Fin', u'')],
                   'channel': u'C23robtv.zap2it.com',
                   'date': u'2003',
                   'start': u'20030702000000 ADT',
                   'stop': u'20030702003000 ADT',
                   'title': [(u'This Week in Business', u'')]},
                  {'audio': {'stereo': u'stereo'},
                   'category': [(u'Comedy', u'')],
                   'channel': u'C36wuhf.zap2it.com',
                   'country': [(u'USA', u'')],
                   'credits': {'producer': [u'Larry David'], 'actor': [u'Jerry Seinfeld']},
                   'date': u'1995',
                   'desc': [(u'In an effort to grow up, George proposes marriage to former girlfriend Susan.',
                             u'')],
                   'episode-num': [(u'7 . 1 . 1/1', u'xmltv_ns')],
                   'language': (u'English', u''),
                   'last-chance': (u'Hah!', u''),
                   'length': {'units': u'minutes', 'length': '22'},
                   'new': True,
                   'orig-language': (u'English', u''),
                   'premiere': (u'Not really. Just testing', u'en'),
                   'previously-shown': {'channel': u'C12whdh.zap2it.com',
                                        'start': u'19950921103000 ADT'},
                   'rating': [{'icon': [{'height': u'64',
                                         'src': u'http://some.ratings/PGicon.png',
                                         'width': u'64'}],
                               'system': u'VCHIP',
                               'value': u'PG'}],
                   'review': [{'type': 'url', 'value': 'http://some.review/'}],
                   'star-rating': [{'icon': [{'height': u'32',
                                             'src': u'http://some.star/icon.png',
                                             'width': u'32'}],
                                   'value': u'4/5'}],
                   'start': u'20030702000000 ADT',
                   'stop': u'20030702003000 ADT',
                   'sub-title': [(u'The Engagement', u'')],
                   'subtitles': [{'type': u'teletext', 'language': (u'English', u'')}],
                   'title': [(u'Seinfeld', u'')],
                   'url': [(u'http://www.nbc.com/')],
                   'video': {'colour': True, 'aspect': u'4:3', 'present': True,
                             'quality': 'standard'}}]

    channels = [{'display-name': [(u'Channel 10 ELTV', u'')],
                 'id': u'C10eltv.zap2it.com',
                 'url': [u'http://www.eastlink.ca/']},
                {'display-name': [(u'Channel 11 CBHT', u'en')],
                 'icon': [{'src': u'http://tvlistings2.zap2it.com/tms_network_logos/cbc.gif'}],
                 'id': u'C11cbht.zap2it.com'}]


    w = Writer(encoding="us-ascii",
               date="20030811003608 -0300",
               source_info_url="http://www.funktronics.ca/python-xmltv",
               source_info_name="Funktronics",
               generator_info_name="python-xmltv",
               generator_info_url="http://www.funktronics.ca/python-xmltv")
    for c in channels:
        w.addChannel(c)
    for p in programmes:
        w.addProgramme(p)
    w.write(sys.stdout, pretty_print=True)
