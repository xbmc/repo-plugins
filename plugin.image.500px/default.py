import urllib2

import simplejson as json
import xbmcgui
import xbmcplugin
baseFeedUrl = "https://api.500px.com/v1/photos?feature={feature}&page={page}&consumer_key=LvUFQHMQgSlaWe3aRQot6Ct5ZC2pdTMyTLS0GMfF"
basePhotoUrl = " https://api.500px.com/v1/photos/{photoid}?image_size=4&consumer_key=LvUFQHMQgSlaWe3aRQot6Ct5ZC2pdTMyTLS0GMfF"
thisPlugin = int(sys.argv [1])
featureNames = ['popular', 'upcoming', 'editors', 'fresh_today', 'fresh_yesterday', 'fresh_week']
index = int(xbmcplugin.getSetting(thisPlugin, 'feature'))
featureName = featureNames[index]
PHOTOS_PER_PAGE = 20
def createListing():
  global featureName
  global thisPlugin
  quantityIndex = int(xbmcplugin.getSetting(thisPlugin, 'quantity')) + 1
  quantity = quantityIndex * PHOTOS_PER_PAGE
  print '**** quantity: ' + str(quantity)
  pageNumber = 1
  while pageNumber <= quantityIndex:
    feedUrl = baseFeedUrl.format(feature=featureName, page=pageNumber)
    print '**** FEED URL:' + feedUrl
    pageNumber = pageNumber + 1
    feedData = urllib2.urlopen(feedUrl)
    feedJson = json.load(feedData)
    photos = feedJson['photos']
    for photoFromFeed in photos:
      id = photoFromFeed['id']
      photoData = urllib2.urlopen(basePhotoUrl.format(photoid=id))
      photoJson = json.load(photoData)
      photoDetails = photoJson['photo']
      listItem = xbmcgui.ListItem(photoDetails['name'], '', '', '', '')
      xbmcplugin.addDirectoryItem(thisPlugin, photoDetails['image_url'], listItem, False, quantity)
  xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=True)
createListing()




