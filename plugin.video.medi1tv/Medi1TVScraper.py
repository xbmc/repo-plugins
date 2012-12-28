# -*- coding: UTF-8 -*-
# coding: utf-8

'''

@author: Ayoub DARDORY (Apolikamixitos)
'''

from BeautifulSoup import BeautifulSoup
from Medi1Utils import Medi1Utils
from random import random, randint
from xbmcswift import download_page
from xml.sax.saxutils import unescape
import re
import urllib

class Medi1Shows:

    # Show's attributs :
    # ID
    # Jsname
    # Title
    # Resume
    # Link
    # Thumbnail
    
    @staticmethod
    def load_shows(lang):       
        url = 'http://www.medi1tv.com/' + lang + '/emission.aspx'
        src = download_page(url)
        Shows = []
        regex = '<div id="imgcurrentinfos_corps"[^>]*><a [^\(]*\([^\(]*\(([\d]*),[\d]*,\'([^\']*)\'[^>]*><img src="([^"]*?)"[^>]*?></a></div>[^<]*<div id="currentinfos_corps_bloc"[^<]*<div id="currentinfos_corps_titre"><b>([^<]*)</b></div><div id="currentinfos_corps_resume"[^>]*>(.*?)</div>'
        SShows = re.findall(regex, src, flags=re.DOTALL | re.IGNORECASE | re.UNICODE)
        
        for Show in SShows:
            SShow = {}
            # Show's ID
            SShow['id'] = Show[0]
            # Show's JS name (for program url generation)
            SShow['jsname'] = Show[1]
            
            # Show's Thumbnail
            SShow['thumbnail'] = Medi1Utils.url_fix(Medi1Utils.direct_thumb_link(Show[2]))
            # Show's title
            SShow['title'] = Medi1Utils.unescape_page(Show[3])
            # Show's resume
            SShow['resume'] = Medi1Utils.clear_html_tags(Show[4])
            # Show's link (Show[0] has the ID of the javascript calling parameter)
            SShow['link'] = Medi1Utils.url_fix(Medi1Shows.generate_link_show(Show[0], Show[1], lang))
            
            Shows.append(SShow)
           
            
        # print "Len Total :" + str(len(self.__Shows))
       
        return Shows
    
    
    @staticmethod
    # Generate the show's URL by using its JSName title
    def generate_link_show(idpage, title, lang):
        if(lang != 'ar'):
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + title + '-emissions-' + idpage)
        else:
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + title + '-البرامج-' + idpage)


    @staticmethod
    # Generate the show's URL with
    # id_generator() just to bypass the .htaccess rule for title show (not verified) (/TITLESHOW-emission-IDSHOW)
    # This method is used because of the limitation of the XBMCSwift Framework arguments (from Shows URL to Shows Episodes URL)
    def generate_link_show_randtitle(idpage, lang):
        if(lang != 'ar'):
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + Medi1Utils.id_generator(randint(1, 5)) + '-emissions-' + idpage)
        else:
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + Medi1Utils.id_generator(randint(1, 5)) + '-البرامج-' + idpage)
        
#    To get other specified links (special pages for some shows)
#    def get_link_ids_dict(self, src):
#        regex = 'function changer_location\(id,langue,titre\)(.*?)</script>'
#        tmp = re.findall(regex, src, flags=re.DOTALL | re.IGNORECASE | re.UNICODE)
#        regex = '[^\(]*\(id==([\d]*)\)[^=]*=\'([^\']*)\''
#        tmp = re.findall(regex, tmp[0], flags=re.DOTALL | re.IGNORECASE | re.UNICODE)
#        DictLinks = {}
#        for stemp in tmp:
#            DictLinks[stemp[0]] = stemp[1]
#        return DictLinks

class ShowEpisodes:
    # Episode's attributs :
    # Title
    # Description
    # Date
    # Link
    # Thumbnail
    
    @staticmethod
    def load_videos(lang, url):

        Episodes = []
        
        src = download_page(url)        
        regex = '<div class=\'txt_emission\'[^>]*><a href=\'([^\']*)\'[^>]*>[^<]*<b>([^<]*)</b>[^<]*</a>[^<]*<div><a [^>]*>([^<]*)</a></div><div id=\'txt_emission_date\'>([^>]*)</div></div></td><td[^>]*><a[^>]*><img src="([^"]*)"[^>]*>'
        Eps = re.findall(regex, src, flags=re.DOTALL | re.IGNORECASE | re.UNICODE)
        
        for Episode in Eps:
            SEp = {}
            
            regex = '([^-]*)-'
            # Episode's ID
            Res = re.split(regex, Episode[0])
            SEp['id'] = Res[len(Res) - 2]
            
            # Episode's title
            SEp['title'] = Medi1Utils.unescape_page(Episode[1])
            # Episode's description
            SEp['description'] = Episode[2]
            # Episode's title
            SEp['date'] = Episode[3]
            # Episode's link
            SEp['link'] = Medi1Utils.url_fix("http://www.medi1tv.com/" + lang + "/" + Episode[0])
            # Episode's thumbnail
            SEp['thumbnail'] = Medi1Utils.url_fix(Medi1Utils.direct_thumb_link_large(Episode[4]))           
            Episodes.append(SEp)
      
        return Episodes

    @staticmethod
    def episode_stream(idShow, idEpisode, lang='ar'):
        src = download_page(ShowEpisodes.generate_link_episode_randtitle(idShow, idEpisode, lang))    
        regex = '&file=([^&]*)'
        playpath = re.findall(regex, src, flags=re.DOTALL | re.IGNORECASE | re.UNICODE)[0]
        rtmpurl = 'rtmp://41.248.240.209:80/vod swfUrl=http://www.medi1tv.com/ar/player.swf playpath=' + playpath
        return rtmpurl
        
    @staticmethod
    # Generate the show's URL with
    # id_generator() just to bypass the .htaccess rule for title show (not verified) (/TITLESHOW-emission-IDSHOW)
    # This method is used because of the limitation of the XBMCSwift Framework arguments (from Shows URL to Shows Episodes URL)
    def generate_link_episode_randtitle(idshow, idepisode, lang):
        if(lang == 'ar'):
            # Example : www.medi1tv.com/ar/a-b-برنامج-5320-35
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + Medi1Utils.id_generator(randint(1, 5)) + '-' + Medi1Utils.id_generator(randint(1, 5)) + '-برنامج-' + idepisode + '-' + idshow)
        else:
            return Medi1Utils.url_fix('http://www.medi1tv.com/' + lang + '/' + Medi1Utils.id_generator(randint(1, 5)) + '-' + Medi1Utils.id_generator(randint(1, 5)) + '-emission-' + idepisode + '-' + idshow)
