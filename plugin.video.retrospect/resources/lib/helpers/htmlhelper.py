# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import re

from resources.lib.regexer import Regexer
from resources.lib.helpers import taghelperbase


class HtmlHelper(taghelperbase.TagHelperBase):
    """Class that could help with parsing of simple HTML"""

    __ToTextRegex = None
    
    def get_tag_content(self, tag, *args, **kwargs):
        """Gets the content of an HTML <tag> 

        Example: ('div', {'cls':'test'}, {'id':'divTest'}) will match

        <div class="test" id="divTest">...content...</div>

        :param str|unicode tag:                     Name of tag to search for.
        :param dict[str|unicode,str|unicode] args:  Each argument is interpreted as a html
                                     attribute. 'cls' is translated to class
                                                    attribute. The attribute with value None \
                                     is retrieved.
        :param any kwargs:  Optional parameters.

        :return: The content of the found tag. If no match is found an empty string is returned.
        :rtype: str|unicode

        Optional parameters:
        bool first_only:    only return the first result. Default: True

        """
        
        first_only = True
        if "first_only" in kwargs:
            first_only = kwargs["first_only"]

        html_regex = "<%s" % (tag,)
                
        for arg in args:
            name = list(arg.keys())[0]
            value = arg[list(arg.keys())[0]]

            # to keep working with older versions where class could not be passed
            if name == "cls":
                name = "class"

            html_regex += r'[^>]*%s\W*=\W*["\']%s["\']' % (name, value)

        html_regex += "[^>]*>([^<]+)</"
        result = Regexer.do_regex(html_regex, self.data)
        if len(result) > 0:
            if first_only:
                return result[0].strip()
            else:
                return result
        else:
            return ""

    @staticmethod
    def to_text(html):
        """ Converts HTML to text by replacing the HTML tags.

        :param str|unicode html: string - HTML text input

        :return: string - Plain text representation of the HTML
        :rtype: str|unicode

        """

        if html is None:
            return html

        if not HtmlHelper.__ToTextRegex:
            HtmlHelper.__ToTextRegex = re.compile(r'<(/?)([^ >]+)(?: [^>]+)?>',
                                                  re.DOTALL + re.IGNORECASE)

        text = HtmlHelper.__ToTextRegex.sub(HtmlHelper.__html_replace, html)
        return text.replace("  ", " ")

    @staticmethod
    def __html_replace(match):
        tag = match.group(2).lower()
        is_start = match.group(1) == ""
        if tag == 'br':
            return '\n'
        elif is_start and tag == "li":
            return '- '
        return ''
