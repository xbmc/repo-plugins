#!/usr/bin/env python

"""
Convert TTML subtitles to SubRip format
Creates .srt file with same base path as TTML file

usage: ttml2srt.py [-h] [--srt-ignore-colors] [--stdout]
                   ttml_file [ttml_file ...]

positional arguments:
  ttml_file

optional arguments:
  -h, --help            show this help message and exit
  --srt-ignore-colors   ignore subtitle text colors
  --stdout              print to stdout instead of creating .srt file
"""

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
from datetime import datetime
import argparse, codecs, os, re, sys
import time

class TTML2SRTParser(HTMLParser):
    """
    Parse TTML subtitles to SubRip format
    
    Usage: 
        
        parser = TTML2SRTParser()
        captions = parser.parse_file(ttml_fp, srt_ignore_colors)
        
            ttml_fp           = TTML file object opened by codecs.open()
            srt_ignore_colors = if true, ignore subtitle text colors
    
    TTML format example (from ITV Player):

    <?xml version="1.0" encoding="UTF-16"?>
    <tt xml:lang="en" xmlns="http://www.w3.org/ns/ttml" xmlns:ttp="http://www.w3.org/ns/ttml#parameter" xmlns:tts="http://www.w3.org/ns/ttml#styling" ttp:frameRate="25">
    <head>
    <styling>
    <style id="Swift" tts:color="white" tts:textAlign="center" tts:extent="720px 576px" tts:fontFamily="Courier New" tts:fontSize="18"/>
    </styling>
    </head>
    <body>
    <div style ="Swift">
    <p xml:id="0" xml:space="preserve" begin="00:00:07:14" end="00:00:09:14" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 21px">(BELL RINGS)</p>
    <p xml:id="1" xml:space="preserve" begin="00:01:00:12" end="00:01:02:22" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 21px"><span xml:space = "preserve" tts:color="cyan">Oh. Hello, Edith, dear.</span></p>
    <p xml:id="2" xml:space="preserve" begin="00:01:02:23" end="00:01:05:06" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 21px"><span xml:space = "preserve" tts:color="yellow">Hello, Granny. Isn't it exciting?</span></p>
    ...
    <p xml:id="645" xml:space="preserve" begin="00:47:31:02" end="00:47:35:07" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 19px">Other men have normal families.<br/><span xml:space = "preserve" tts:color="cyan">No family is ever what it seems.</span></p>
    <p xml:id="646" xml:space="preserve" begin="00:47:35:13" end="00:47:38:19" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 19px">Tell them I'm all right.<br/><span xml:space = "preserve" tts:color="yellow">Sybil? Hello?</span></p>
    <p xml:id="647" xml:space="preserve" begin="00:47:39:16" end="00:47:41:16" tts:backgroundColor="black" tts:fontSize="18px" tts:origin="0px 21px">itfc subtitles</p>
    </div>
    </body>
    </tt>
    """

    HEX_COLORS = {
        'black'   : '#000000',
        'blue'    : '#0000ff',
        'green'   : '#00ff00',
        'lime'    : '#00ff00',
        'aqua'    : '#00ffff',
        'cyan'    : '#00ffff',
        'red'     : '#ff0000',
        'fuchsia' : '#ff00ff',
        'magenta' : '#ff00ff',
        'yellow'  : '#ffff00',
        'white'   : '#ffffff'
    }
    
    SRT_TIME_FORMAT = '%H:%M:%S,%f'

    def parse_file(self, ttml_fp, srt_ignore_colors):
        self.srt_ignore_colors = srt_ignore_colors
        self.ttml_time_format = None
        self.frame_rate = 0
        self.use_frame_rate = False
        self.captions = []
        self.caption = None
        self.index = 0
        self.font_open = False
        self.last_color = ''
        self.feed(ttml_fp.read())
        return self.captions
    
    def handle_starttag(self, tag, attrs):
        if tag == 'tt':
            attribs = dict(attrs)
            if 'ttp:framerate' in attribs:
                self.frame_rate = float(attribs['ttp:framerate'])
        if tag == 'p':
            attribs = dict(attrs)
            if not self.caption:
                # determine time format from first entry
                if re.match(r'\d+(:\d+){3,3}', attribs['begin']):
                    if not self.frame_rate:
                        raise Exception('Frame rate not found')
                    self.ttml_time_format = "%H:%M:%S:%f"
                    self.use_frame_rate = True
                elif re.match(r'\d+(:\d+){2,2}\.\d+', attribs['begin']):
                    self.ttml_time_format = "%H:%M:%S.%f"
                elif re.match(r'\d+(:\d+){2,2}', attribs['begin']):
                    self.ttml_time_format = "%H:%M:%S"
                else:
                    raise Exception('Cannot determine TTML time format')
            begin = attribs['begin']
            end = attribs['end']
            if self.use_frame_rate:
                begin = re.sub(r'\.\d+$', '', begin)
                end = re.sub(r'\.\d+$', '', end)
            #00:00:25.484
            begin=datetime(2000,1,1,int(begin[0:2]),int(begin[3:5]),int(begin[6:8]),int(begin[9:12]))
            end=datetime(2000,1,1,int(end[0:2]),int(end[3:5]),int(end[6:8]),int(end[9:12]))
            if self.use_frame_rate:
                begin = begin.replace(microsecond=int(begin.microsecond / 10000.0 / self.frame_rate * 1000000))
                end = end.replace(microsecond=int(end.microsecond / 10000.0 / self.frame_rate * 1000000))
            self.caption = {}
            self.index += 1
            self.caption['index'] = self.index
            self.caption['begin'] = begin.strftime(self.SRT_TIME_FORMAT)            
            self.caption['begin'] = self.caption['begin'][0:9]+self.caption['begin'][-3:]            
            self.caption['end'] = end.strftime(self.SRT_TIME_FORMAT)
            self.caption['end'] = self.caption['end'][0:9]+self.caption['end'][-3:]
            self.caption['text'] = u''
        if not self.caption:
            return
        if tag == 'span':
            attribs = dict(attrs)
            if 'tts:color' in attribs:
                color = attribs['tts:color'].lower()
                if self.srt_ignore_colors:
                    if color != self.last_color:
                        if self.caption['text']:
                            self.caption['text'] += '\n- '
                    self.last_color = color
                else:
                    if color in self.HEX_COLORS:
                        self.caption['text'] += '<font color="' + self.HEX_COLORS[color] + '">'
                        self.font_open = True
                    elif re.match(r'#', color):
                        self.caption['text'] += '<font color="{}">'.format(color)
                        self.font_open = True
            else:
                if self.caption['text']:
                    self.caption['text'] += '\n- '
                self.last_color = ''
        elif tag == 'br':
            self.caption['text'] += '\n'

    def handle_endtag(self, tag):
        if not self.caption:
            return
        if tag == 'p':
            if self.srt_ignore_colors:
                self.last_color = ''
            self.caption['text'] = re.sub(r'\n\s+', '\n',  self.caption['text'])
            self.caption['text'] = re.sub(r'\s+\n', '\n',  self.caption['text'])
            self.caption['text'] = re.sub(r'\n</font>', '</font>\n',  self.caption['text'])
            self.caption['text'] = re.sub(r'\n\s+<font', '\n<font',  self.caption['text'])
            self.caption['text'] = self.caption['text'].strip()
            self.captions.append('%(index)s\n%(begin)s --> %(end)s\n%(text)s\n\n' % self.caption)
            self.caption = None
        elif tag == 'span':
            if self.font_open:
                self.caption['text'] += '</font>'
                self.font_open = False

    def handle_data(self, data):
        if not self.caption:
            return
        self.caption['text'] += data

    def handle_entityref(self, name):
        if not self.caption:
            return
        c = unichr(name2codepoint[name])
        self.caption['text'] += c

    def handle_charref(self, name):
        if not self.caption:
            return
        if name.startswith('x'):
            c = unichr(int(name[1:], 16))
        else:
            c = unichr(int(name))
        self.caption['text'] += c

