# returns a video list from http://joerogan.net
import urllib,urllib2,re,os
#import xbmcplugin,xbmcgui
from BeautifulSoup import BeautifulSoup

def pull_video_list(page_no):
	"""
	Gets the list of thumbnails, video URLs and titles from the video site and display the list

	@param string url - Main URL of uStream page (without page number)
	@param int page_no - Page number to get

	@returns dictionary
	"""		

	# Get the page number and add it to the URL (to allow moving through the video pages)
	url = "http://blog.joerogan.net" + "/page/" + str(page_no)

	# Build the page request including setting the User Agent
	req  = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

	# Open URL and read contents to variable
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	
	matches = {}
	matches['title'] = []
	matches['guests'] = []
	matches['video_url'] = []
	matches['thumbnail'] = []

	# Create a new soup instance and assign a video list html to a variable
	soup = BeautifulSoup(''.join(link))

	# Get all the divs with the podcast content
	result = soup.find('tr', id='bodyrow').find('td', id='middle').findAll('div', id=re.compile('post-\d+'))

	# For each div
	for r in result:
		# Get the title
		title = r.find('div', 'post-headline').h2.a.string

		try:
			# Get the main divs
			div = r.find('div', 'post-bodycopy clearfix')
			# Get the video URL
			video_url = div.center.a['href']
			print 'The video URL is', video_url
			if re.search(r"(ustream)|(vimeo)", video_url) is None:
				if pull_podcast_mp3(div) != False:
					video_url = pull_podcast_mp3(div)
				else:
					continue

			# Get the thumbnail
			thumbnail = div.center.img['src']
			guests = ""
			# Check if the Guests exist (some videos don't have any guests)
			try:
				guests_twit = div.findAll('a', href=re.compile('(http://www.twitter.com/.*)|(http://twitter.com/#!/.*)'))

				for count in range(len(guests_twit)):
					guest = re.sub(r',|\ $', '', guests_twit[count].string) 

					if count == 0:
						guests = ' (' + guest
					elif count == len(guests_twit)-1:
						guests = guests + ' & ' + guest + ")"
					else:
						guests = guests + ', ' +  guest

					if len(guests_twit)-1 == 0:
						guests = guests + ')' 

			except:
				pass

			# Append the title to the title list
			matches['title'].append(title + guests)
			matches['video_url'].append(video_url)
			matches['thumbnail'].append(thumbnail)
		except:
			pass
		# If it's not a podcast link, it'll be a special video like a blog or user submitted Youtube clip
		try:
			video_url = r.find('div', 'post-bodycopy clearfix').center.iframe['src']
			if re.search(r"(ustream)|(vimeo)", video_url) is None:
				if pull_podcast_mp3(div) != False:
					video_url = pull_podcast_mp3(div)
				else:
					continue

			#thumbnail = r.find('div', 'post-bodycopy clearfix').center.a.img['src']
			matches['title'].append(title)
			matches['video_url'].append(video_url)
			matches['thumbnail'].append(thumbnail)
		except:
			pass

	return matches

def pull_podcast_mp3(div):
	"""
	Gets the audio link to the podcast if avaiable
	"""
	try:
		url = div.find('div', 'podPress_content').find('div', 'podPress_downloadlinks').a['href']
		return url
	except:
		return False
