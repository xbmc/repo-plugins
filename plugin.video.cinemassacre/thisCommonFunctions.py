'''
   Parsedom for XBMC plugins
   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import urllib
import urllib2
import re
import CommonFunctions as common

def parseDOM(html, name=u"", attrs={}, ret=False):
    common.log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)

    if isinstance(name, str): # Should be handled
        try:
            name = name #.decode("utf-8")
        except:
            common.log("Couldn't decode name binary string: " + repr(name))

    if isinstance(html, str):
        try:
            html = [html.decode("utf-8")] # Replace with chardet thingy
        except:
            common.log("Couldn't decode html binary string. Data length: " + repr(len(html)))
            html = [html]
    elif isinstance(html, unicode):
        html = [html]
    elif not isinstance(html, list):
        common.log("Input isn't list or string/unicode.")
        return u""

    if not name.strip():
        common.log("Missing tag name")
        return u""

    ret_lst = []
    for item in html:
        temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
        for match in temp_item:
            item = item.replace(match, match.replace("\n", " "))

        lst = common._getDOMElements(item, name, attrs)

        if isinstance(ret, str):
            common.log("Getting attribute %s content for %s matches " % (ret, len(lst) ), 3)
            lst2 = []
            for match in lst:
                lst2 += common._getDOMAttributes(match, name, ret)
            lst = lst2
        else:
            common.log("Getting element content for %s matches " % len(lst), 3)
            lst2 = []
            for match in lst:
                common.log("Getting element content for %s" % match, 4)
                temp = common._getDOMContent(item, name, match, ret).strip()
                if temp:
                    item = item[item.find(temp, item.find(match)) + len(temp):]
                    lst2.append(temp)
            lst = lst2
        ret_lst += lst

    common.log("Done: " + repr(ret_lst), 3)
    return ret_lst
