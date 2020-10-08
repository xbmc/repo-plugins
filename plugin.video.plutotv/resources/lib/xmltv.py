#   Copyright (C) 2020 Lunatixz
#
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

""" 
MODIFIED FROM
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

# The Python-XMLTV version
VERSION = "1.4.4"

# The date format used in XMLTV (the %Z will go away in 0.6)
date_format = '%Y%m%d%H%M%S %Z'
date_format_notz = '%Y%m%d%H%M%S'

from xml.etree.ElementTree import ElementTree, Element, SubElement, tostring
from kodi_six              import xbmcvfs

def set_attrs(d, elem, attrs):
    """
    set_attrs(d, elem, attrs) -> None

    Add any attributes in 'attrs' found in 'elem' to 'd'
    """
    for attr in attrs:
        if attr in elem:
            d[attr] = elem.get(attr)

def set_boolean(d, name, elem):
    """
    set_boolean(d, name, elem) -> None

    If element, 'name' is found in 'elem', set 'd'['name'] to a boolean
    from the 'yes' or 'no' content of the node
    """
    node = elem.find(name)
    if node is not None:
        if node.text.lower() == 'yes':
            d[name] = True
        elif node.text.lower() == 'no':
            d[name] = False

def append_text(d, name, elem, with_lang=True):
    """
    append_text(d, name, elem, with_lang=True) -> None

    Append any text nodes with 'name' found in 'elem' to 'd'['name']. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is appended
    """
    for node in elem.findall(name):
        if name not in d:
            d[name] = []
        if with_lang:
            d[name].append((node.text, node.get('lang', '')))
        else:
            d[name].append(node.text)

def set_text(d, name, elem, with_lang=True):
    """
    set_text(d, name, elem, with_lang=True) -> None

    Set 'd'['name'] to the text found in 'name', if found under 'elem'. If
    'with_lang' is 'True', a tuple of ('text', 'lang') is set
    """
    node = elem.find(name)
    if node is not None:
        if with_lang:
            d[name] = (node.text, node.get('lang', ''))
        else:
            d[name] = node.text

def append_icons(d, elem):
    """
    append_icons(d, elem) -> None

    Append any icons found under 'elem' to 'd'
    """
    for iconnode in elem.findall('icon'):
        if 'icon' not in d:
            d['icon'] = []
        if iconnode.get('src'):
            d['icon'].append({'src':iconnode.get('src')})
        # icond = {}
        # set_attrs(icond, iconnode, ('src', 'width', 'height'))

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
    channels = []
    if fp:
        et = ElementTree()
        tree = et.parse(fp)
    for elem in tree.findall('channel'):
        channel = elem_to_channel(elem) 
        try:
            channel['icon'] = [{'src':elem.findall('icon')[0].get('src')}]
        except:
            channel['icon'] = ''  #temp fix
        channels.append(channel)
    return channels


def elem_to_programme(elem):
    """
    elem_to_programme(Element) -> dict

    Convert programme element to dictionary
    """
    d = {'start': elem.get('start'),
         'stop': elem.get('stop'),
         'channel': elem.get('channel'),
         'title': [],
         'icon': []}

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
        if 'episode-num' not in d:
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
        if 'subtitles' not in d:
            d['subtitles'] = []
        std = {}
        set_attrs(std, stnode, ('type',))
        set_text(std, 'language', stnode)
        d['subtitles'].append(std)

    for ratnode in elem.findall('rating'):
        if 'rating' not in d:
            d['rating'] = []
        ratd = {}
        set_attrs(ratd, ratnode, ('system',))
        set_text(ratd, 'value', ratnode, with_lang=False)
        append_icons(ratd, ratnode)
        d['rating'].append(ratd)

    for srnode in elem.findall('star-rating'):
        if 'star-rating' not in d:
            d['star-rating'] = []
        srd = {}
        set_attrs(srd, srnode, ('system',))
        set_text(srd, 'value', srnode, with_lang=False)
        append_icons(srd, srnode)
        d['star-rating'].append(srd)

    for revnode in elem.findall('review'):
        if 'review' not in d:
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

          'source-info-url' -- A URL for information about the source of the
                               data. *Optional*

          'source-info-name' -- A human readable description of
                                'source-info-url'. *Optional*

          'generator-info-url' -- A URL for information about the program
                                  that is generating the XMLTV document.
                                  *Optional*

          'generator-info-name' -- A human readable description of
                                   'generator-info-url'. *Optional*

        """
        self.encoding = encoding
        self.data = {'date': date,
                     'source-info-url': source_info_url,
                     'source-info-name': source_info_name,
                     'generator-info-url': generator_info_url,
                     'generator-info-name': generator_info_name}

        self.root = Element('tv')
        for attr in self.data:
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
                node.text = ''
            else:
                node.text = text[0]
            if text[1]:
                node.set('lang', text[1])
        else:
            if text == None:
                node.text = ''
            else:
                node.text = text

    def seticons(self, node, icons):
        """
        seticon(node, icons) -> None

        Create 'icons' under 'node'
        """
        for icon in icons:
            if 'src' not in icon:
                raise ValueError("'icon' element requires 'src' attribute")
            i = SubElement(node, 'icon')
            for attr in ('src', 'width', 'height'):
                if attr in icon:
                    self.setattr(i, attr, icon[attr])


    def set_zero_ormore(self, programme, element, p):
        """
        set_zero_ormore(programme, element, p) -> None

        Add nodes under p for the element 'element', which occurs zero
        or more times with PCDATA and a 'lang' attribute
        """
        if element in programme:
            for item in programme[element]:
                e = SubElement(p, element)
                self.settext(e, item)

    def set_zero_orone(self, programme, element, p):
        """
        set_zero_ormore(programme, element, p) -> None

        Add nodes under p for the element 'element', which occurs zero
        times or once with PCDATA and a 'lang' attribute
        """
        if element in programme:
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
            if attr in programme:
                self.setattr(p, attr, programme[attr])
            else:
                raise ValueError("'programme' must contain '%s' attribute" % attr)

        for attr in ('stop', 'pdc-start', 'vps-start', 'showview', 'videoplus', 'clumpidx'):
            if attr in programme:
                self.setattr(p, attr, programme[attr])

        for title in programme['title']:
            t = SubElement(p, 'title')
            self.settext(t, title)

        # Sub-title and description
        for element in ('sub-title', 'desc'):
            self.set_zero_ormore(programme, element, p)

        # Credits
        if 'credits' in programme:
            c = SubElement(p, 'credits')
            for credtype in ('director', 'actor', 'writer', 'adapter',
                             'producer', 'presenter', 'commentator', 'guest'):
                if credtype in programme['credits']:
                    for name in programme['credits'][credtype]:
                        cred = SubElement(c, credtype)
                        self.settext(cred, name, with_lang=False)

        # Date
        if 'date' in programme:
            d = SubElement(p, 'date')
            self.settext(d, programme['date'], with_lang=False)

        # Category
        self.set_zero_ormore(programme, 'category', p)

        # Language and original language
        for element in ('language', 'orig-language'):
            self.set_zero_orone(programme, element, p)

        # Length
        if 'length' in programme:
            l = SubElement(p, 'length')
            self.setattr(l, 'units', programme['length']['units'])
            self.settext(l, programme['length']['length'], with_lang=False)

        # Icon
        if 'icon' in programme:
            self.seticons(p, programme['icon'])

        # URL
        if 'url' in programme:
            for url in programme['url']:
                u = SubElement(p, 'url')
                self.settext(u, url, with_lang=False)

        # Country
        self.set_zero_ormore(programme, 'country', p)

        # Episode-num
        if 'episode-num' in programme:
            for epnum in programme['episode-num']:
                e = SubElement(p, 'episode-num')
                self.setattr(e, 'system', epnum[1])
                self.settext(e, epnum[0], with_lang=False)

        # Video details
        if 'video' in programme:
            e = SubElement(p, 'video')
            for videlem in ('aspect', 'quality'):
                if videlem in programme['video']:
                    v = SubElement(e, videlem)
                    self.settext(v, programme['video'][videlem], with_lang=False)
            for attr in ('present', 'colour'):
                if attr in programme['video']:
                    a = SubElement(e, attr)
                    if programme['video'][attr]:
                        self.settext(a, 'yes', with_lang=False)
                    else:
                        self.settext(a, 'no', with_lang=False)

        # Audio details
        if 'audio' in programme:
            a = SubElement(p, 'audio')
            if 'stereo' in programme['audio']:
                s = SubElement(a, 'stereo')
                self.settext(s, programme['audio']['stereo'], with_lang=False)
            if 'present' in programme['audio']:
                p = SubElement(a, 'present')
                if programme['audio']['present']:
                    self.settext(p, 'yes', with_lang=False)
                else:
                    self.settext(p, 'no', with_lang=False)

        # Previously shown
        if 'previously-shown' in programme:
            ps = SubElement(p, 'previously-shown')
            for attr in ('start', 'channel'):
                if attr in programme['previously-shown']:
                    self.setattr(ps, attr, programme['previously-shown'][attr])

        # Premiere / last chance
        for element in ('premiere', 'last-chance'):
            self.set_zero_orone(programme, element, p)

        # New
        if 'new' in programme:
            n = SubElement(p, 'new')

        # Subtitles
        if 'subtitles' in programme:
            for subtitles in programme['subtitles']:
                s = SubElement(p, 'subtitles')
                if 'type' in subtitles:
                    self.setattr(s, 'type', subtitles['type'])
                if 'language' in subtitles:
                    l = SubElement(s, 'language')
                    self.settext(l, subtitles['language'])

        # Rating
        if 'rating' in programme:
            for rating in programme['rating']:
                r = SubElement(p, 'rating')
                if 'system' in rating:
                    self.setattr(r, 'system', rating['system'])
                v = SubElement(r, 'value')
                self.settext(v, rating['value'], with_lang=False)
                if 'icon' in rating:
                    self.seticons(r, rating['icon'])

        # Star rating
        if 'star-rating' in programme:
            for star_rating in programme['star-rating']:
                sr = SubElement(p, 'star-rating')
                if 'system' in star_rating:
                    self.setattr(sr, 'system', star_rating['system'])
                v = SubElement(sr, 'value')
                self.settext(v, star_rating['value'], with_lang=False)
                if 'icon' in star_rating:
                    self.seticons(sr, rating['icon'])

        # Review
        if 'review' in programme:
            for review in programme['review']:
                r = SubElement(p, 'review')
                for attr in ('type', 'source', 'reviewer'):
                    if attr in review:
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
        if 'icon' in channel:
            self.seticons(c, channel['icon'])

        # URL
        if 'url' in channel:
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
        et = ElementTree(self.root).getroot()
        fle = xbmcvfs.File(file, "wb")
        fle.write(tostring(et, encoding='utf8', method='xml').decode('utf-8'))
        fle.close()