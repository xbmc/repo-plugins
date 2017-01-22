# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import xbmcplugin
import libwdr as libWdr

def main():
	l = []
	l.append({'name':'2016', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-106~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2015', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-108~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2014', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-110~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2013', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-112~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2012', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-114~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2011', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-116~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2010', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-118~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2009', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-120~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2008', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-122~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2007', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-124~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2006', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-126~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2005', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-128~_format-mp111_type-rss.feed', '_type':'dir'})
	l.append({'name':'2004', 'mode':'libWdrListFeed', 'url':'http://www1.wdr.de/mediathek/video/sendungen/rockpalast/rockpalast-132~_format-mp111_type-rss.feed', '_type':'dir'})
	return l

def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	mode = params.get('mode','main')
	if mode.startswith('libWdr'):
		libWdr.list()
	else:
		l = modes.get(mode)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	

modes = {
'main': main,
}	

list()