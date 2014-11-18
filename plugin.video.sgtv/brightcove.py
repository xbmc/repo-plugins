#brightcove
import urllib, urllib2, cookielib, httplib, pyamf, brightcove
from pyamf import remoting
CONST = '84c401e577ddd24ca827eab0184302b8281e8b51'

def getBrightCoveUrl(video_content_id):
	video_player_key = "AQ~~%2CAAABhuSnh_E~%2CMYK8rOjehP4S5O2-9HT51QOan9pItjG3"
	page_url = "http://xin.msn.com/en-sg/video/catchup/hawaii-five-o-4-episode-6/Fvi-BBamdrC"
	video_player_id = "3605549263001"
	publisher_id = "1678873430001"

	swf_url = get_swf_url("myExperience",video_player_id,publisher_id,str(video_content_id))
	print "swf_url = "+str(swf_url)
	renditions = get_episode_info(video_player_key,str(video_content_id),page_url,video_player_id)
	print "renditions = "+str(renditions)
	finalurl = renditions['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
	print "finalurl = "+str(finalurl)

# use 'IOSRenditions' in place of 'renditions' in below for .m3u8 list, note case of 'r' in renditions, using 'renditions' gives you rtmp links

#	if (addon.getSetting('vid_res') == "1"):
	stored_size=stored_height = 0
	for item in sorted(renditions['programmedContent']['videoPlayer']['mediaDTO']['renditions'], key = lambda item:item['frameHeight'], reverse = False):
		stream_size = item['size']
		stream_height = item['frameHeight']
		if (int(stream_size) > stored_size) and (int(item['encodingRate']) < 4000000):
			finalurl = item['defaultURL']
			stored_size = stream_size
			stored_height = stream_height

	(server,ppath)= finalurl.split('&',1)
	finalurl = "%s playpath=%s swfUrl=%s  swfvfy=1 timeout=45 pageurl=http://xin.msn.com/en-sg/video/catchup/" % (server, ppath, swf_url)
	return finalurl


def get_episode_info(video_player_key, video_content_id, video_url, video_player_id):

	envelope = build_amf_request(video_player_key, video_content_id, video_url, video_player_id)
	connection_url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=" + video_player_key
	values = bytes(remoting.encode(envelope).read())
	header = {'Content-Type' : 'application/x-amf'}
	response = remoting.decode(getURL(connection_url, values, header, amf = True)).bodies[0][1].body
	return response

def getURL(url, values = None, header = {}, amf = False, cookieinfo = False):
	try:
		if values is None:
			req = urllib2.Request(bytes(url))
		else:
			if amf == False:
				data = urllib.urlencode(values)
			elif amf == True:
				data = values
			req = urllib2.Request(bytes(url), data)
		header.update({'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0'})
		for key, value in header.iteritems():
			req.add_header(key, value)
		response = urllib2.urlopen(req)
		link = response.read()
		cookie = response.info()
		response.close()
	except urllib2.HTTPError, error:
		return error.read()
	else:
		if cookieinfo is True:
			return link, cookie
		else:
			return link

class ViewerExperienceRequest(object):
	def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken = ''):
		self.TTLToken = TTLToken
		self.URL = URL
		self.deliveryType = float(0)
		self.contentOverrides = contentOverrides
		self.experienceId = experienceId
		self.playerKey = playerKey

class ContentOverride(object):
	def __init__(self, contentId, contentType = 0, target = 'videoPlayer'):
		self.contentType = contentType
		self.contentId = contentId
		self.target = target
		self.contentIds = None
		self.contentRefId = None
		self.contentRefIds = None
		self.contentType = 0
		self.featureId = float(0)
		self.featuredRefId = None

def build_amf_request(video_player_key, video_content_id, video_url, video_player_id):
	pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
	pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
	content_override = ContentOverride(int(video_content_id))
	viewer_exp_req = ViewerExperienceRequest(video_url, [content_override], int(video_player_id), video_player_key)
	env = remoting.Envelope(amfVersion=3)
	env.bodies.append(
	(
		"/1",
		remoting.Request(
			target = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience",
			body = [CONST, viewer_exp_req],
			envelope = env
		)
	)
	)
	return env
 
def get_swf_url(flash_experience_id, player_id, publisher_id, video_id):
	conn = httplib.HTTPConnection('c.brightcove.com')
	qsdata = dict(width=640, height=480, flashID=flash_experience_id, 
				  bgcolor="#000000", playerID=player_id, publisherID=publisher_id,
				  isSlim='true', wmode='opaque', optimizedContentLoad='true', autoStart='', debuggerID='')
	qsdata['@videoPlayer'] = video_id
	conn.request("GET", "/services/viewer/federated_f9?&" + urllib.urlencode(qsdata))
	resp = conn.getresponse()
	location = resp.getheader('location')
	base = location.split("?",1)[0]
	location = base.replace("BrightcoveBootloader.swf", "federatedVideo/BrightcovePlayer.swf")
	return location