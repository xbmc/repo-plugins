# returns a video list or video from UStream
import urllib,urllib2,re,os
import xbmcplugin,xbmcgui
from BeautifulSoup import BeautifulSoup

def pull_video_list(url, page_no):
	"""
	Gets the list of thumbnails, video URLs and titles from the video site and display the list

	@param string url - Main URL of uStream page (without page number)
	@param int page_no - Page number to get

	@returns dictionary
	"""		

	# Get the page number and add it to the URL (to allow moving through the video pages)
	url = url + "/" + str (page_no)

	# Build the page request including setting the User Agent
	req  = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

	# Open URL and read contents to variable
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()

	# Create a new soup instance and assign a video list html to a variable
	soup = BeautifulSoup(''.join(link))
	result = soup.find("div", "scrollPagerWrp clearAfter")

	# Create another instance of soup with the subset of data
	soup = BeautifulSoup(str(result))

	# Build a dictionary to house matches found on the page and set keys
	match = {}
	match['name'] = []
	match['vid_url'] = []
	match['thumbnail'] = []

	# Go through each title and get the text
	for title in soup.findAll("h4"):
		match['name'].append(title.text)

	# Go through each link with a shadowbox class (the image) and get the href
	for link in soup.findAll("a", "shadowbox"):
		# With the URL, get the .mp4 file
		match['vid_url'].append(link['href'])
		
	# Go through each img tag and get the source (thumbnail)
	for img in soup.findAll("img"):
		match['thumbnail'].append(img['src'])

	# Return the match dictionary
	return match



def pull_video_url(url):
	"""
	Get an individual MP4 file from a video page URL

	@params string url - URL of page

	@returns output_url - URL to be sent to play URL
	"""

	# Gets the URL sent and adds uStream TV (in future this will check if it doesn't already have it
	url = str (url)

	# Build the page reuqest including setting the User Agent
	req  = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

	# Open URL and read contents
	response = urllib2.urlopen(req)

	# Create a new soup instance
	soup = BeautifulSoup(''.join(response))

	# get text in the JSON data for video playback, then split it to a list with a ; delimiter
	result = soup.find(id="UstreamExposedVariables").text.split(";")

	# Remove the extra backslash
	output_url = re.sub(r'\\', '', result[8].split("=")[1])

	# Remove the quotes
	output_url = re.sub(r'"', '', output_url)

	# Return the output URL
	return output_url

	# Play the video (obviously...)
	#play_vid(output_url)


def get_swf():
        url = 'http://www.ustream.tv/flash/viewer.swf'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        swf_url = response.geturl()
        return swf_url 


def pull_live_stream(url):
	headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
	data = None
	req = urllib2.Request(url,data,headers)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	match = re.compile('.*(rtmp://.+?)\x00.*').findall(link)
	try:
		rtmp = match[0]
	except:
		return False

	s_name = re.compile('.*streamName\W\W\W(.+?)[/]*\x00.*').findall(link)
	playpath = ' playpath='+s_name[0]
	swf = ' swfUrl='+get_swf()
	page_rrl = ' pageUrl=http://ustream.tv/joerogan'
	url = rtmp + playpath + swf + page_url + ' swfVfy=1 live=true'
	return url
        
        


