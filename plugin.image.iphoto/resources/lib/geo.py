"""
    Geocoding and map fetching utilities using Google Maps.

    Portions taken and modified from Brian Beck's geo.py toolbox:
    http://code.google.com/p/geopy/source/browse/trunk/LICENSE
"""

__author__ = "jingai <jingai@floatingpenguins.com>"
__credits__ = "jingai, Brian Beck"
__url__ = "git://github.com/jingai/plugin.image.iphoto.git"

import os
import sys
try:
    import xbmc
except:
    pass
from urllib2 import Request,urlopen,unquote,HTTPError
from urllib import urlencode,urlretrieve,urlcleanup
try:
    import simplejson as json
except:
    import json
import xml.dom.minidom
from xml.parsers.expat import ExpatError
from traceback import print_exc

GOOGLE_DOMAIN = "maps.googleapis.com"

MAP_ZOOM_MIN = 1
MAP_ZOOM_MAX = 21
MAP_IMAGE_X_MAX = 640
MAP_IMAGE_Y_MAX = 640
MAP_IMAGE_X_MIN = 100
MAP_IMAGE_Y_MIN = 100
MAP_MARKER_COLOR = "red"
MAP_MARKER_LABEL = "P"

HTTP_USER_AGENT = 'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16'


def get_encoding(page, contents=None):
    plist = page.headers.getplist()
    if plist:
	key, value = plist[-1].split('=')
	if key.lower() == 'charset':
	    return value

    if contents:
	try:
	    return xml.dom.minidom.parseString(contents).encoding
	except ExpatError:
	    pass

def decode_page(page):
    contents = page.read()
    # HTTP 1.1 defines iso-8859-1 as the 'implied' encoding if none is given
    encoding = get_encoding(page, contents) or 'iso-8859-1'
    return unicode(contents, encoding=encoding).encode('utf-8')

class GeocoderError(Exception):
    pass

class GeocoderResultError(GeocoderError):
    pass

class GQueryError(GeocoderResultError):
    pass

class GTooManyQueriesError(GeocoderResultError):
    pass

def check_status(status):
    if status == 'ZERO_RESULTS':
	raise GQueryError("Geocode was successful but returned no results.")
    elif status == 'OVER_QUERY_LIMIT':
	raise GTooManyQueriesError("The given key has gone over the requests limit in the 24 hour period or has submitted too many requests in too short a period of time.")
    elif status == 'REQUEST_DENIED':
	raise GQueryError("Request was denied, generally because of lack of a sensor parameter.")
    elif status == 'INVALID_REQUEST':
	raise GQueryError("Invalid request.  Probably missing address or latlng.")
    else:
	raise GeocoderResultError("Unknown error.")

# forward geocode an address or reverse geocode a latitude/longitude pair.
# input loc should not be pre-urlencoded (that is, use spaces, not plusses).
#
# returns all addresses found with their corresponding lat/lon pairs, unless
# exactly_one is True, which returns just the first (probably best) match.
def geocode(loc, exactly_one=True):
    req_url = "http://%s/maps/api/geocode/json" % (GOOGLE_DOMAIN.strip('/'))
    req_hdr = { 'User-Agent':HTTP_USER_AGENT }
    req_par = { 'latlng':loc, 'sensor':'false', 'output':'json' }
    req_dat = urlencode(req_par)

    req = Request(unquote(req_url + "?" + req_dat), None, req_hdr)
    resp = urlopen(req)
    if not isinstance(resp, basestring):
	resp = decode_page(resp)

    doc = json.loads(resp)
    places = doc.get('results', [])

    if not places:
	check_status(doc.get('status'))
	return None

    def parse_place(place):
	location = place.get('formatted_address')
	latitude = place['geometry']['location']['lat']
	longitude = place['geometry']['location']['lng']
	return (location, (latitude, longitude))

    if exactly_one:
	return parse_place(places[0])
    else:
	return [parse_place(place) for place in places]

