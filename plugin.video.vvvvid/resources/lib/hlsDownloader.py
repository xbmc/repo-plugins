"""
Simple HTTP Live Streaming client.

References:
    http://tools.ietf.org/html/draft-pantos-http-live-streaming-08

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://sam.zoy.org/wtfpl/COPYING for more details.

Last updated: July 22, 2012
MODIFIED BY shani to make it work with F4mProxy
"""

import urlparse, urllib2, subprocess, os,traceback,cookielib,re,Queue,threading
import xml.etree.ElementTree as etree
import base64
from struct import unpack, pack
import sys
import io
import os
import time
import itertools
import xbmcaddon
import xbmc
import urllib2,urllib
import traceback
import urlparse
import posixpath
import re
import hmac
import hashlib
import binascii 
import zlib
from hashlib import sha256
import cookielib
import array

#from Crypto.Cipher import AES
'''
from crypto.cipher.aes      import AES
from crypto.cipher.cbc      import CBC
from crypto.cipher.base     import padWithPadLen
from crypto.cipher.rijndael import Rijndael
from crypto.cipher.aes_cbc import AES_CBC
'''
try:
    from Crypto.Cipher import AES
    USEDec=1 ## 1==crypto 2==local, local pycrypto
except:
    print 'pycrypt not available using slow decryption'
    USEDec=3 ## 1==crypto 2==local, local pycrypto

if USEDec==1:
    #from Crypto.Cipher import AES
    print 'using pycrypto'
elif USEDec==2:
    from decrypter import AESDecrypter
    AES=AESDecrypter()
else:
    from utils import python_aes
#from decrypter import AESDecrypter

iv=None
key=None
value_unsafe = '%+&;#'
VALUE_SAFE = ''.join(chr(c) for c in range(33, 127)
    if chr(c) not in value_unsafe)
    
SUPPORTED_VERSION=3

cookieJar=cookielib.LWPCookieJar()
clientHeader=None
    
class HLSDownloader():
    global cookieJar
    """
    A downloader for f4m manifests or AdobeHDS.
    """

    def __init__(self):
        self.init_done=False

    def init(self, out_stream, url, proxy=None,use_proxy_for_chunks=True,g_stopEvent=None, maxbitrate=0, auth=''):
        global clientHeader
        try:
            self.init_done=False
            self.init_url=url
            clientHeader=None
            self.status='init'
            self.proxy = proxy
            self.auth=auth
            if self.auth ==None or self.auth =='None' :
                self.auth=''
            if self.proxy and len(self.proxy)==0:
                self.proxy=None
            self.use_proxy_for_chunks=use_proxy_for_chunks
            self.out_stream=out_stream
            self.g_stopEvent=g_stopEvent
            self.maxbitrate=maxbitrate
            if '|' in url:
                sp = url.split('|')
                url = sp[0]
                clientHeader = sp[1]
                clientHeader= urlparse.parse_qsl(clientHeader)
                print 'header recieved now url and headers are',url, clientHeader 
            self.status='init done'
            self.url=url
            return self.preDownoload()
        except: 
            traceback.print_exc()
            self.status='finished'
        return False
        
    def preDownoload(self):
        
        print 'code here'
        return True
        
    def keep_sending_video(self,dest_stream, segmentToStart=None, totalSegmentToSend=0,startRange = 0):
        try:
            self.status='download Starting'
            downloadInternal(self.url,dest_stream,self.maxbitrate)
        except: 
            traceback.print_exc()
        self.status='finished'

        
    
    
def getUrl(url,timeout=20, returnres=False):
    global cookieJar
    global clientHeader
    try:
        post=None
        #print 'url',url
        
        #openner = urllib2.build_opener(urllib2.HTTPHandler, urllib2.HTTPSHandler)
        cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
        openner = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
        #print cookieJar

        if post:
            req = urllib2.Request(url, post)
        else:
            req = urllib2.Request(url)
        
        ua_header=False
        if clientHeader:
            for n,v in clientHeader:
                req.add_header(n,v)
                if n=='User-Agent':
                    ua_header=True

        if not ua_header:
            req.add_header('User-Agent','AppleCoreMedia/1.0.0.12B411 (iPhone; U; CPU OS 8_1 like Mac OS X; en_gb)')
        
        #req.add_header('X-Playback-Session-Id','9A1E596D-6AB6-435F-85D1-59BDD0E62D24')

        response = openner.open(req)
        
        if returnres: return response
        data=response.read()

        #print len(data)

        return data

    except:
        print 'Error in getUrl'
        traceback.print_exc()
        return None

