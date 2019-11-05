# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.regexer import Regexer


class Smil(object):
    """Class that could help with parsing of simple Smil files"""
    
    def __init__(self, data):
        """Creates a class object with Smil <data>

        Example data:
        
        <smil xmlns="http://www.w3.org/2001/SMIL20/Language">
        <head>
           <meta name="title" content="myStream"/>
           <meta name="httpBase" content="http://mydomain.com/"/>
           <meta name="rtmpPlaybackBase" content="http://mydomain.com/"/>
        </head>
        <body>
           <switch>
              <video src="myStream500K@54552" system-bitrate="500000"/>
              <video src="myStream900K@54552" system-bitrate="900000"/>
              <video src="myStream1500K@54552" system-bitrate="1500000"/>
           </switch>
        </body>

        :param str data:    Smil data to parse.

        """
        
        self.data = data
    
    def get_base_url(self):
        """ Retrieves the BaseUrl from the Smil data.
        
        From the example data it would be http://mydomain.com

        :return: the base URL for the playlist.
        :rtype: str

        """
        
        regex = '<meta base="([^"]+)" />'
        results = Regexer.do_regex(regex, self.data)
        if len(results) > 0:
            return results[0]
        else:
            regex = r'<meta name="httpBase" content="([^"]+)"\W*/>'
            results = Regexer.do_regex(regex, self.data)
            if len(results) > 0:
                return results[0]
            else:            
                return ""
    
    def get_best_video(self):
        """ Returns a list of video's with the highest quality.
        
        In this case: myStream1500K@54552

        :return: The best available stream.
        :rtype: str

        """
        
        urls = self.get_videos_and_bitrates()
        if urls is None:
            return ""

        urls.sort(key=lambda u: -int(u[1]))
        return urls[0][0]
    
    def get_videos_and_bitrates(self):
        """ Retrieves all video's and bitrates in the Smil file.
        
        In this case:

            ["myStream500K@54552", "500000"]
            ["myStream900K@54552", "900000"]
            ["myStream1500K@54552", "1500000"]

        :return: A list of all video's and bitrates in the Smil file.
        :rtype: list[list[str,str]]

        """
        
        regex = '<video src="([^"]+)"[^>]+system-bitrate="([^"]+)"'
        results = Regexer.do_regex(regex, self.data)
        if len(results) > 0:
            return results
        else:
            return None
    
    def get_subtitle(self):
        """ Retrieves the URL of the included subtitle

        :return: The url for the subtitle
        :rtype: str

        """
        
        regex = r'<param\W*name="subtitle"[^>]*value="([^"]+)'
        urls = Regexer.do_regex(regex, self.data)
        
        for url in urls:
            if "http:" in url:            
                return url
            else:
                return "%s/%s" % (self.get_base_url().rstrip("/"), url.lstrip("/"))
        
        return ""
    
    def strip_type_start(self, url):
        """ Strips the first part of an URL up to the first /

        Example:
        mp4:/mp4root/2009-04-14/pid201_671978_T1L__671978_T6MP48_.mp4 -> /mp4root/2009-04-14/pid201_671978_T1L__671978_T6MP48_.mp4 

        :param str url:     The URL to strip.

        :return: The url with the first part (until /) stripped, duh!
        :rtype: str

        """
        
        pos = url.find('/')
        return url[pos:]
