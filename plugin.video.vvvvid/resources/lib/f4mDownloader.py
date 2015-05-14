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
#import youtube_dl
#from youtube_dl.utils import *
addon_id = 'plugin.video.vvvvid'
selfAddon = xbmcaddon.Addon(id=addon_id)
__addonname__   = selfAddon.getAddonInfo('name')
__icon__        = selfAddon.getAddonInfo('icon')
downloadPath   = xbmc.translatePath(selfAddon.getAddonInfo('profile'))#selfAddon["profile"])
F4Mversion=''
#from Crypto.Cipher import AES

value_unsafe = '%+&;#'
VALUE_SAFE = ''.join(chr(c) for c in range(33, 127)
    if chr(c) not in value_unsafe)
def urlencode_param(value):
    """Minimal URL encoding for query parameter"""
    return urllib.quote_plus(value, safe=VALUE_SAFE)
        
class FlvReader(io.BytesIO):
    """
    Reader for Flv files
    The file format is documented in https://www.adobe.com/devnet/f4v.html
    """
    indexString = 0
    def read_metadata_filesize(self):
        try:
            indexString = self.getvalue().index('filesize')
            self.read(indexString)
            self.read_string()
            return self.read_Number_to_double()
        except:
            return 0
    def read_metadata_duration(self):
        try:
            indexString = self.getvalue().index('duration')
            self.read(indexString)
            self.read_string()
            return self.read_Number_to_double()
        except:
            return 0
    def read_Number_to_double(self):
        return unpack('>d', self.read(8))[0]
    # Utility functions for reading numbers and strings
    def read_unsigned_long_long(self):
        return unpack('!Q', self.read(8))[0]
    def read_unsigned_int(self):
        return unpack('!I', self.read(4))[0]
    def read_unsigned_char(self):
        return unpack('!B', self.read(1))[0]
    def read_string(self):
        res = b''
        while True:
            char = self.read(1)
            if char == b'\x00':
                break
            res+=char
        return res

    def read_box_info(self):
        """
        Read a box and return the info as a tuple: (box_size, box_type, box_data)
        """
        real_size = size = self.read_unsigned_int()
        box_type = self.read(4)
        header_end = 8
        if size == 1:
            real_size = self.read_unsigned_long_long()
            header_end = 16
        return real_size, box_type, self.read(real_size-header_end)

    def read_asrt(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        quality_entry_count = self.read_unsigned_char()
        quality_modifiers = []
        for i in range(quality_entry_count):
            quality_modifier = self.read_string()
            quality_modifiers.append(quality_modifier)
        segment_run_count = self.read_unsigned_int()
        segments = []
        #print 'segment_run_count',segment_run_count
        for i in range(segment_run_count):
            first_segment = self.read_unsigned_int()
            fragments_per_segment = self.read_unsigned_int()
            segments.append((first_segment, fragments_per_segment))
        #print 'segments',segments
        return {'version': version,
                'quality_segment_modifiers': quality_modifiers,
                'segment_run': segments,
                }

    def read_afrt(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        time_scale = self.read_unsigned_int()
        quality_entry_count = self.read_unsigned_char()
        quality_entries = []
        for i in range(quality_entry_count):
            mod = self.read_string()
            quality_entries.append(mod)
        fragments_count = self.read_unsigned_int()
        #print 'fragments_count',fragments_count
        fragments = []
        for i in range(fragments_count):
            first = self.read_unsigned_int()
            first_ts = self.read_unsigned_long_long()
            duration = self.read_unsigned_int()
            if duration == 0:
                discontinuity_indicator = self.read_unsigned_char()
            else:
                discontinuity_indicator = None
            fragments.append({'first': first,
                              'ts': first_ts,
                              'duration': duration,
                              'discontinuity_indicator': discontinuity_indicator,
                              })
            print 'fragments'
        #print 'fragments',fragments
        return {'version': version,
                'time_scale': time_scale,
                'fragments': fragments,
                'quality_entries': quality_entries,
                }

    def read_abst(self, debug=False):
        version = self.read_unsigned_char()
        self.read(3) # flags
        bootstrap_info_version = self.read_unsigned_int()
        streamType=self.read_unsigned_char()#self.read(1) # Profile,Live,Update,Reserved
        islive=False
        if (streamType & 0x20) >> 5:
            islive=True
        print 'LIVE',streamType,islive
        time_scale = self.read_unsigned_int()
        current_media_time = self.read_unsigned_long_long()
        smpteTimeCodeOffset = self.read_unsigned_long_long()
        movie_identifier = self.read_string()
        server_count = self.read_unsigned_char()
        servers = []
        for i in range(server_count):
            server = self.read_string()
            servers.append(server)
        quality_count = self.read_unsigned_char()
        qualities = []
        for i in range(server_count):
            quality = self.read_string()
            qualities.append(server)
        drm_data = self.read_string()
        metadata = self.read_string()
        segments_count = self.read_unsigned_char()
        #print 'segments_count11',segments_count
        segments = []
        for i in range(segments_count):
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'asrt'
            segment = FlvReader(box_data).read_asrt()
            segments.append(segment)
        fragments_run_count = self.read_unsigned_char()
        #print 'fragments_run_count11',fragments_run_count
        fragments = []
        for i in range(fragments_run_count):
            # This info is only useful for the player, it doesn't give more info 
            # for the download process
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'afrt'
            fragments.append(FlvReader(box_data).read_afrt())
    
        return {'segments': segments,
                'movie_identifier': movie_identifier,
                'drm_data': drm_data,
                'fragments': fragments
                },islive

    def read_bootstrap_info(self):
        """
        Read the bootstrap information from the stream,
        returns a dict with the following keys:
        segments: A list of dicts with the following keys
            segment_run: A list of (first_segment, fragments_per_segment) tuples
        """
        total_size, box_type, box_data = self.read_box_info()
        assert box_type == b'abst'
        return FlvReader(box_data).read_abst()

def read_bootstrap_info(bootstrap_bytes):
    return FlvReader(bootstrap_bytes).read_bootstrap_info()

def build_fragments_list(boot_info,total_size,total_duration,startFromFregment=None, live=True):
    """ Return a list of (segment, fragment) for each fragment in the video """
    res = []
    segment_run_table = boot_info['segments'][0]
    #print 'segment_run_table',segment_run_table
    # I've only found videos with one segment
    #if len(segment_run_table['segment_run'])>1:
    #    segment_run_table['segment_run']=segment_run_table['segment_run'][-2:] #pick latest

    
    frag_start = boot_info['fragments'][0]['fragments']
    #print boot_info['fragments']
 
 
    
#    sum(j for i, j in segment_run_table['segment_run'])
    
    first_frag_number=frag_start[0]['first']
    last_frag_number=frag_start[-1]['first']
    if last_frag_number==0:
        last_frag_number=frag_start[-2]['first']
    endfragment=0
    segment_to_start=None
    for current in range (len(segment_run_table['segment_run'])):
        seg,fregCount=segment_run_table['segment_run'][current]
        #print 'segmcount',seg,fregCount
        if (not live):
            frag_end=last_frag_number
        else:
            frag_end=first_frag_number+fregCount-1
            if fregCount>10000:
                frag_end=last_frag_number
        #if frag_end

            
        
        segment_run_table['segment_run'][current]=(seg,fregCount,first_frag_number,frag_end)
        if (not startFromFregment==None) and startFromFregment>=first_frag_number and startFromFregment<=frag_end:
            segment_to_start=current
        first_frag_number+=fregCount
    #if we have no index then take the last segment
    if segment_to_start==None:
        segment_to_start=len(segment_run_table['segment_run'])-1
        #if len(segment_run_table['segment_run'])>2:
        #    segment_to_start=len(segment_run_table['segment_run'])-2;
        if live:
            if len(boot_info['fragments'][0]['fragments'])>1: #go bit back
                startFromFregment= boot_info['fragments'][0]['fragments'][-1]['first']
        else:
            startFromFregment= boot_info['fragments'][0]['fragments'][0]['first'] #start from begining
            
        #if len(boot_info['fragments'][0]['fragments'])>2: #go little bit back
        #    startFromFregment= boot_info['fragments'][0]['fragments'][-2]['first']
        
    #print 'segment_to_start',segment_to_start
    for currentIndex in range (segment_to_start,len(segment_run_table['segment_run'])):
        currentSegment=segment_run_table['segment_run'][currentIndex]
        #print 'currentSegment',currentSegment
        (seg,fregCount,frag_start,frag_end)=currentSegment
        #print 'startFromFregment',startFromFregment, 
        if (not startFromFregment==None) and startFromFregment>=frag_start and startFromFregment<=frag_end:
            frag_start=startFromFregment
        #print 'frag_start',frag_start,frag_end
        #custom ordering for byte and duration calculus
        fragmentsSorted = boot_info['fragments'][0]['fragments']
        fragmentsSorted.sort(key=lambda frag: frag['first'],reverse = True)
        indexFragSorted = 0
        startByte = total_size
        fragSize = 0
        startDuration = fragmentsSorted[0]['duration']
        totalSizeCheck = 0
        fragmentsSorted =  [frag for frag in fragmentsSorted if frag['duration'] != 0 and frag['first'] != 0]
        for currentFreg in range(frag_end,frag_start-1,-1):
            startDuration = fragmentsSorted[indexFragSorted]['duration']
            fragSize = (total_size * startDuration) / (total_duration * 1000)
            startByte = startByte - fragSize
            if(fragmentsSorted[indexFragSorted]['first'] == currentFreg):
                indexFragSorted += 1
            res.append((seg,currentFreg,startDuration,fragSize,(startByte, 0)[bool(startByte<0)]))
            totalSizeCheck += fragSize
        res.sort(key = lambda frag:(frag[0],frag[1]))
    return res

def join(base,url):
    join = urlparse.urljoin(base,url)
    url = urlparse.urlparse(join)
    path = posixpath.normpath(url[2])
    return urlparse.urlunparse(
        (url.scheme,url.netloc,path,url.params,url.query,url.fragment)
        )
        
def _add_ns(prop):
    #print 'F4Mversion',F4Mversion
    return '{http://ns.adobe.com/f4m/%s}%s' %(F4Mversion, prop)


#class ReallyQuietDownloader(youtube_dl.FileDownloader):
#    def to_screen(sef, *args, **kargs):
#        pass

class F4MDownloader():
    """
    A downloader for f4m manifests or AdobeHDS.
    """
    outputfile =''
    clientHeader=None
    cookieJar=cookielib.LWPCookieJar()

    def __init__(self):
        self.init_done=False
        
    def getUrl(self,url, ischunkDownloading=False):
        try:
            post=None
            print 'url',url
            url = urllib.quote(url, safe=":/&=?")
            print 'urlafter',url
            
            openner = urllib2.build_opener(urllib2.HTTPHandler, urllib2.HTTPSHandler)
            #cookie_handler = urllib2.HTTPCookieProcessor(self.cookieJar)
            #openner = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())

            if post:
                req = urllib2.Request(url, post)
            else:
                req = urllib2.Request(url)
            
            ua_header=False
            if self.clientHeader:
                for n,v in self.clientHeader:
                    req.add_header(n,v)
                    if n=='User-Agent':
                        ua_header=True

            if not ua_header:
                req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0')
            #response = urllib2.urlopen(req)
            if self.proxy and (  (not ischunkDownloading) or self.use_proxy_for_chunks ):
                req.set_proxy(self.proxy, 'http')
            response = openner.open(req)
            data=response.read()

            return data

        except:
            print 'Error in getUrl'
            traceback.print_exc()
            return None
            
        
    def _write_flv_header(self, stream, metadata):
        """Writes the FLV header and the metadata to stream"""
        # FLV header
        stream.write(b'FLV\x01')
        stream.write(b'\x05')
        stream.write(b'\x00\x00\x00\x09')
        # FLV File body
        stream.write(b'\x00\x00\x00\x00')
        # FLVTAG
        if metadata:
            stream.write(b'\x12') # Script data
            stream.write(pack('!L',len(metadata))[1:]) # Size of the metadata with 3 bytes
            stream.write(b'\x00\x00\x00\x00\x00\x00\x00')
            stream.write(metadata)
        # All this magic numbers have been extracted from the output file
        # produced by AdobeHDS.php (https://github.com/K-S-V/Scripts)
            stream.write(b'\x00\x00\x01\x73')
    
    def _write_flv_header2(self, stream):
        """Writes the FLV header and the metadata to stream"""
        # FLV header
        stream.write(b'FLV\x01')
        stream.write(b'\x01')
        stream.write(b'\x00\x00\x00\x09')
        # FLV File body
        stream.write(b'\x00\x00\x00\x09')

    def init(self, out_stream, url, proxy=None,use_proxy_for_chunks=True,g_stopEvent=None, maxbitrate=0, auth=''):
        try:
            self.statusStream=''
            self.init_done=False
            self.total_frags=0
            self.total_size=0
            self.total_duration=0
            self.fragments_list = []
            self.init_url=url
            self.clientHeader=None
            self.status='init'
            self.proxy = proxy
            self.auth=auth
            #self.auth="pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYzMDMxMTV+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWQxODA5MWVkYTQ4NDI3NjFjODhjOWQwY2QxNTk3YTI0MWQwOWYwNWI1N2ZmMDE0ZjcxN2QyMTVjZTJkNmJjMDQ%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3DACF8A1E4467676C9BCE2721CA5EFF840BD6ED1780046954039373A3B0D942ADC&hdntl=exp=1406303115~acl=%2f*~data=hdntl~hmac=4ab96fa533fd7c40204e487bfc7befaf31dd1f49c27eb1f610673fed9ff97a5f&als=0,2,0,0,0,NaN,0,0,0,37,f,52293145.57,52293155.9,t,s,GARWLHLMHNGA,2.11.3,37&hdcore=2.11.3" 
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
                self.clientHeader = sp[1]
                self.clientHeader= urlparse.parse_qsl(self.clientHeader)
                
                print 'header recieved now url and headers are',url, self.clientHeader 
            self.status='init done'
            self.url=url
            #self.downloadInternal(  url)
            return self.preDownoload()
            
            #os.remove(self.outputfile)
        except: 
            traceback.print_exc()
            self.status='finished'
        return False
     
    def preDownoload(self):
        global F4Mversion
        try:
            self.seqNumber=0
            self.live=False #todo find if its Live or not
            man_url = self.url
            url=self.url
            print 'Downloading f4m manifest'
            manifest = self.getUrl(man_url)#.read()
            if not manifest:
                return False
            print len(manifest)
            try:
                print manifest
            except: pass
            
            self.status='manifest done'
            #self.report_destination(filename)
            #dl = ReallyQuietDownloader(self.ydl, {'continuedl': True, 'quiet': True, 'noprogress':True})
            version_fine="xmlns=\".*?\/([0-9].*?)\""
            F4Mversion =re.findall(version_fine, manifest)[0]
            #print F4Mversion,_add_ns('media')
            auth_patt='<pv-2.0>(.*?)<'

            auth_obj =re.findall(auth_patt, manifest)
            self.auth20=''
            if auth_obj and len(auth_obj)>0:
                self.auth20=auth_obj[0] #not doing anything for time being
            print 'auth',self.auth,self.auth20
            #quick for one example where the xml was wrong.
            if '\"bootstrapInfoId' in manifest:
                manifest=manifest.replace('\"bootstrapInfoId','\" bootstrapInfoId')

            doc = etree.fromstring(manifest)
            
            # Added the-one 05082014
            # START
            # Check if manifest defines a baseURL tag
            baseURL_tag = doc.find(_add_ns('baseURL'))
            if baseURL_tag != None:
                man_url = baseURL_tag.text
                url = man_url
                self.url = url
                print 'base url defined as: %s' % man_url
            # END
            
            try:
                #formats = [(int(f.attrib.get('bitrate', -1)),f) for f in doc.findall(_add_ns('media'))]
                formats=[]
                duration  = 0
                for f in doc.findall(_add_ns('media')):
                    vtype=f.attrib.get('type', '')
                    if f.attrib.get('type', '')=='video' or vtype=='' :
                        formats.append([int(f.attrib.get('bitrate', -1)),f])
                print 'format works',formats
            except:
                formats=[(int(0),f) for f in doc.findall(_add_ns('media'))]
            #print 'formats',formats
            
            
            formats = sorted(formats, key=lambda f: f[0])
            if self.maxbitrate==0:
                rate, media = formats[-1]
            elif self.maxbitrate==-1:
                rate, media = formats[0]
            else: #find bitrate
                brselected=None
                rate, media=None,None
                for r, m in formats:
                    if r<=self.maxbitrate:
                        rate, media=r,m
                    else:
                        break
                
                if media==None:
                    rate, media = formats[-1]
                
            
            dest_stream =  self.out_stream
            print 'rate selected',rate
            self.metadata=None
            try:
                self.metadata = base64.b64decode(media.find(_add_ns('metadata')).text)
                print 'metadata stream read done'#,media.find(_add_ns('metadata')).text
                self.total_duration = FlvReader(self.metadata).read_metadata_duration()
                if(self.total_duration == 0):
                    total_duration_text = media.attrib['duration']
                    self.total_duration = int(float(total_duration_text) * 1000)
                    
                self.total_size = FlvReader(self.metadata).read_metadata_filesize()
                if(self.total_size == 0):
                    self.total_size = (rate * int(self.total_duration ) * 1000) / 8 
                print 'totalsize in bytes'
                print self.total_size
                print 'totalsize in megabytes'
                print self.total_size / 1024 / 1024
                print 'duration in seconds'
                print self.total_duration
                print 'duration in minutes'
                print self.total_duration / 60
            except:  traceback.print_exc()
        
            # Modified the-one 05082014
            # START
            # url and href can be used interchangeably
            # so if url attribute is not present
            # check for href attribute
            try:
                mediaUrl=media.attrib['url']
            except:
                mediaUrl=media.attrib['href']
            # END
            
            # Added the-one 05082014
            # START
            # if media url/href points to another f4m file
            if '.f4m' in mediaUrl:
                sub_f4m_url = join(man_url,mediaUrl)
                print 'media points to another f4m file: %s' % sub_f4m_url
                
                print 'Downloading f4m sub manifest'
                sub_manifest = self.getUrl(sub_f4m_url)#.read()
                if not sub_manifest:
                    return False
                print len(sub_manifest)
                try:
                    print sub_manifest
                except: pass
                self.status='sub manifest done'
                F4Mversion =re.findall(version_fine, sub_manifest)[0]
                doc = etree.fromstring(sub_manifest)
                print doc
                media = doc.find(_add_ns('media'))
                if media == None:
                    return False
                    
                try:
                    self.metadata = base64.b64decode(media.find(_add_ns('metadata')).text)
                    print 'metadata stream read done'
                    readerDuration = FlvReader(self.metadata)
                    self.total_duration = readerDuration.read_metadata_duration()
                    if(self.total_duration == 0):
                        total_duration_text = media.attrib['duration']
                        self.total_duration = int(float(total_duration_text) * 1000)
                    readerFile = FlvReader(self.metadata)
                    self.total_size = readerFile.read_metadata_filesize()
                    if(self.total_size == 0):
                         self.total_size = (rate * int(self.total_duration) * 1000) / 8
                except: pass
                
                try:
                    mediaUrl=media.attrib['url']
                except:
                    mediaUrl=media.attrib['href']
            # END
            
            
            try:
                bootStrapID = media.attrib['bootstrapInfoId']
            except: bootStrapID='xx'
            #print 'mediaUrl',mediaUrl
            base_url = join(man_url,mediaUrl)#compat_urlparse.urljoin(man_url,media.attrib['url'])
            if mediaUrl.endswith('/') and not base_url.endswith('/'):
                    base_url += '/'

            self.base_url=base_url
            bsArray=doc.findall(_add_ns('bootstrapInfo'))
            print 'bootStrapID',bootStrapID
            #bootStrapID='bootstrap_450'
            bootstrap=self.getBootStrapWithId(bsArray,bootStrapID)
            if bootstrap==None: #if not available then find any!
                print 'bootStrapID NOT Found'
                bootstrap=doc.findall(_add_ns('bootstrapInfo'))[0]
            else:
                print 'found bootstrap with id',bootstrap
            #print 'bootstrap',bootstrap
            

            bootstrapURL1=''
            try:
                bootstrapURL1=bootstrap.attrib['url']
            except: pass

            bootstrapURL=''
            bootstrapData=None
            queryString=None

            if bootstrapURL1=='':
                bootstrapData=base64.b64decode(doc.findall(_add_ns('bootstrapInfo'))[0].text)
                #
            else:
                from urlparse import urlparse
                queryString = urlparse(url).query
                print 'queryString11',queryString
                if len(queryString)==0: queryString=None
                
                if queryString==None or '?'  in bootstrap.attrib['url']:
                   
                    bootstrapURL = join(man_url,bootstrap.attrib['url'])# take out querystring for later
                    queryString = urlparse(bootstrapURL).query
                    print 'queryString override',queryString
                    if len(queryString)==0: 
                        queryString=None
                        if len(self.auth)>0:
                            bootstrapURL+='?'+self.auth
                            queryString=self.auth#self._pv_params('',self.auth20)#not in use
                else:
                    print 'queryString!!',queryString
                    bootstrapURL = join(man_url,bootstrap.attrib['url'])+'?'+queryString
                    if len(self.auth)>0:
                        authval=self.auth#self._pv_params('',self.auth20)#not in use
                        bootstrapURL = join(man_url,bootstrap.attrib['url'])+'?'+authval
                        queryString=authval

            print 'bootstrapURL',bootstrapURL
            if queryString==None:
                queryString=''
            self.bootstrapURL=bootstrapURL
            self.queryString=queryString
            print 'arrivato'
            self.bootstrap, self.boot_info, self.fragments_list,self.total_frags=self.readBootStrapInfo(bootstrapURL,bootstrapData)
            self.init_done=True
            return True
        except:
            traceback.print_exc()
        return False

        
    def keep_sending_video(self,dest_stream, fragmentToStart=None, totalSegmentToSend=0,startRange=0):
        try:
            self.status='download Starting'
            self.downloadInternal(self.url,dest_stream,fragmentToStart,totalSegmentToSend,startRange)
        except: 
            traceback.print_exc()
        self.status='finished'
            
    def downloadInternal(self,url,dest_stream ,fragmentToStart=None,totalSegmentToSend=0,startRange = 0):
        global F4Mversion
        try:
            #dest_stream =  self.out_stream
            queryString=self.queryString
            print 'fragmentToStart',fragmentToStart
            
            print 'writing metadata'#,len(self.metadata)
            if(fragmentToStart == 1 and self.statusStream == 'seeking'):
                self._write_flv_header(dest_stream, self.metadata)
                dest_stream.flush()
            elif(fragmentToStart != 1 and self.statusStream == 'seeking'):
                self._write_flv_header2(dest_stream)
                dest_stream.flush()
                
           
            
            url=self.url
  
            bootstrap, boot_info, fragments_list,total_frags=(self.bootstrap, self.boot_info, self.fragments_list,self.total_frags)
            print  boot_info, fragments_list,total_frags
            self.status='bootstrap done'


            self.status='file created'
            self.downloaded_bytes = 0
            self.bytes_in_disk = 0
            self.frag_counter = 0
            start = time.time()


            frags_filenames = []
            self.seqNumber=fragmentToStart -1
            frameSent=0
            self.statusStream = 'play'
            while (True and self.statusStream == 'play'):
                    
                if self.g_stopEvent and self.g_stopEvent.isSet():
                        return
                seg_i, frag_i,duration_i,size_i,start_byte_i=self.fragments_list[self.seqNumber]
                self.seqNumber+=1
                frameSent+=1
                name = u'Seg%d-Frag%d' % (seg_i, frag_i)
                #print 'base_url',base_url,name
                url = self.base_url + name
                if queryString and '?' not in url:
                    url+='?'+queryString
                elif '?' in self.base_url:
                    url = self.base_url.split('?')[0] + name+'?'+self.base_url.split('?')[1]
                #print(url),base_url,name
                #frag_filename = u'%s-%s' % (tmpfilename, name)
                #success = dl._do_download(frag_filename, {'url': url})
                print 'downloading....',url
                success=False
                urlTry=0
                while not success and urlTry<5:
                    success = self.getUrl(url,True)
                    if not success: xbmc.sleep(300)
                    urlTry+=1
                print 'downloaded',not success==None,url
                if not success:
                    return False
                #with open(frag_filename, 'rb') as down:
                
                if 1==1:
                    down_data = success#down.read()
                    reader = FlvReader(down_data)
                    while (True and self.statusStream == 'play'):
                        _, box_type, box_data = reader.read_box_info()
                        print  'box_type',box_type,len(box_data)
                        #if box_type == b'afra':
                        #    dest_stream.write(box_data)
                        #    dest_stream.flush()
                        #    break
                        conditionOffset = False
                        if((startRange == 0) or (startRange != 0 and (start_byte_i + len(box_data) >= startRange))):
                            conditionOffset = True
                        print 'conditionOffset',conditionOffset
                        print 'startRangepassed',startRange
                        if (box_type == b'mdat' ):
                            isDrm=True if ord(box_data[0])&1 else False
                            #print 'isDrm',isDrm,repr(box_data)
                            if 1==2 and isDrm:
                                print 'drm',repr(box_data[1:17])
                                box_data=box_data[17:]
                            dest_stream.write(box_data)
                            dest_stream.flush()
                            break
                            # Using the following code may fix some videos, but 
                            # only in mplayer, VLC won't play the sound.
                            # mdat_reader = FlvReader(box_data)
                            # media_type = mdat_reader.read_unsigned_char()
                            # while True:
                            #     if mdat_reader.read_unsigned_char() == media_type:
                            #         if mdat_reader.read_unsigned_char() == 0x00:
                            #             break
                            # dest_stream.write(pack('!B', media_type))
                            # dest_stream.write(b'\x00')
                            # dest_stream.write(mdat_reader.read())
                            # break
                if self.seqNumber==len(fragments_list):
                    if not self.live:
                        break
                    self.seqNumber=0
                    #todo if the url not available then get manifest and get the data again
                    total_frags=None
                    try:
                        bootstrap, boot_info, fragments_list,total_frags=self.readBootStrapInfo(self.bootstrapURL,None,updateMode=True,lastSegment=seg_i, lastFragement=frag_i)
                    except: 
                        traceback.print_exc()
                        pass
                    if total_frags==None:
                        break

            del self.downloaded_bytes
            del self.frag_counter
        except:
            traceback.print_exc()
            return
    def getBootStrapWithId (self,BSarray, id):
        try:
            for bs in BSarray:
                print 'compare val is ',bs.attrib['id'], 'id', id
                if bs.attrib['id']==id:
                    print 'gotcha'
                    return bs
        except: pass
        return None
    
    def readBootStrapInfo(self,bootstrapUrl,bootStrapData, updateMode=False, lastFragement=None,lastSegment=None):

        try:
            retries=0
            while retries<=5:

                if self.g_stopEvent and self.g_stopEvent.isSet():
                        return
                if not bootStrapData:
                    bootStrapData =self.getUrl(bootstrapUrl)
                if bootStrapData==None:
                    retries+=1
                    continue
                #print 'bootstrapData',len(bootStrapData)
                bootstrap = bootStrapData#base64.b64decode(bootStrapData)#doc.findall(_add_ns('bootstrapInfo'))[0].text)
                #print 'boot stream read done'
                boot_info,self.live = read_bootstrap_info(bootstrap)
                #print 'boot_info  read done',boot_info
                newFragement=None
                if not lastFragement==None:
                    newFragement=lastFragement+1
                fragments_list = build_fragments_list(boot_info,self.total_size,self.total_duration,newFragement,self.live)
                total_frags = len(fragments_list)
                #print 'fragments_list',fragments_list, newFragement
                #print lastSegment
                if updateMode and (len(fragments_list)==0 or (  newFragement and newFragement>fragments_list[0][1])):
                    #todo check lastFragement to see if we got valid data
                    print 'retrying......'
                    bootStrapData=None
                    retries+=1
                    xbmc.sleep(2000)
                    continue
                return bootstrap, boot_info, fragments_list,total_frags
        except:
            traceback.print_exc()
    

        

    
    def _pv_params(self, pvswf, pv):
        """Returns any parameters needed for Akamai HD player verification.

        Algorithm originally documented by KSV, source:
        http://stream-recorder.com/forum/showpost.php?p=43761&postcount=13
        """
        pv="ZXhwPTE0MDYyODMxOTF+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPTgwNTA0N2E1Yjk5ZmFjMjMzMDY0N2MxMzkyNGM0MDNiYzY1YjZmYzgyYTZhMjYyZDIxNDdkZTExZjI1MzQ5ZDI=;hdntl=exp=1406283191~acl=%2f*~data=hdntl~hmac=b65dc0c5ae60570f105984f0cc5ec6ce3a51422a7a1442e09f55513718ba80bf"
        (data, hdntl) = pv.split(";")
        SWF_VERIFICATION_KEY = b"Genuine Adobe Flash Player 001"
        #SWF_VERIFICATION_KEY=binascii.unhexlify("9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba009l2564") 
                               
        SWF_VERIFICATION_KEY = binascii.unhexlify(b"BD938D5EE6D9F42016F9C56577B6FDCF415FE4B184932B785AB32BCADC9BB592")
        swf = self.getUrl('http://www.wat.tv/images/v70/PlayerLite.swf',True)
        #AKAMAIHD_PV_KEY = unhexlify(b"BD938D5EE6D9F42016F9C56577B6FDCF415FE4B184932B785AB32BCADC9BB592")
        AKAMAIHD_PV_KEY = "9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba009l2564"

        hash = hashlib.sha256()
        hash.update(self.swfdecompress(swf))
        hash = base64.b64encode(hash.digest()).decode("ascii")
        print 'hash',hash
        hash="96e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ="
        print 'hash',hash
        #data="ZXhwPTE0MDYyMDQ3NjB+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWEzMjBlZDI5YjI1MDkwN2ExODcyMTJlOWJjNGFlNGUzZjA3MTM3ODk1ZDk4NmI2ZDVkMzczNzNhYzNiNDgxOWU="
        msg = "exp=9999999999~acl=%2f%2a~data={0}!{1}".format(data, hash)
        auth = hmac.new(AKAMAIHD_PV_KEY, msg.encode("ascii"), sha256)
        pvtoken = "{0}~hmac={1}".format(msg, auth.hexdigest())

        # The "hdntl" parameter can be accepted as a cookie or passed in the
        # query string, but the "pvtoken" parameter can only be in the query
        # string
        print 'pvtoken',pvtoken


        #return "pvtoken={}&{}".format(
        #urlencode_param(pvtoken), urlencode_param(hdntl))
        
        params=urllib.urlencode({'pvtoken':pvtoken})+'&'+hdntl+'&hdcore=2.11.3'
        #params='pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYwNDMzOTN+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWQxMTk0ZDc4NDExMDYwNjZlNDI5OWU2NTc3ODA0Mzk0ODU5NGZiMDQ5Njk2OGNiYzJiOGU2OTI2MjIzMjczZTA%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3D1BE9DEB8262AB4886A0CB9E8376D04652F015751B88DD3D2201DE463D9E47733&hdntl=exp=1406043393~acl=%2f*~data=hdntl~hmac=28d5e28f47b7b3821fafae0250ba37091f2fc66d1a9d39b76b925c423458c537'+'&hdcore=2.11.3'

        #php AdobeHDS.php --manifest "http://nt1livhdsweb-lh.akamaihd.net/z/live_1@90590/manifest.f4m?hdnea=st=1405958620~exp=1405960420~acl=/*~hmac=5ca0d2521a99c897fb9ffaf6ed9c2e40e5d0300cdcdd9dfb7302d9e32a84f98d&hdcore=2.11.3&g=VQYTYCFRUDRA"
        #params="pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYwNDUwNDZ+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWYwYWQ5ZGQyNDJlYjdiYjQ2YmZhMzk3MjY3MzE0ZWZiOWVlYTY5MDMzYWE2ODM5ZDM1ZWVjMWM1ZDUzZTk3ZjA%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3D9FCCB6BC90C17E8057EE52CD53DDF0C6D07B20638D68B8FFCE98ED74153AA960&hdntl=exp=1406045046~acl=%2f*~data=hdntl~hmac=11e323633ad708a11e57a91e8c685011292f42936f5f7f3b1cb0fb8d2266586a&als=0,2,0,0,0,NaN,0,0,0,52,f,52035079.57,52035089.9,t,s,VQYTYCFRUDRA,2.11.3,52&hdcore=2.11.3"
        #--useragent "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"
        #+'&als=0,2,0,0,0,NaN,0,0,0,47,f,52018363.57,52018373.9,t,s,HPFXDUMCMNPG,2.11.3,47&hdcore=2.11.3'
        params=params.replace('%2B','+')
        params=params.replace('%2F','/')

        
        #params='pvtoken=' +pvtoken+'&'+hdntl
        #params = [("pvtoken", pvtoken)]
        #params.extend(parse_qsl(hdntl, keep_blank_values=True))
        #params='pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYwMzc2Njl+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWZjYzY5OTVkYjE5ODIxYTJlNDM4YTdhMWNmZjMyN2RhNTViOWNhMWM4NjZhZjYxM2ZkNDI4MTMwNjU4MjFjMjM%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3DFA3BCC1CF6466CAFFCC6EF5CB2855ED065F36687CBFCD11570B7D702F71F10A6&hdntl=exp=1406037669~acl=%2f*~data=hdntl~hmac=4ab5ad38849b952ae93721af7451936b4c5906258d575eda11e52a05f78c7d75&als=0,2,0,0,0,NaN,0,0,0,96,f,52027699.57,52027709.89,t,s,RUIDLGQGDHVH,2.11.3,90&hdcore=2.11.3'
        #print '_pv_params params',params
        print params
        print "pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYyODMxOTF+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPTgwNTA0N2E1Yjk5ZmFjMjMzMDY0N2MxMzkyNGM0MDNiYzY1YjZmYzgyYTZhMjYyZDIxNDdkZTExZjI1MzQ5ZDI%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3D47A2B2AA9570ECFB37966C884174D608D86A7DE2466DE7EB48A6F118A155BD80&hdntl=exp=1406283191~acl=%2f*~data=hdntl~hmac=b65dc0c5ae60570f105984f0cc5ec6ce3a51422a7a1442e09f55513718ba80bf"

        return "pvtoken=exp%3D9999999999%7Eacl%3D%252f%252a%7Edata%3DZXhwPTE0MDYzMDMxMTV+YWNsPSUyZip+ZGF0YT1wdmMsc35obWFjPWQxODA5MWVkYTQ4NDI3NjFjODhjOWQwY2QxNTk3YTI0MWQwOWYwNWI1N2ZmMDE0ZjcxN2QyMTVjZTJkNmJjMDQ%3D%2196e4sdLWrezE46RaCBzzP43/LEM5en2KujAosbeDimQ%3D%7Ehmac%3DACF8A1E4467676C9BCE2721CA5EFF840BD6ED1780046954039373A3B0D942ADC&hdntl=exp=1406303115~acl=%2f*~data=hdntl~hmac=4ab96fa533fd7c40204e487bfc7befaf31dd1f49c27eb1f610673fed9ff97a5f&als=0,2,0,0,0,NaN,0,0,0,37,f,52293145.57,52293155.9,t,s,GARWLHLMHNGA,2.11.3,37&hdcore=2.11.3" 
 
        return params
        
    def swfdecompress(self,data):
        if data[:3] == b"CWS":
            data = b"F" + data[1:8] + zlib.decompress(data[8:])

        return data

        
        