# class to fetch map image files using the Google Staticmaps API.
class staticmap:
    def __init__(self, imagepath="", loc="", marker=True, imagefmt="", zoomlevel=18, xsize=640, ysize=640, maptype=""):
	if (imagepath == ""):
	    raise ValueError("imagepath is required.")
	self.imagepath = imagepath

	if (loc == ""):
	    raise ValueError("loc (lat/lon pair or address) is required.")
	self.loc = loc
	self.showmarker = marker
	self.marker = "color:%s|label:%s|%s" % (MAP_MARKER_COLOR, MAP_MARKER_LABEL, self.loc)

	self.imagefmt = (imagefmt or "jpg")

	if (zoomlevel < MAP_ZOOM_MIN or zoomlevel > MAP_ZOOM_MAX):
	    raise ValueError("zoomlevel must be between %d and %d" % (MAP_ZOOM_MIN, MAP_ZOOM_MAX))
	self.zoomlevel = zoomlevel

	if (xsize < MAP_IMAGE_X_MIN or xsize > MAP_IMAGE_X_MAX):
	    raise ValueError("xsize must be between %d and %d" % (MAP_IMAGE_X_MIN, MAP_IMAGE_X_MAX))
	if (ysize < MAP_IMAGE_Y_MIN or ysize > MAP_IMAGE_Y_MAX):
	    raise ValueError("ysize must be between %d and %d" % (MAP_IMAGE_Y_MIN, MAP_IMAGE_Y_MAX))
	self.xsize = xsize
	self.ysize = ysize

	self.maptype = (maptype or "hybrid")

    def set_imageformat(self, imagefmt):
	if (imagefmt != ""):
	    self.imagefmt = (imagefmt or "jpg")

    def set_xsize(self, xsize):
	if (xsize >= MAP_IMAGE_X_MIN and xsize <= MAP_IMAGE_X_MAX):
	    self.xsize = xsize

    def set_ysize(self, ysize):
	if (ysize >= MAP_IMAGE_Y_MIN and ysize <= MAP_IMAGE_Y_MAX):
	    self.ysize = ysize

    def set_type(self, maptype):
	self.maptype = (maptype or "hybrid")

    def toggle_marker(self):
	self.showmarker = not self.showmarker

    def zoom(self, way, step=1):
	if (way == "+"):
	    self.zoomlevel = self.zoomlevel + step
	elif (way == "-"):
	    self.zoomlevel = self.zoomlevel - step
	else:
	    self.zoomlevel = step
	if (self.zoomlevel < MAP_ZOOM_MIN):
	    self.zoomlevel = MAP_ZOOM_MIN
	if (self.zoomlevel > MAP_ZOOM_MAX):
	    self.zoomlevel = MAP_ZOOM_MAX

    def fetch(self, file_prefix="", file_suffix=""):
	imagefile = ""

	try:
	    imagefile = os.path.join(self.imagepath, file_prefix + self.loc + file_suffix + "." + self.imagefmt)
	    if (os.path.isfile(imagefile)):
		return imagefile

	    req_url = "http://%s/maps/api/staticmap" % (GOOGLE_DOMAIN.strip('/'))
	    # descriptions of permissible paramaters can be found here:
	    # http://gmaps-samples.googlecode.com/svn/trunk/geocoder/singlegeocode.html
	    req_par = {
		"zoom":self.zoomlevel,
		"size":"%dx%d" % (self.xsize, self.ysize),
		"format":"%s" % (self.imagefmt),
		"maptype":"%s" % (self.maptype),
		"sensor":"false"
	    }
	    if (self.showmarker == True):
		req_par['markers'] = self.marker
	    else:
		req_par['center'] = self.loc
	    if (self.xsize <= 256 or self.ysize <= 256):
		req_par['style'] = "feature:road.local|element:geometry|visibility:simplified"
	    req_dat = urlencode(req_par)
	except Exception, e:
	    raise e

	try:
	    try:
		xbmc.sleep(1000)
	    except:
		pass
	    urlretrieve(unquote(req_url + "?" + req_dat), imagefile)
	except HTTPError, e:
	    print smart_utf8(e.geturl())
	    raise e
	except:
	    urlcleanup()
	    remove_tries = 3
	    while remove_tries and os.path.isfile(imagefile):
		try:
		    os.remove(imagefile)
		except:
		    remove_tries -= 1
		    try:
			xbmc.sleep(1000)
		    except:
			pass

	return imagefile

if (__name__ == "__main__"):
    try:
	lat = sys.argv[1]
	lon = sys.argv[2]
    except:
	print "Usage geo.py <latitude> <longitude>"
	sys.exit(1)

    try:
	places = geocode("%s,%s" % (lat, lon), False)
	for p in places:
	    print places

	loc = "%s+%s" % (lat, lon)
	map = staticmap("./", loc)
	map.set_xsize(640)
	map.set_ysize(640)
	print map.fetch("map_", "")
    except:
	print_exc()

# vim: tabstop=8 softtabstop=4 shiftwidth=4 noexpandtab:
