# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is plugin.games.xbmame.
#
# The Initial Developer of the Original Code is Olivier LODY aka Akira76.
# Portions created by the XBMC team are Copyright (C) 2003-2010 XBMC.
# All Rights Reserved.

import re

class XMLHelper(object):

    def getNodes(self, xml, node):
        return re.findall("(<%s.*?>.*?</%s>|<%s.*?/>)" % (node, node, node), xml)

    def getNodeValue(self, xml, node):
        results = re.findall("<%s.*?>(.*?)</%s>" % (node, node), xml)
        if len(results): return self.decode(results[0])
        else: return ""

    def getAttribute(self, xml, node, attr):
        results = re.findall("<%s.*?%s=\"(.*?)\"" % (node, attr), xml)
        if len(results): return self.decode(results[0])
        else: return ""

    def decode(self, string):
        return string.decode('utf8').replace("&lt;", "<").replace("&gt;", ">").replace("&apos;", "'").replace("&amp;", "&").replace("&quot;","\"")
