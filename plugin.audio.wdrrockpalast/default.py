# -*- coding: utf-8 -*-
import libwdr

class rockpalast(libwdr.libwdr):
	def __init__(self):
		libwdr.libwdr.__init__(self)

	def libWdrListMain(self):
		d = {'items':[]}
		d['items'].append({'metadata':{'name':self.translation(32030)}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-100~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2019'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast264~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2018'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-156~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2017'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-136~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2016'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-106~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2015'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-108~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2014'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-110~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2013'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-112~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2012'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-114~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2011'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-116~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2010'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-118~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2009'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-120~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2008'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-122~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2007'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-124~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2006'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-126~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2005'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-128~_format-mp111_type-rss.feed'}, 'type':'dir'})
		d['items'].append({'metadata':{'name':'2004'}, 'params':{'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-132~_format-mp111_type-rss.feed'}, 'type':'dir'})
		return d

r = rockpalast()
r.action()