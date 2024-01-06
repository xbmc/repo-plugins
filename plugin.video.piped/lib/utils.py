from urllib.parse import urlparse, parse_qsl

def get_component(uri: str) -> dict:
	parsed_uri = urlparse(uri)
	params: dict = dict()

	for param in parse_qsl(parsed_uri.query):
		params[param[0]] = param[1]
	
	return dict(
		path = parsed_uri.path,
		params = params
	)

def human_format(num):
	num = float('{:.3g}'.format(num))
	magnitude = 0
	while abs(num) >= 1000:
		magnitude += 1
		num /= 1000.0
	return '{} {}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
