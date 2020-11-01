# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import re

from resources.lib.logger import Logger


class Regexer(object):
    """ Main regexer class """

    __compiledRegexes = dict()
    
    def __init__(self):
        raise Exception("Static only class")

    @staticmethod
    def from_expresso(regex):
        """ Returns a Regex that has the Expresso grouping (.NET) convert to Python grouping. E.g.: (?<Name>...)
        converted to (?P<Name>....)

        :param str regex:   The regex to convert.

        :return: Converted Regex string.
        :rtype: str

        """

        return regex.replace("(?<", "(?P<")

    @staticmethod
    def do_regex(regex, data):
        """ Performs a regular expression and returns a list of matches that came from
        the regex.findall method.
        
        Performs a regular expression findall on the <data> and returns the results that came
        from the method.
        
        From the sre.py library:
        If one or more groups are present in the pattern, return a list of groups; this will be
        a list of tuples if the pattern has more than one group.
    
        Empty matches are included in the result.

        :param list[str|unicode]|str|unicode regex:     The regex to perform on the data.
        :param str|unicode data:                        The data to perform the regex on.

        :return:
        :rtype: list[str|dict[str|unicode,str|unicode]]

        """
                
        try:
            if not isinstance(regex, (tuple, list)):
                if "?P<" in regex:
                    return Regexer.__do_dictionary_regex(regex, data)
                else:
                    return Regexer.__do_regex(regex, data)

            # We got a list of Regexes
            Logger.debug("Performing multi-regex find on '%s'", regex)
            results = []
            count = 0
            for r in regex:
                if "?P<" in r:
                    regex_results = Regexer.__do_dictionary_regex(r, data)
                    # add to the results with a count in front of the results
                    results += [(count, x) for x in regex_results]
                else:
                    regex_results = Regexer.__do_regex(r, data)
                    if len(regex_results) <= 0:
                        continue

                    if isinstance(regex_results[0], (tuple, list)):
                        # is a tupe/list was returned, prepend it with the count
                        # noinspection PyTypeChecker
                        results += [(count,) + x for x in regex_results]
                    else:
                        # create a tuple with the results
                        results += [(count, x) for x in regex_results]
                # increase count
                count += 1
            Logger.debug("Returning %s results", len(results))
            return list(results)
        except:
            Logger.critical('error regexing', exc_info=True)
            return []

    @staticmethod
    def __do_regex(regex, data):
        """ does the actual regex for non-dictionary regexes 
        
        Arguments:
        regex : string - the regex to perform on the data.
        data  : string - the data to perform the regex on.
        
        Returns:
        A list of matches that came from the regex.findall method.
        :rtype: list[str]
       
        """
        
        compiled_regex = Regexer.__get_compiled_regex(regex)
        return compiled_regex.findall(data)
    
    @staticmethod
    def __do_dictionary_regex(regex, data):
        """ Does the actual regex for dictionary regexes and returns a list of matches that
        came from the regex.finditer method.

        :param regex:   The regex to perform on the data.
        :param data:    The data to perform the regex on.

        :return: a list of matches that came from the regex.finditer method.
        :rtype: list[dict[str|unicode,str|unicode]]

        """
        
        compiled_regex = Regexer.__get_compiled_regex(regex)
        it = compiled_regex.finditer(data)
        return [x.groupdict() for x in it]

    @staticmethod
    def __get_compiled_regex(regex):
        """
        @param regex: The input regex to fetch a compiled version from
        @return: a compiled regex
        """

        if regex in Regexer.__compiledRegexes:
            Logger.debug("Re-using cached Compiled Regex object")
            compiled_regex = Regexer.__compiledRegexes[regex]
        else:
            Logger.trace("Compiling Regex object and storing in cache")
            compiled_regex = re.compile(regex, re.DOTALL + re.IGNORECASE)
            Regexer.__compiledRegexes[regex] = compiled_regex

        return compiled_regex
