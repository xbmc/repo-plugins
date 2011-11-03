import urllib,urllib2,re,os
#import xbmcplugin,xbmcgui
from BeautifulSoup import BeautifulStoneSoup
import string
import re

def pull_video_url(url):
	"""
	Get an individual MP4 file from a video page URL

	@params URL of page

	@returns output_url - URL to be sent to play URL
	"""

	# Extra clip ID from the URL, method varying depending on whether it's player.vimeo.com or vimeo.com/id
	if re.search(r'player.vimeo.com/video', url):
		url_section = string.split(url, '/')
		clip_id = url_section[4]
		clip_id = string.split(clip_id, '?')[0]
	else:
		url_section =  string.split(url, '/')
		clip_id = url_section[3]
	
	url = 'http://www.vimeo.com/moogaloop/load/clip:' + clip_id

	print url

	# Build the page reuqest including setting the User Agent
	req  = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

	# Open URL and read contents
	response = urllib2.urlopen(req)

	# Create a new Stone Soup instance
	xml = BeautifulStoneSoup(response)

	req_sig = xml.find('request_signature').string
	req_sig_expires = xml.find('request_signature_expires').string

	output_url = 'http://vimeo.com/moogaloop/play/clip:' + clip_id + '/' + req_sig + '/' + req_sig_expires

	req = urllib2.Request(output_url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

	conn = urllib2.urlopen(req)

	output_url = conn.geturl()


	return output_url