# From: http://code.activestate.com/recipes/363841-detect-character-encoding-in-an-xml-file/
def detectXMLEncoding(fp):
    """ Attempts to detect the character encoding of the xml file
    given by a file object fp. fp must not be a codec wrapped file
    object!

    The return value can be:
        - if detection of the BOM succeeds, the codec name of the
        corresponding unicode charset is returned

        - if BOM detection fails, the xml declaration is searched for
        the encoding attribute and its value returned. the "<"
        character has to be the very first in the file then (it's xml
        standard after all).

        - if BOM and xml declaration fail, None is returned. According
        to xml 1.0 it should be utf_8 then, but it wasn't detected by
        the means offered here. at least one can be pretty sure that a
        character coding including most of ASCII is used :-/
    """
    ### detection using BOM
    
    ## the BOMs we know, by their pattern
    bomDict={ # bytepattern : name              
             (0x00, 0x00, 0xFE, 0xFF) : "utf_32_be",        
             (0xFF, 0xFE, 0x00, 0x00) : "utf_32_le",
             (0xFE, 0xFF, None, None) : "utf_16_be", 
             (0xFF, 0xFE, None, None) : "utf_16_le", 
             (0xEF, 0xBB, 0xBF, None) : "utf_8",
            }

    ## go to beginning of file and get the first 4 bytes
    oldFP = fp.tell()
    fp.seek(0)
    (byte1, byte2, byte3, byte4) = tuple(map(ord, fp.read(4)))

    ## try bom detection using 4 bytes, 3 bytes, or 2 bytes
    bomDetection = bomDict.get((byte1, byte2, byte3, byte4))
    if not bomDetection :
        bomDetection = bomDict.get((byte1, byte2, byte3, None))
        if not bomDetection :
            bomDetection = bomDict.get((byte1, byte2, None, None))

    ## if BOM detected, we're done :-)
    if bomDetection :
        fp.seek(oldFP)
        return bomDetection


    ## still here? BOM detection failed.
    ##  now that BOM detection has failed we assume one byte character
    ##  encoding behaving ASCII - of course one could think of nice
    ##  algorithms further investigating on that matter, but I won't for now.
    

    ### search xml declaration for encoding attribute
    import re

    ## assume xml declaration fits into the first 2 KB (*cough*)
    fp.seek(0)
    buffer = fp.read(2048)

    ## set up regular expression
    xmlDeclPattern = r"""
    ^<\?xml             # w/o BOM, xmldecl starts with <?xml at the first byte
    .+?                 # some chars (version info), matched minimal
    encoding=           # encoding attribute begins
    ["']                # attribute start delimiter
    (?P<encstr>         # what's matched in the brackets will be named encstr
     [^"']+              # every character not delimiter (not overly exact!)
    )                   # closes the brackets pair for the named group
    ["']                # attribute end delimiter
    .*?                 # some chars optionally (standalone decl or whitespace)
    \?>                 # xmldecl end
    """

    xmlDeclRE = re.compile(xmlDeclPattern, re.VERBOSE)

    ## search and extract encoding string
    match = xmlDeclRE.search(buffer)
    fp.seek(oldFP)
    if match :
        return match.group("encstr")
    else :
        return None