def download_chunks(URL, chunk_size=4096, enc=False):
    #conn=urllib2.urlopen(URL)
    print 'starting download'
    if enc:
        if USEDec==1 :
            chunk_size*=1000
        else:
            chunk_size*=100
    else:
        chunk_size=chunk_size*10
    conn=getUrl(URL,returnres=True)
    while 1:
        if chunk_size==-1:
            data=conn.read()
        else:
            data=conn.read(chunk_size)
        if not data : return
        yield data
        if chunk_size==-1: return

    print 'function finished'

    if 1==2:
        data= conn.read()
        #print repr(data)
        #print 'data downloaded'
        for i in range(0,len(data), chunk_size):
            d=data[i:i+chunk_size]
            #print repr(d)
            yield d
            
        mod_index=len(data)%chunk_size;
        if mod_index>0 and mod_index <chunk_size :
            d=data[-mod_index:]
            yield d
        #print 'function finished'
        return
    
    #    data=conn.read(chunk_size)
    #    if not data: return
    #    yield data
    #print 'LEN of DATA %d'%len(data)
    #return data

def download_file(URL):
    return ''.join(download_chunks(URL))

def validate_m3u(conn):
    ''' make sure file is an m3u, and returns the encoding to use. '''
    return 'utf8'
    mime = conn.headers.get('Content-Type', '').split(';')[0].lower()
    if mime == 'application/vnd.apple.mpegurl':
        enc = 'utf8'
    elif mime == 'audio/mpegurl':
        enc = 'iso-8859-1'
    elif conn.url.endswith('.m3u8'):
        enc = 'utf8'
    elif conn.url.endswith('.m3u'):
        enc = 'iso-8859-1'
    else:
        raise Exception("Stream MIME type or file extension not recognized")
    if conn.readline().rstrip('\r\n') != '#EXTM3U':
        raise Exception("Stream is not in M3U format")
    return enc

def gen_m3u(url, skip_comments=True):
    global cookieJar
    #print url
    #url0="https://secure.en.beinsports.net/streaming/wab/multiformat/index.html?partnerId=1864&eventId=978267&xmlerrs=true&antiCache=1417448354098"
    #conn = getUrl(url0)#urllib2.urlopen(url)
    #url2= re.compile('streamLaunchCode>\s?.*?(http.*)\s?]]').findall(conn)[0]
    #print url2
    #url2="https://beinsportnet5-lh.akamaihd.net/i/bisusch332_0@99606/master.m3u8?reportingKey=eventId-978267_partnerId-1864&hdnea=st=1417475666~exp=1417475726~acl=/*~hmac=7ba8a95d718b62d0a5d83f2e3702c7e076c03825c8631242a9f777d58350199d"
    #conn = getUrl(url2)#urllib2.urlopen(url)
    #print conn
    #url=re.compile(',RESOLUTION=512x2.*\s?(.*?)\s').findall(conn)[0]
    conn = getUrl(url,returnres=True )#urllib2.urlopen(url)
    #print conn
    #conn=urllib2.urlopen(url)
    enc = validate_m3u(conn)
    #print conn
    for line in conn:#.split('\n'):
        line = line.rstrip('\r\n').decode(enc)
        if not line:
            # blank line
            continue
        elif line.startswith('#EXT'):
            # tag
            yield line
        elif line.startswith('#'):
            # comment
            if skip_comments:
                continue
            else:
                yield line
        else:
            # media file
            yield line

def parse_m3u_tag(line):
    if ':' not in line:
        return line, []
    tag, attribstr = line.split(':', 1)
    attribs = []
    last = 0
    quote = False
    for i,c in enumerate(attribstr+','):
        if c == '"':
            quote = not quote
        if quote:
            continue
        if c == ',':
            attribs.append(attribstr[last:i])
            last = i+1
    return tag, attribs

