# Copyright 2011 Jonathan Beluch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import urllib
import re
from xbmccommon import parse_url_qs, unhex

def get_flv_url(docid=None, url=None):
    '''Takes a docid id from a google video page url, or takes a complete url 
    to a googlevideo swf and returns the url to the actual video resource.
    Returns None if no match is found.
    
    >>> get_flv_url(url='http://video.google.com/googleplayer.swf?docid=-7205983324127064982&hl=en&fs=true')
    'http://v19.lscache1.googlevideo.com/videoplayback?id=9aced06ebda81e9a&itag=5&begin=0&ip=0.0.0.0&ipbits=0&expire=1294349447&sparams=ip,ipbits,expire,id,itag&signature=0F0871585D48C2ED310571CBA37E1D31F9283020.39A632C3EFFA49544EB2F09391AACDD613B5DB7A&key=ck1'
    
    >>> get_flv_url(docid='-7205983324127064982')
    'http://v19.lscache1.googlevideo.com/videoplayback?id=9aced06ebda81e9a&itag=5&begin=0&ip=0.0.0.0&ipbits=0&expire=1294349447&sparams=ip,ipbits,expire,id,itag&signature=73F88621DCD5386AC8E215ED6FB3C9A50D113572.4EB3FB28324BA65AD7AEA70A174D067765D05297&key=ck1'
    ''' 
    if url:
        docid = parse_url_qs(url).get('docid')
    url = 'http://video.google.com/videoplay?docid=%s&hl=en' % docid

    #load the googlevideo page for a given docid or googlevideo swf url
    src = urllib.urlopen(url).read()
    flvurl_pattern = re.compile(r"preview_url:'(.+?)'")
    m = flvurl_pattern.search(src)
    if not m:
        return
    previewurl = m.group(1)

    #replace hex things
    # videoUrl\x3dhttp -> videoUrl=http
    previewurl = unhex(previewurl)
    #parse querystring and return the videoUrl
    params = parse_url_qs(previewurl)
    return urllib.unquote_plus(params['videoUrl'])
