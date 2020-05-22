import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as datetimeparse
import re
import json

quality_re = re.compile(r'\d+(?=p)')
nl_only_categories = [
	u'NOS Sportjournaal',
	u'NOS Studio Sport',
	u'NOS Studio Sport Eredivisie',
	u'NOS Studio Voetbal',
]

def index():
	data = []
	url = u'https://nos.nl/uitzendingen/'
	response = requests.request(
		method = u'GET',
		url = url,
	)
	soup = BeautifulSoup(response.content, 'html.parser')
	categories_container = soup.findAll(id = u'broadcasts')[0]
	categories = categories_container.findAll(u'li')
	
	data_unique = []
	for category in categories:
		category_anchor = category.findAll(u'a')[0]
		
		category_text = category_anchor.findAll('span')[1].text
		category_text = ' '.join(category_text.split())
		
		category_time = category_anchor.findAll('time')[0].text
		category_time = ' '.join(category_time.split())
		
		category_url  = category_anchor[u'href']
		
		if category_text in nl_only_categories:
			category_text = u'{category_text} (georestricted NL only)'.format( category_text = category_text )
		
		if category_text not in data_unique:
			data_unique.append(category_text)
			
			if category_url.startswith(u'/uitzending/'):
				data.append(
					{
						u'label': category_text + ' - ' + category_time,
						u'path': {
							u'endpoint': u'show_category',
							u'category_url': (
								u'https://nos.nl{category_url}'.format( category_url = category_url )
							),
						},
					}
				)
	return data

def show_category(category_url):
	data = []
	response = requests.request(
		method = u'GET',
		url = category_url,
	)
	soup = BeautifulSoup(response.content, 'html.parser')
	videos = soup.findAll( u'div', {u'class': u'broadcast-player'} )

	for video in videos:
		data_unique = []
		title = video.findAll( u'h1', {u'class': u'broadcast-player-meta__title'} )[0].text
		title = " ".join(title.split())
		timecode = video.findAll(u'time')[0][u'datetime']
		parsed_timecode = datetimeparse(timecode)
		label = u'{title}'.format(title = title)
		date = u'{time}'.format(time = parsed_timecode.strftime(u'%Y-%m-%d %H:%M'))
		videoJSONStr = video.find("script").contents[0]
		videoJSON = json.loads(videoJSONStr)
		
		# add each quality version of the video as an entry
		for vid in videoJSON['formats']:
			quality = vid['name']
			if quality not in data_unique:
				data_unique.append(quality)
				file_url = vid['url']['mp4'].replace("&legacy=resolve.php", "")
				data.append(
					{
						u'label': label + ' - ' + date + ' (' + quality + ')',
						u'path': {
							 u'endpoint': u'show_video',
							 u'video_url': u'{video_url}'.format( video_url = file_url ),
						},
						u'is_playable': True,
					}
				)
	return data

def video_url_to_file_url(video_url):
	return video_url
