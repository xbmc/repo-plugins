# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.regexer import Regexer
from resources.lib.logger import Logger


class TagHelperBase(object):
    """Base class that holds the mutual code for XMLHelper and HTMLHelper"""
        
    def __init__(self, data):
        """Creates a class object with HTML <data>
        
        Arguments:
        data : string - HTML data to parse
        
        """
        
        self.data = data
    
    def get_tag_attribute(self, tag, *args, **kwargs):
        """Gets the content of an specific attribute of an HTML <tag>
        
        Arguments:
        tag    : string     - name of tag to search for.
        **args : dictionary - each argument is interpreted as a html 
                              attribute. 'cls' is translated to class 
                              attribute. The attribute with value None 
                              is retrieved.
        
        Keyword Arguments:
        firstOnly : [opt] boolean - only return the first result. Default: True
        
        Returns:
        The content of the attribute of the found tag. If no match is found 
        an empty string is returned.
        
        Example: ('div', {'cls':'test'}, {'id':'divTest'}, {'width':None}, {'alt':'test'}) will match 
        <div class="test" id="divTest" width="20" alt="test">...content...</div> and 
        will return 20. 
        
        """
        
        first_only = True
        if list(kwargs.keys()).count("firstOnly") > 0:
            first_only = kwargs["firstOnly"]
            Logger.trace("Setting 'firstOnly' to '%s'", first_only)
            
        html_regex = '<%s' % (tag,)
        
        for arg in args:
            name = list(arg.keys())[0]
            value = arg[list(arg.keys())[0]]
            Logger.trace("Name: %s, Value: %s", name, value)
            
            # to keep working with older versions where class could not be passed
            if name == "cls":
                name = "class"
            
            if value is None:
                html_regex += r'[^>]*%s\W*=\W*["\']([^"\']+)["\']' % (name,)
            else:
                html_regex += r'[^>]*%s\W*=\W*["\']%s["\']' % (name, value)

        html_regex += "[^>]*>"
        Logger.trace("HtmlRegex = %s", html_regex)
        
        result = Regexer.do_regex(html_regex, self.data)
        Logger.trace(result)
        
        if len(result) > 0:
            if first_only:
                return result[0].strip()
            else:
                return result
        else:
            return ""
