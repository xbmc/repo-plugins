# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import urllib
import re

class SearchEngine:
    YAHOO_SEARCH_STRING = 'http://search.yahooapis.com/ImageSearchService/V1/imageSearch?query=%s&appid=1'

    def __init__( self ):
        pass

    def search(self, query):
        # prepare search string
        query = self.YAHOO_SEARCH_STRING % (query, )
        query = query.replace(" ","%20")

        # open the search string
        usock = urllib.urlopen(query)
        
        # read source
        xmlSource = usock.read()

        # close socket
        usock.close()

        # make it single line
        xmlSource = xmlSource.replace("\n","").replace("\r","")

        # get the results
        results = re.findall( "<Result>(.*?)</Result>", xmlSource )
        result_of_query = []

        for result in results:
            title = re.findall( "<Title>(.*?)</Title>", result )
            url = re.findall( "<Url>(.*?)</Url>", result )
            thumb = re.findall( "<Thumbnail><Url>(.*?)</Url>", result )
            result_data = {}
            result_data["title"] = title[0]
            result_data["url"] = url[0]
            result_data["thumb"] = thumb[0]
            result_of_query.append(result_data)
            
        return result_of_query