def parse_kv(attribs, known_keys=None):
    d = {}
    for item in attribs:
        k, v = item.split('=', 1)
        k=k.strip()
        v=v.strip().strip('"')
        if known_keys is not None and k not in known_keys:
            raise ValueError("unknown attribute %s"%k)
        d[k] = v
    return d

def handle_basic_m3u(url):
    global iv
    global key
    global USEDec
    seq = 1
    enc = None
    nextlen = 5
    duration = 5
    targetduration=5
    for line in gen_m3u(url):
        if line.startswith('#EXT'):
            tag, attribs = parse_m3u_tag(line)
            if tag == '#EXTINF':
                duration = float(attribs[0])
            elif tag == '#EXT-X-TARGETDURATION':
                assert len(attribs) == 1, "too many attribs in EXT-X-TARGETDURATION"
                targetduration = int(attribs[0])
                pass
            elif tag == '#EXT-X-MEDIA-SEQUENCE':
                assert len(attribs) == 1, "too many attribs in EXT-X-MEDIA-SEQUENCE"
                seq = int(attribs[0])
            elif tag == '#EXT-X-KEY':
                attribs = parse_kv(attribs, ('METHOD', 'URI', 'IV'))
                assert 'METHOD' in attribs, 'expected METHOD in EXT-X-KEY'
                if attribs['METHOD'] == 'NONE':
                    assert 'URI' not in attribs, 'EXT-X-KEY: METHOD=NONE, but URI found'
                    assert 'IV' not in attribs, 'EXT-X-KEY: METHOD=NONE, but IV found'
                    enc = None
                elif attribs['METHOD'] == 'AES-128':
                    assert 'URI' in attribs, 'EXT-X-KEY: METHOD=AES-128, but no URI found'
                    #from Crypto.Cipher import AES
                    key = download_file(attribs['URI'].strip('"'))
                    assert len(key) == 16, 'EXT-X-KEY: downloaded key file has bad length'
                    if 'IV' in attribs:
                        assert attribs['IV'].lower().startswith('0x'), 'EXT-X-KEY: IV attribute has bad format'
                        iv = attribs['IV'][2:].zfill(32).decode('hex')
                        assert len(iv) == 16, 'EXT-X-KEY: IV attribute has bad length'
                    else:
                        iv = '\0'*8 + struct.pack('>Q', seq)
                    
                    if not USEDec==3:
                        enc = AES.new(key, AES.MODE_CBC, iv)
                    else:
                        ivb=array.array('B',iv)
                        keyb= array.array('B',key)
                        enc=python_aes.new(keyb, 2, ivb)
                    #enc = AES_CBC(key)
                    #print key
                    #print iv
                    #enc=AESDecrypter.new(key, 2, iv)
                else:
                    assert False, 'EXT-X-KEY: METHOD=%s unknown'%attribs['METHOD']
            elif tag == '#EXT-X-PROGRAM-DATE-TIME':
                assert len(attribs) == 1, "too many attribs in EXT-X-PROGRAM-DATE-TIME"
                # TODO parse attribs[0] as ISO8601 date/time
                pass
            elif tag == '#EXT-X-ALLOW-CACHE':
                # XXX deliberately ignore
                pass
            elif tag == '#EXT-X-ENDLIST':
                assert not attribs
                yield None
                return
            elif tag == '#EXT-X-STREAM-INF':
                raise ValueError("don't know how to handle EXT-X-STREAM-INF in basic playlist")
            elif tag == '#EXT-X-DISCONTINUITY':
                assert not attribs
                print "[warn] discontinuity in stream"
            elif tag == '#EXT-X-VERSION':
                assert len(attribs) == 1
                if int(attribs[0]) > SUPPORTED_VERSION:
                    print "[warn] file version %s exceeds supported version %d; some things might be broken"%(attribs[0], SUPPORTED_VERSION)
            #else:
            #    raise ValueError("tag %s not known"%tag)
        else:
            yield (seq, enc, duration, targetduration, line)
            seq += 1

