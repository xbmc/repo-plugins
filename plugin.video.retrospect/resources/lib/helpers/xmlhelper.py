# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.regexer import Regexer
from resources.lib.helpers.taghelperbase import TagHelperBase

#===============================================================================
# Make global object available
#===============================================================================
from resources.lib.logger import Logger


class XmlHelper(TagHelperBase):
    """Class that helps getting the content of XML nodes"""

    def get_single_node_content(self, node_tag, *args, **kwargs):
        """Retrieves a single node
        
        Arguments:
        nodeTag : string     - Name of the node to retrieve 
        args    : dictionary - Dictionary holding the node's attributes. Should
                               occur in order of appearance.
        
        Keyword Arguments:
        stripCData : Bool - If True the <![CDATA[......]]> will be removed.
        
        Returns:
        the content of the first match that is found.
        
        The args should be a dictionary: {"size": "380x285"}, {"ratio":"4:3"} 
        will find a node with <nodename size="380x285" name="test" ratio="4:3">
        
        """
        
        if "stripCData" in kwargs:
            strip_cdata = kwargs["stripCData"]
        else:
            strip_cdata = False
        
        result = self.get_nodes_content(node_tag, *args)
        if len(result) > 0:
            if strip_cdata:
                return XmlHelper.__strip_cdata(result[0])
            else:
                return result[0]
        else:
            return ""
    
    def get_nodes_content(self, node_tag, *args):
        """Retrieves all nodes with nodeTag as name
        
        Arguments:
        nodeTag : string     - Name of the node to retrieve 
        args    : dictionary - Dictionary holding the node's attributes. Should
                               occur in order of appearance.
        
        Returns:
        A list of all the content of the found nodes.
        
        The args should be a dictionary: {"size": "380x285"}, {"ratio":"4:3"} 
        will find a node with <nodename size="380x285" name="test" ratio="4:3">
        
        """
        
        regex = "<%s" % (node_tag,)
        
        for arg in args:
            regex += r'[^>]*%s\W*=\W*"%s"' % (list(arg.keys())[0], arg[list(arg.keys())[0]])
            # just do one pass

        regex += r"[^>]*>([\w\W]+?)</%s>" % (node_tag,)
        Logger.trace("XmlRegex = %s", regex)

        results = Regexer.do_regex(regex, self.data)
        Logger.trace(results)
        return results
    
    @staticmethod
    def __strip_cdata(data):
        """ Strips the <![CDATA[......]]> from XML data tags 
        
        Arguments:
        data : String - The data to strip from.
        
        """

        return data.replace("<![CDATA[", "").replace("]]>", "")