def ttml2srt(ttml_file, srt_ignore_colors, outfile):
    parser = TTML2SRTParser()   
    ttml_fp = open(ttml_file)
    ttml_encoding = detectXMLEncoding(ttml_fp)
    ttml_fp.close()
    if not ttml_encoding:
            raise Exception('cannot determine TTML file encoding: {}'.format(ttml_file))
    ttml_fp = codecs.open(ttml_file, 'r', ttml_encoding, 'ignore')
    srt_captions = parser.parse_file(ttml_fp, srt_ignore_colors)
    ttml_fp.close()
    srt_file = os.path.splitext(ttml_file)[0] + '.srt'
        
    srt_fp = codecs.open(outfile, 'w', 'utf_8', 'ignore')
    for srt_caption in srt_captions:
        srt_fp.write(srt_caption)
    
    srt_fp.close()

#def main():
#    arg_parser = argparse.ArgumentParser()
#    arg_parser.add_argument('ttml_file', nargs='+')
#    arg_parser.add_argument('--srt-ignore-colors', dest='srt_ignore_colors', action='store_true', help='ignore subtitle text colors')
#    arg_parser.add_argument('--stdout', action='store_true', help='print to stdout instead of creating .srt file')
#    args = arg_parser.parse_args()
 #   ttml2srt(args.ttml_file, args.srt_ignore_colors, args.stdout)

#if __name__ == '__main__':
#    main()