def player_pipe(queue, control,file):
    while 1:
        block = queue.get(block=True)
        if block is None: return
        file.write(block)
        file.flush()
        
def send_back(data,file):
    file.write(data)
    file.flush()
        
def downloadInternal(url,file,maxbitrate=0):
    global key
    global iv
    global USEDec
    dumpfile = None
    #dumpfile=open('c:\\temp\\myfile.mp4',"wb")
    variants = []
    variant = None
    for line in gen_m3u(url):
        if line.startswith('#EXT'):
            tag, attribs = parse_m3u_tag(line)
            if tag == '#EXT-X-STREAM-INF':
                variant = attribs
        elif variant:
            variants.append((line, variant))
            variant = None
    if len(variants) == 1:
        url = urlparse.urljoin(url, variants[0][0])
    elif len(variants) >= 2:
        print "More than one variant of the stream was provided."

        choice=-1
        lastbitrate=0
        print 'maxbitrate',maxbitrate
        for i, (vurl, vattrs) in enumerate(variants):
            print i, vurl,
            for attr in vattrs:
                key, value = attr.split('=')
                key = key.strip()
                value = value.strip().strip('"')
                if key == 'BANDWIDTH':
                    print 'bitrate %.2f kbps'%(int(value)/1024.0)
                    if int(value)<=int(maxbitrate) and int(value)>lastbitrate:
                        choice=i
                        lastbitrate=int(value)
                elif key == 'PROGRAM-ID':
                    print 'program %s'%value,
                elif key == 'CODECS':
                    print 'codec %s'%value,
                elif key == 'RESOLUTION':
                    print 'resolution %s'%value,
                else:
                    raise ValueError("unknown STREAM-INF attribute %s"%key)
            print
        if choice==-1: choice=0
        #choice = int(raw_input("Selection? "))
        print 'choose %d'%choice
        url = urlparse.urljoin(url, variants[choice][0])

    #queue = Queue.Queue(1024) # 1024 blocks of 4K each ~ 4MB buffer
    control = ['go']
    #thread = threading.Thread(target=player_pipe, args=(queue, control,file))
    #thread.start()
    last_seq = -1
    targetduration = 5
    changed = 0
    
    try:
        while 1==1:#thread.isAlive():
            medialist = list(handle_basic_m3u(url))
            playedSomething=False
            if None in medialist:
                # choose to start playback at the start, since this is a VOD stream
                pass
            else:
                # choose to start playback three files from the end, since this is a live stream
                medialist = medialist[-3:]
            #print medialist
            
            for media in medialist:
                if media is None:
                    #queue.put(None, block=True)
                    return
                seq, enc, duration, targetduration, media_url = media
                if seq > last_seq:
                    #print 'downloading.............',url
                    for chunk in download_chunks(urlparse.urljoin(url, media_url),enc=enc):
                        #print '1. chunk available %d'%len(chunk)
                        if enc: 
                             if not USEDec==3:
                                chunk = enc.decrypt(chunk)
                             else:
                                chunkb=array.array('B',chunk)
                                chunk = enc.decrypt(chunkb)
                                chunk="".join(map(chr, chunk))
                        #if enc: chunk = enc.decrypt(chunk,key,'CBC')
                        #print '2. chunk done %d'%len(chunk)
                        if dumpfile: dumpfile.write(chunk)
                        #queue.put(chunk, block=True)
                        send_back(chunk,file)
                        #print '3. chunk available %d'%len(chunk)
                    last_seq = seq
                    changed = 1
                    playedSomething=True
            
            '''if changed == 1:
                # initial minimum reload delay
                time.sleep(duration)
            elif changed == 0:
                # first attempt
                time.sleep(targetduration*0.5)
            elif changed == -1:
                # second attempt
                time.sleep(targetduration*1.5)
            else:
                # third attempt and beyond
                time.sleep(targetduration*3.0)
            
            changed -= 1
            '''
            if not playedSomething:
                xbmc.sleep(2000)
    except:
        control[0] = 'stop'
        raise

    