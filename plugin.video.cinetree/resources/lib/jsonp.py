
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import json
import re
import logging

from codequick.support import logger_id
from .errors import ParseError


logger = logging.getLogger('.'.join((logger_id, __name__)))


def parse(document: str) -> dict:
    """Parse a jsonp document and return a dict representation of the json object returned by the js function.

    The jsonp responses from cinetree are basically functions with a bunch of parameters that are
    being called with a matching amount arguments. The function just returns a js object consisting
    of key-value pairs and lists

    This function extracts the return statement in the function body and arguments from the response.
    Arguments are inserted at each place they are referenced in the js object. Finally, the js code
    is converted in such a way that it is a json parsable string.

    The function returns the python dict created by doing a json.loads(...).

    :param document: A string containing a jsonp document as retrieved from the web.

    """
    try:
        if '__NUXT_' not in document[:16]:
            logger.error('JSONP parse error: Document does not contain parsable JSONP.')
            raise ParseError

        # Replace any occurrence of 'void 0' by a json compatible 'null'
        document = document.replace('void 0', 'null')
        # In some documents there are empty objects as argument. Replace for None, so they don't interfere
        # with further processing, in particular with finding the end of the function body
        document = document.replace('{}', 'null')

        # Split the document in the function body, parameter and arguments list
        funct, args = document.rsplit('}', 1)
        _, funct = funct.split('function(', 1)

        # Find the closing parentheses of the function definition and split the string
        # in the parameter list and function body
        params, _, funct = funct.partition(')')

        # Some jsonp responses the function start with a return statement, others start with
        # assigning some values to variables, followed by a return statement.
        # In either way, we are only interested in the returned object.
        start = funct.find('return {', 1)
        # Strip anything up to the matching closing brace.
        funct = funct[start + 7:]

        # create a lists of parameters
        param_list = params.split(",")
        # Create a list of arguments
        args_list = _create_args_list(args)
    except(IndexError, ValueError, TypeError, AttributeError):
        logger.error("JSONP parse error: document does not have the expected structure", exc_info=True)
        raise ParseError

    # create mapping af parameter to their respective argument
    args_map = dict(zip(param_list, args_list))

    funct = _substitute_args(funct, args_map)

    # Now the function body should be valid json
    try:
        return json.loads(funct)
    except json.JSONDecodeError:
        logger.error("JSONP parse error: failed to parse jsonp return statement.", exc_info=True)
        raise ParseError


def _create_args_list(args: str) -> list:
    """Return a list of arguments from the string `args_str`.

    Modify args_str in such a way it can be parsed as json string and data
    are preserved in their original type, like text, numbers, True, False and None.
    Parse the result and return the arguments as list.

    :param args: raw string of arguments
    :return: list of arguments

    """
    # Create JSON list from the raw args
    arg_str = ''.join(('[', args[1:].rstrip('});'), ']'))

    # Since json.loads() un-escapes everything we need to escape backslashes again in order to
    # preserve them for the final json load of the function body. But this effectively unescapes
    # escaped quotes, so we need to add en extra backslash to solve that.
    arg_str = arg_str.replace('\\', '\\\\').replace(r'\"', r'\\"')

    # Filter out any argument that is not a text, number, true, false or null.
    # e.g. a js function, or a variable.
    def replace_str(match):
        match_txt = match.group(1)
        if match_txt in ('true', 'false', 'null'):
            return match.group(0)
        else:
            return ',null'

    # Find text that:
    #   - starts with a comma,
    #   - followed not by normal upper or lower case letter,
    #     thus excluding normal text, starting with '"' and numbers.
    #   - followed by any number of 'normal' characters found in js functions, including whitespace,
    #     but excluding '"'.
    #   - Must be followed by a comma.
    #     As such specifically excluding normal text that ends with '",'.
    #
    # FIXME: This kinda relies on arguments of type text to have a space after a comma
    #        when there is a comma within that text.
    #        However, it will only be a problem when the text has more than one comma
    #        and the character directly following the comma is a normal letter. Any other
    #        characters, like a space or special markdown character will cause the whole
    #        text to be disregarded. As well as text with a single comma and missing
    #        whitespace, because the text will then end with a '"'.
    #        In all not a perfect solution, but working in practice.

    arg_str = re.sub(r',([a-zA-Z][\w(){}[\]\s]+)(?=,)', replace_str, arg_str)

    try:
        return json.loads(arg_str)
    except json.JSONDecodeError:
        logger.error("JSONP parse error: failed to parse arguments list", exc_info=True)
        raise ParseError


def _substitute_args(jsonp_doc: str, args_map: dict) -> str:
    """Replace all parameters with their corresponding argument value and ensure that keys
    are enclosed in double quotes.

    :param jsonp_doc: String containing a jsonp function body
    :param args_map: Dictionary mapping parameters the passed arguments
    :return: A new document with all parameters substituted for their value.

    """
    def replace_arg(match):
        """Function that actually replaces parameters by their corresponding argument value.

        Take a match object, decide if it is a known parameter and replace it by its
        value if it is. If not, return the string unaltered.

        """
        param = match.group(0)
        try:
            arg_val = args_map[param]
        except KeyError:
            return param

        if isinstance(arg_val, str):
            new_val = ''.join(('"', arg_val.replace('\n', '\\n'), '"'))
        else:
            new_val = 'null' if arg_val is None else str(arg_val).lower()
        return new_val

    # Regex to replace arguments
    find_param_pattern = re.compile(r'(?<=[\[:{,])[A-Za-z0-9_$]{1,3}(?=[\s,}\]])')
    # Regex to find keys that are to be enclosed in quotes.
    find_key_pattern = re.compile(r'([}{\]\[,])(\w+):')

    def insert_vars_and_quote_keys(match):
        """Search for parameter sequence in the match and perform a replace on found
        parameters. Also search for keys and enclose them in double quotes in order to
        comply to json standards.

        The passed match can contain quoted as wel as un-quoted string, but only un-quoted
        string are in capture group 1. To ensure not te replace anything resembling a
        parameter or a key in normal text, only perform the operations on the parts that are
        not enclosed in double quotes, i.e when match has group 1.

        """
        orig_str = match.group(1)
        if not orig_str:
            return match.group(0)

        result = find_param_pattern.sub(replace_arg, orig_str)
        # In order to comply to json standards ensure that keys are quoted strings.
        result = find_key_pattern.sub(r'\1"\2":', result)
        return result

    # regex that produces either quoted or unquoted parts, disregarding backslash escaped quotes.
    new_doc = re.sub(r'\"(?:\\"|[^\"])*\"|([^\"]+)', insert_vars_and_quote_keys, jsonp_doc)
    return new_doc


def parse_simple(jsonp_doc):
    # Parse a simple jsonp doc, without function and arguments.
    try:
        resp = jsonp_doc.partition('{')[2]
        resp = resp.rsplit('}')[0]
        resp = ''.join(('{', resp, '}'))
        resp = _substitute_args(resp, {})  # only to ensure keys are quoted
        resp_dict = json.loads(resp)
        return resp_dict
    except (IndexError, TypeError, AttributeError, json.JSONDecodeError) as e:
        logger.warning("failed to parse simple jsonp: %r", e)
        raise ParseError
