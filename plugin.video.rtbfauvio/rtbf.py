#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import channel
import HTMLParser
from bs4 import BeautifulSoup
import m3u8

 

id2skip = [str(x) for x in [5683,2913,5614,5688,156]]


class Channel(channel.Channel):
    def get_main_url(self):
        return 'https://www.rtbf.be/auvio'
   
    def get_categories(self, datas):
   	for category_id, cat in channel.categories.iteritems():
   		channel.addDir(name=cat['name'], iconimage='DefaultVideo.png', channel_id=category_id, action='show_category')
   		
    def get_category(self, datas):
    	    data = channel.get_url(self.main_url+'/categorie/'+datas.get('name')+'?id='+datas.get('channel_id'))
    	    soup = BeautifulSoup(data, 'html.parser')
    	    main = soup.main
    	    section = main.section
    	    articles = section.find_all('article')
    	    for article in articles:
    	    	icons = article.find('img',{'data-srcset':True})['data-srcset']
    	    	regex = r""",([^,]+?\.(?:jpg|gif|png|jpeg))\s640w"""
    	    	icon = str(re.findall(regex, icons)[0])
    	    	container = article.h3
    	    	url = container.find('a',{'href':True})['href']
    	    	id = url.split('?id=')[1]
    	    	name = container.find('a', {'title':True})['title'] 	
    	        channel.addDir(name, icon, channel_id=datas.get('channel_id'), url=url, action='show_videos', id=id)
    
    def get_channel(self, datas):
    	    data = channel.get_url(self.main_url + '/emissions')
    	    try:
    	    	    ch = channel.channelsTV[datas.get('channel_id')]['name']
    	    except:
    	    	    ch = channel.channelsRadio[datas.get('channel_id')]['name']
    	    regex = r""",([^\,]+-original.(?:jpg|gif|png|jpeg))[^/]*/>\s*\n\s*</div>\s*\n\s*</figure>\s*\n\s*<header[^>]+>\s*\n\s*<span class="rtbf-media-item__channel">([^<]+)*</span>\s*\n\s*<a href="([^"]+)"\s*>\s*\n\s*<h4[^>]+>([^<]+)"""
    	    for icon, chan, url, name in re.findall(regex, data):
    	    	    if ch in chan:
    	    	       id = url.split('?id=')[1]
                       channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    	    
    	    
    def get_programs(self, skip_empty_id = True):
        data = channel.get_url(self.main_url + '/emissions')
        regex = r""",([^\,]+-original.(?:jpg|gif|png|jpeg))[^/]*/>\s*\n\s*</div>\s*\n\s*</figure>\s*\n\s*<header[^>]+>\s*\n\s*<span[^<]+</span>\s*\n\s*<a href="([^"]+)"\s*>\s*\n\s*<h4[^>]+>([^<]+)"""
        for icon, url, name in re.findall(regex, data):
            id = url.split('?id=')[1]
            if skip_empty_id and id in id2skip:
                continue
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    def get_lives(self, datas):
        def parse_lives(data):
            #regex = r""",([^,]+?\.(?:jpg|gif|png|jpeg))\s648w"[^/]*/>(?s).*?"Maintenant</span> "([^s]+)</"rtbf-media-item__title">\s*<a href="([^"]+)"\s*title="([^"]+)"""
            #for icon, chan, url, name in re.findall(regex, data, flags=re.DOTALL):
            regex = r""",([^,]+?\.(?:jpg|gif|png|jpeg))\s648w"[^/]*/>(?s).*?"rtbf-media-item__title">\s*<a href="([^"]+)"\s*title="([^"]+)"""
            for icon, url, name in re.findall(regex, data, flags=re.DOTALL):
                xbmc.log("found",xbmc.LOGDEBUG)
                vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_live')
                channel.addLink(name.replace('&#039;', "'").replace('&#034;', '"') , vurl, icon) # + ' - ' + date
        live_url = self.main_url + '/direct/#category=0'
        data = channel.get_url(live_url)
        parse_lives(data)

    def get_videos_cat(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        soup = BeautifulSoup(data)
    	sections = soup.find_all('section',{'class':True,'id':True})
    	section = sections[0]
    	regex = r""",([^\,]+-original.(?:jpg|gif|png|jpeg))[^/]*/>\s*\n\s*</div>\s*\n\s*</figure>\s*\n\s*<header[^>]+>\s*\n\s*<span[^<]+</span>\s*\n\s*<a href="([^"]+)"\s*>\s*\n\s*<h4[^>]+>([^<]+)"""
        for icon, url, name in re.findall(regex, data):
            id = url.split('?id=')[1]
            if skip_empty_id and id in id2skip:
                continue
            channel.addDir(name, icon, channel_id=self.channel_id, url=url, action='show_videos', id=id)

    
    def get_videos(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        soup = BeautifulSoup(data)
    	sections = soup.find_all('section',{'class':True,'id':True})
    	for section in sections:
    	  if section['id']!='widget-ml-avoiraussi-':
    	     regex = r""">([^<]+)</time>\s*\n\s*<h3[^<]*<a href="([^"]+)"[^>]*>([^<]+)</a></h3>"""
	     for date, url, title in re.findall(regex, str(section)):
                title = title + ' - ' + date
                vurl = channel.array2url(channel_id=self.channel_id, url=url, action='play_video')
                channel.addLink(title.replace('&#039;', "'").replace('&#034;', '"'), vurl, None)

    def play_video(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r"""src="(https://www.rtbf.be/auvio/embed/media[^"]+)"""
        iframe_url = re.findall(regex, data)[0]
        iframe_url
        data = channel.get_url(iframe_url)
       	regex = r"""data-media="([^"]+)"""
       	media = re.findall(regex, data)[0]        
       	h = HTMLParser.HTMLParser()
       	media_json = h.unescape(media)
       	regex = r""""high":"([^"]+)"""
       	all_url = re.findall(regex, media_json)
       	if len(all_url) > 0:
       		video_url = all_url[0]
        else:
        	regex = r"""url&quot;:&quot;([^&]+)"""
        	iframe_url = re.findall(regex, data)[0]
        	video_url = iframe_url.replace("\\", "") 	
        channel.playUrl(video_url)


    def play_live(self, datas):
        url = datas.get('url')
        data = channel.get_url(url)
        regex = r"""src="(https://www.rtbf.be/auvio/embed/direct[^"]+)"""
        iframe_url = re.findall(regex, data)[0]
        rtmp = self.get_live_rtmp(iframe_url)
        if rtmp is not None:
           channel.playUrl(rtmp)



    def get_live_rtmp(self, page_url):
        xbmc.log("live stream!",xbmc.LOGDEBUG)
	data = channel.get_url(page_url)
	regex = r"""streamName&quot;:&quot;([^&]+)"""
	stream_name = re.search(regex, data)
	if stream_name is None:
		return None
	stream_name = stream_name.group(1)
	xbmc.log("stream name: >" + stream_name + "<",xbmc.LOGDEBUG)
	if stream_name == 'freecaster':
		xbmc.log("freecaster stream",xbmc.LOGDEBUG)
		regex = r"""streamUrl&quot;:&quot;([^&]+)"""
		freecaster_stream =  re.search(regex, data)
		freecaster_stream = freecaster_stream.group(1)
		freecaster_stream=freecaster_stream.replace("\\", "") 
		channel.playUrl(freecaster_stream)
	else:
		xbmc.log("not a freecaster stream",xbmc.LOGDEBUG)
		regex = r"""streamUrlHls&quot;:&quot;([^&]+)"""
		hls_stream_url = re.search(regex,data)
		if hls_stream_url is not None:
			xbmc.log("HLS stream",xbmc.LOGDEBUG)
			hls_stream_url = hls_stream_url.group(1)
			hls_stream_url = hls_stream_url.replace("\\", "")
			xbmc.log("HLS stream url: >" + hls_stream_url + "<",xbmc.LOGDEBUG)
			stream_data = channel.get_url(hls_stream_url)
			variant_m3u8 = m3u8.loads(stream_data)
			stream_url = variant_m3u8.playlists[len(variant_m3u8.playlists)-1].uri
			home_url = hls_stream_url.split('/open',1)
			xbmc.log(home_url[0],xbmc.LOGDEBUG)
			stream_url = stream_url.replace("../..",home_url[0])
			channel.playUrl(stream_url)
		else:
			regex = r"""streamUrl&quot;:&quot;([^&]+)"""
			stream_url = re.search(regex,data)
			if stream_url is not None:
				stream_url = stream_url.group(1)
				stream_url = stream_url.replace("\\", "")
				xbmc.log("strange stream",xbmc.LOGDEBUG) 
				xbmc.log("stream url: >" + stream_url + "<",xbmc.LOGDEBUG)
				channel.playUrl(stream_url)
			else:
				xbmc.log("normal stream",xbmc.LOGDEBUG)
				page_url = 'http://www.rtbf.be'
				token_json_data = channel.get_url(page_url + '/api/media/streaming?streamname=' + stream_name, referer=page_url)
				token = token_json_data.split('":"')[1].split('"')[0]
				swf_url = 'http://static.infomaniak.ch/livetv/playerMain-v4.2.41.swf?sVersion=4%2E2%2E41&sDescription=&bLd=0&sTitle=&autostart=1'
				rtmp = 'rtmp://rtmp.rtbf.be/livecast'
				play = '%s?%s' % (stream_name, token)
				rtmp += '/%s swfUrl=%s pageUrl=%s tcUrl=%s' % (play, swf_url, page_url, rtmp)
				return rtmp

if __name__ == "__main__":
    import sys
    args = sys.argv
    if len(args) == 2:
        action = args[1]
        if action == 'scan_empty':
            Channel({'channel_id': 'rtbf', 'action': 'scan_empty'})
        elif action == 'get_lives':
            Channel({'channel_id': 'rtbf', 'action': 'get_lives'})
        else:
            Channel({'channel_id': 'rtbf', 'action': 'show_videos', 'url':args[1]})
    else:
        Channel({'channel_id': 'rtbf', 'action': 'show_menu'})
