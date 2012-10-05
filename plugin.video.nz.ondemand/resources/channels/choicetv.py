import re, sys

from BeautifulSoup import BeautifulSoup, SoupStrainer

import resources.tools as tools
from resources.tools import webpage

class choicetv:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "ChoiceTV"
  self.urls = dict()
  self.urls['base'] = 'http://catchup.pulsedigital.co.nz'
  self.urls['media'] = 'media'
  self.urls['index'] = 'showall'
  self.xbmcitems = tools.xbmcItems(self.channel)
  self.prefetch = self.xbmcitems.booleansetting('%s_prefetch' % self.channel)

 def index(self, type = 'showall', id = ""):
  page = webpage('/'.join([self.urls['base'], self.urls['media'], type, id]))
  if page.doc:
   div_tag = SoupStrainer('div')
   html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
   programmes = html_divtag.findAll(attrs={'class' : 'col gu1 video'})
   if len(programmes) > 0:
    for program in programmes:
     item = tools.xbmcItem()
     link = re.search("/media/([a-z]+)/([0-9]+)", program.p.a['href'])
     if link:
      item.info["Title"] = program.p.span.string
      item.info["Thumb"] = "%s%s" % (self.urls['base'], program.p.a.img['src'])
      if link.group(1) == "view":
       item.info["Title"] += ' ' + program.p.span.next.next.next.next.next.string.strip()[6:].strip()
       if self.prefetch:
        item.info["FileName"] = self._geturl(link.group(2))
       else:
        item.playable = True
        item.info["FileName"] = "%s?ch=%s&view=%s&info=%s" % (self.base, self.channel, link.group(2), item.infoencode())
      else:
       item.info["FileName"] = "%s?ch=%s&type=%s&id=%s" % (self.base, self.channel, link.group(1), link.group(2))
      self.xbmcitems.items.append(item)
    self.xbmcitems.addall()
   else:
    sys.stderr.write("index: no programmes")
  else:
   sys.stderr.write("index: no page.doc")

 def play(self, id):
  self.xbmcitems.play(self._geturl(id))

 def _geturl(self, id):
  page = webpage('/'.join([self.urls['base'], self.urls['media'], 'view', id]))
  if page.doc:
   link = re.search("'file': 'http(.*?)'", page.doc)
   if link:
    return 'http' + link.group(1)
   else:
    sys.stderr.write("_geturl: no link")
  else:
   sys.stderr.write("_geturl: no page.doc")
    
