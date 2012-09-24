import sys
import resources.tools as tools

class prime:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "Prime"
  self.urls = dict()
  self.urls['base'] = 'http://www.primetv.co.nz/Portals/1/PrimeNewsVideo/'
  self.urls['file1'] = 'PRIME_'
  self.urls['file2'] = '_Flash.flv'
  self.programs = dict()
  self.programs['News'] = "Prime News: First At 5:30 brings you the top news and sports stories from New Zealand and around the world."
  self.programs['Sport'] = "Business & Sport News"
  self.programs['Weather'] = "The Weather News"
  self.xbmcitems = tools.xbmcItems(self.channel)
  for channel, description in self.programs.iteritems():
   item = tools.xbmcItem()
   item.channel = self.channel
   item.info['Title'] = channel
   item.info["Plot"] = description
   item.info['FileName'] = self.urls['base'] + self.urls['file1'] + channel.upper() + self.urls['file2']
   self.xbmcitems.items.append(item)
  self.xbmcitems.addall()
