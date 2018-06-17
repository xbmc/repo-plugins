import requests

class UrlToLivestreamService:
    
	_TOKEN_URL = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens"
	
	def get_stream_from_url(self, url):
		token_response = requests.post(self._TOKEN_URL)
		token = token_response.json()['vrtPlayerToken']
		stream_response = requests.get(url, {'vrtPlayerToken': token, 'client':'vrtvideo' }).json()
		target_urls = stream_response['targetUrls']
		found_url = False
		index = 0
		while not found_url and index < len(target_urls):
			item = target_urls[index]
			found_url = item['type'] == 'hls_aes'
			stream = item['url']
			index +=1
		return stream


