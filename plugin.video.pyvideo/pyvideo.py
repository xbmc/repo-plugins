# -*- coding: utf-8 -*-
# Copyright 2012 Jörn Schumacher 
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
#

import xbmcplugin, xbmcgui, xbmcaddon

import urlparse, urllib2
import json
import sys

from BeautifulSoup import BeautifulSoup

# ------------------------------------------------------------

ALL_VIDEOS_URL = "http://pyvideo.org/api/v1/video/?limit=0"
CONFERENCES_URL = "http://pyvideo.org/api/v1/category/?limit=0"
CONFERENCE_URL = "http://pyvideo.org/api/v1/category/{id}/?limit=0"
SPEAKERS_URL = "http://pyvideo.org/api/v1/speaker/?limit=0"
SPEAKER_URL = "http://pyvideo.org/api/v1/speaker/{id}/?limit=0"
TAGS_URL = "http://pyvideo.org/api/v1/tag/?limit=0"
TAG_URL = "http://pyvideo.org/api/v1/tag/{id}/?limit=0"
VIDEO_URL = "http://pyvideo.org/api/v1/video/{id}/"

YOUTUBE_URL = 'plugin://plugin.video.youtube?path=/root/video&action=play_video&videoid={ID}'

FORMATS = ['ogv', 'webm', 'mp4', 'flv']


language = xbmcaddon.Addon(id='plugin.video.pyvideo').getLocalizedString

strings = { 'allvideos': language(30001),
            'conferences': language(30002),
            'speakers': language(30003),
            'tags': language(30004)
            }

# ------------------------------------------------------------

def addLink(name, url, iconimage, max_elems, info):
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    li.setProperty("IsPlayable", "true")
    li.setInfo( type="Video", infoLabels=info )
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li, isFolder=False, totalItems=max_elems)
    
def addDir(name,path,page,iconimage):
    u=sys.argv[0]+"?path=%s&page=%s"%(path,str(page))
    li=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    li.setInfo( type="Video", infoLabels={ "Title": name })
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=li,isFolder=True)

# ------------------------------------------------------------

def html_to_text(html):
    return ''.join(BeautifulSoup(html).findAll(text=True))

def resolve_content_url(video):
    for format in FORMATS:
        attribute = 'video_'+format+'_url'
        if video[attribute]:
            return video[attribute]
    src_url = video['source_url']
    if 'youtube' in src_url:
        try:
            v = urlparse.parse_qs(urlparse.urlparse(src_url).query)['v'][0]
            return YOUTUBE_URL.format(id=v)
        except:
            pass
    return src_url


def add_video(video, max_elems):
    info = {
        'Title': video['title'],
        'Plot': html_to_text(video['summary']),
        'PlotOutline': html_to_text(video['description']).replace('\n', ' '),
        'Date': str(video['recorded'])
        }
    url = resolve_content_url(video)
    thumb = video['thumbnail_url']
    if url:
        addLink(info['Title'], url, thumb, max_elems, info)

def add_videos_by_id(video_ids):
    max_elems = len(video_ids)
    for id in video_ids:
        url = VIDEO_URL.format(id=id)
        video_string = urllib2.urlopen(url).read()
        video = json.loads(video_string)
        add_video(video, max_elems)


# ------------------------------------------------------------

params = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)

try:
    path = params['path'][0]
except:
    path = '/'

if path == '/':
    addDir(strings['allvideos'], "/all_videos/", 1, "")
    addDir(strings['conferences'], "/conferences/", 1, "")
    addDir(strings['speakers'], "/speakers/", 1, "")
    addDir(strings['tags'], "/tags/", 1, "")

elif path == '/all_videos/':
    all_videos_string = urllib2.urlopen(ALL_VIDEOS_URL).read()
    all_videos = json.loads(all_videos_string)

    max_elems = all_videos['meta']['total_count']
    
    for video in all_videos['objects']:
        add_video(video, max_elems)
        
        
elif path == '/conferences/':
    conferences_string = urllib2.urlopen(CONFERENCES_URL).read()
    conferences = json.loads(conferences_string)
    for conference in conferences['objects']:
        addDir(conference['title'], '/conference/%s/'%conference['id'], 1, "")
        
elif path.startswith('/conference/'):
    id = path.split('/')[2]
    conference_string = urllib2.urlopen(CONFERENCE_URL.format(id=id)).read()
    conference = json.loads(conference_string)
    video_ids = [v.split('/')[-2] for v in conference['videos']]
    add_videos_by_id(video_ids)

elif path == '/speakers/':
    speakers_string = urllib2.urlopen(SPEAKERS_URL).read()
    speakers = json.loads(speakers_string)
    for speaker in speakers['objects']:
        addDir(speaker['name'], '/speaker/%s/'%speaker['id'], 1, "")

elif path.startswith('/speaker/'):
    id = path.split('/')[2]
    speaker_string = urllib2.urlopen(SPEAKER_URL.format(id=id)).read()
    speaker = json.loads(speaker_string)
    video_ids = [v.split('/')[-2] for v in speaker['videos']]
    add_videos_by_id(video_ids)
    
elif path == '/tags/':
    tags_string = urllib2.urlopen(TAGS_URL).read()
    tags = json.loads(tags_string)
    for tag in tags['objects']:
        addDir(tag['tag'], '/tag/%s/'%tag['id'], 1, "")

elif path.startswith('/tag/'):
    id = path.split('/')[2]
    tags_string = urllib2.urlopen(TAG_URL.format(id=id)).read()
    tag = json.loads(tags_string)
    video_ids = [v.split('/')[-2] for v in tag['videos']]
    add_videos_by_id(video_ids)
    
    
else:
    print "ERROR: Path", path, "not valid"

xbmcplugin.endOfDirectory(int(sys.argv[1]))
