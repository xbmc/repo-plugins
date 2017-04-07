# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import xbmcplugin
import xbmcaddon
import libwdr

translation = xbmcaddon.Addon().getLocalizedString

def main():
	l = []
	l.append({'_name':translation(30001), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/indexstreamsundticker100~_format-mp111_type-rss.feed', '_type':'dir'})#Live
	l.append({'_name':translation(30002), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht102~_format-mp111_type-rss.feed', '_type':'dir'})#Newest
	l.append({'_name':translation(30003), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht104~_format-mp111_type-rss.feed', '_type':'dir'})#Football
	l.append({'_name':translation(30004), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht-wintersport-100~_format-mp111_type-rss.feed', '_type':'dir'})#Wintersports
	l.append({'_name':translation(30005), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht106~_format-mp111_type-rss.feed', '_type':'dir'})#DTM
	l.append({'_name':translation(30006), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht116~_format-mp111_type-rss.feed', '_type':'dir'})#Sportnetzschau
	l.append({'_name':translation(30007), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht140~_format-mp111_type-rss.feed', '_type':'dir'})#Handball
	l.append({'_name':translation(30008), 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/video/videouebersicht112~_format-mp111_type-rss.feed', '_type':'dir'})#Other
	#l.append({'_name':'Tor des Monats', 'mode':'goals'})
	return l
	
def goals():
	l = []
	l.append({'name':'2016', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2016index102~_format-mp111_type-rss.feed'})
	l.append({'name':'2015', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2015index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2014', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2014index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2013', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2013index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2012', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2012index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2011', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2011index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2010', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik10er/tdm2010index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2009', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2009index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2008', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2008index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2007', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2007index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2006', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2006index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2005', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2005index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2004', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2004index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2003', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2003index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2002', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2002index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2001', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2001index100~_format-mp111_type-rss.feed'})
	l.append({'name':'2000', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik00er/tdm2000index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1999', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1999index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1998', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1998index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1997', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1997index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1996', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1996index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1995', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1995index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1994', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1994index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1993', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1993index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1992', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1992index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1991', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1991index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1990', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik90er/tdm1990index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1989', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1989index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1988', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1988index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1987', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1987index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1986', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1986index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1985', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1985index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1984', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1984index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1983', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1983index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1982', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1982index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1981', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1981index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1980', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik80er/tdm1980index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1979', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1979index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1978', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1978index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1977', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1977index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1976', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1976index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1975', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1975index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1974', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1974index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1973', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1973index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1972', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1972index100~_format-mp111_type-rss.feed'})
	l.append({'name':'1971', 'mode':'libWdrListFeed', 'url':'http://www.sportschau.de/sendung/tdm/archiv/chronik70er/tdm1971index100~_format-mp111_type-rss.feed'})
	return l

modes = {
'main': main,
'goals': goals,
}
	
def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	mode = params.get('mode','main')
	if mode.startswith('libWdr'):
		libwdr.list()
	else:
		l = modes.get(mode)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	
list()