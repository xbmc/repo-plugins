# -*- coding: utf-8 -*-

# Advanced MAME Launcher MAME filter engine.

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# --- Python standard library ---
# Division operator: https://www.python.org/dev/peps/pep-0238/
from __future__ import unicode_literals
from __future__ import division

import xml.etree.ElementTree as ET

# --- Modules/packages in this plugin ---
from .constants import *
from .utils import *
from .utils_kodi import *
from .misc import *
from .disk_IO import *

# -------------------------------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------------------------------
OPTIONS_KEYWORK_LIST = [
    'NoClones',
    'NoCoin',
    'NoCoinLess',
    'NoROMs',
    'NoCHDs',
    'NoSamples',
    'NoMature',
    'NoBIOS',
    'NoMechanical',
    'NoImperfect',
    'NoNonworking',
    'NoVertical',
    'NoHorizontal',
]

# -------------------------------------------------------------------------------------------------
# Parse filter XML definition
# -------------------------------------------------------------------------------------------------
#
# Strips a list of strings.
#
def _strip_str_list(t_list):
    for i, s_t in enumerate(t_list):
        t_list[i] = s_t.strip()

    return t_list

#
# Returns a comma-separated string of values as a list of strings.
#
def _get_comma_separated_list(text_t):
    if not text_t:
        return []
    else:
        return _strip_str_list(text_t.split(','))

#
# Parse a string 'XXXXXX with YYYYYY' and return a tuple.
#
def _get_change_tuple(text_t):
    if not text_t: return ()
    # Returns a list of strings or list of tuples.
    tuple_list = re.findall('(\w+) with (\w+)', text_t)
    if tuple_list:
        return tuple_list[0]
    else:
        log_error('_get_change_tuple() text_t = "{0}"'.format(text_t))
        m = '(Exception) Cannot parse <Change> "{0}"'.format(text_t)
        log_error(m)
        raise Addon_Error(m)

# -------------------------------------------------------------------------------------------------
# String Parser (SP) engine. Grammar token objects.
# Parser inspired by http://effbot.org/zone/simple-top-down-parsing.htm
#
# SP operators: and, or, not, has, lacks, literal.
# -------------------------------------------------------------------------------------------------
debug_SP_parser = False
debug_SP_parse_exec = False

class SP_literal_token:
    def __init__(self, value):
        self.value = value
        self.id = "STRING"
    def nud(self):
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing LITERAL token value "{0}"'.format(self.value))
        ret = self.value
        if debug_SP_parser: log_debug('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return '<LITERAL "{0}">'.format(self.value)

class SP_operator_has_token:
    lbp = 50
    def __init__(self):
        self.id = "OP HAS"
    def nud(self):
        self.first = SP_expression(50)
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing HAS token')
        ret = True if SP_parser_search_string.find(self.first.exec_token()) >= 0 else False
        if debug_SP_parser: log_debug('HAS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP has>"

class SP_operator_lacks_token:
    lbp = 50
    def __init__(self):
        self.id = "OP LACKS"
    def nud(self):
        self.first = SP_expression(50)
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing LACKS token')
        ret = False if SP_parser_search_string.find(self.first.exec_token()) >= 0 else True
        if debug_SP_parser: log_debug('LACKS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP lacks>"

class SP_operator_not_token:
    lbp = 50
    def __init__(self):
        self.id = "OP NOT"
    def nud(self):
        self.first = SP_expression(50)
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_SP_parser: log_debug('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP not>"

class SP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_SP_parser: log_debug('Executing AND token')
        self.first = left
        self.second = SP_expression(10)
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_SP_parser: log_debug('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP and>"

class SP_operator_or_token:
    lbp = 10
    def __init__(self):
        self.id = "OP OR"
    def led(self, left):
        self.first = left
        self.second = SP_expression(10)
        return self
    def exec_token(self):
        if debug_SP_parser: log_debug('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_SP_parser: log_debug('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP or>"

class SP_end_token:
    lbp = 0
    def __init__(self):
        self.id = "END TOKEN"
    def __repr__(self):
        return "<END token>"

# -------------------------------------------------------------------------------------------------
# String Parser (SP) Tokenizer
# See http://jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
# -------------------------------------------------------------------------------------------------
SP_token_pat = re.compile("\s*(?:(and|or|not|has|lacks)|(\"[ \.\w_\-\&\/]+\")|([\.\w_\-\&]+))")

def SP_tokenize(program):
    # \s* -> Matches any number of blanks [ \t\n\r\f\v].
    # (?:...) -> A non-capturing version of regular parentheses.
    # \w -> Matches [a-zA-Z0-9_]
    for operator, q_string, string in SP_token_pat.findall(program):
        if string:
            yield SP_literal_token(string)
        elif q_string:
            if q_string[0] == '"': q_string = q_string[1:]
            if q_string[-1] == '"': q_string = q_string[:-1]
            yield SP_literal_token(q_string)
        elif operator == "and":
            yield SP_operator_and_token()
        elif operator == "or":
            yield SP_operator_or_token()
        elif operator == "not":
            yield SP_operator_not_token()
        elif operator == "has":
            yield SP_operator_has_token()
        elif operator == "lacks":
            yield SP_operator_lacks_token()
        else:
            raise SyntaxError("Unknown operator: '{0}'".format(operator))
    yield SP_end_token()

# -------------------------------------------------------------------------------------------------
# String Parser (SP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
# -------------------------------------------------------------------------------------------------
def SP_expression(rbp = 0):
    global SP_token

    t = SP_token
    SP_token = SP_next()
    left = t.nud()
    while rbp < SP_token.lbp:
        t = SP_token
        SP_token = SP_next()
        left = t.led(left)
    return left

def SP_parse_exec(program, search_string):
    global SP_token, SP_next, SP_parser_search_string

    if debug_SP_parse_exec:
        log_debug('SP_parse_exec() Initialising program execution')
        log_debug('SP_parse_exec() Search string "{0}"'.format(search_string))
        log_debug('SP_parse_exec() Program       "{0}"'.format(program))
    SP_parser_search_string = search_string
    SP_next = SP_tokenize(program).next
    SP_token = SP_next()

    # --- Old function parse_exec() ---
    rbp = 0
    t = SP_token
    SP_token = SP_next()
    left = t.nud()
    while rbp < SP_token.lbp:
        t = SP_token
        SP_token = SP_next()
        left = t.led(left)
    if debug_SP_parse_exec:
        log_debug('SP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# -------------------------------------------------------------------------------------------------
# List of String Parser (LSP) engine. Grammar token objects.
# Parser inspired by http://effbot.org/zone/simple-top-down-parsing.htm
#
# LSP operators: and, or, not, '(', ')', literal.
# -------------------------------------------------------------------------------------------------
debug_LSP_parser = False
debug_LSP_parse_exec = False

class LSP_literal_token:
    def __init__(self, value):
        self.value = value
        self.id = "STRING"
    def nud(self):
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing LITERAL token value "{0}"'.format(self.value))
        ret = self.value
        if debug_LSP_parser: log_debug('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return '<LITERAL "{0}">'.format(self.value)

def LSP_advance(id = None):
    global LSP_token

    if id and LSP_token.id != id:
        raise SyntaxError("Expected {0}".format(id))
    LSP_token = LSP_next()

class LSP_operator_open_par_token:
    lbp = 0
    def __init__(self):
        self.id = "OP ("
    def nud(self):
        expr = LSP_expression()
        LSP_advance("OP )")
        return expr
    def __repr__(self):
        return "<OP (>"

class LSP_operator_close_par_token:
    lbp = 0
    def __init__(self):
        self.id = "OP )"
    def __repr__(self):
        return "<OP )>"

class LSP_operator_has_token:
    lbp = 50
    def __init__(self):
        self.id = "OP HAS"
    def nud(self):
        self.first = LSP_expression(50)
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing HAS token')
        ret = self.first.exec_token() in LSP_parser_search_list
        if debug_LSP_parser: log_debug('HAS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP has>"

class LSP_operator_lacks_token:
    lbp = 50
    def __init__(self):
        self.id = "OP LACKS"
    def nud(self):
        self.first = LSP_expression(50)
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing LACKS token')
        ret = self.first.exec_token() not in LSP_parser_search_list
        if debug_LSP_parser: log_debug('LACKS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP lacks>"

class LSP_operator_not_token:
    lbp = 50
    def __init__(self):
        self.id = "OP NOT"
    def nud(self):
        self.first = LSP_expression(50)
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_LSP_parser: log_debug('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP not>"

class LSP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_LSP_parser: log_debug('Executing AND token')
        self.first = left
        self.second = LSP_expression(10)
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_LSP_parser: log_debug('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP and>"

class LSP_operator_or_token:
    lbp = 10
    def __init__(self):
        self.id = "OP OR"
    def led(self, left):
        self.first = left
        self.second = LSP_expression(10)
        return self
    def exec_token(self):
        if debug_LSP_parser: log_debug('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_LSP_parser: log_debug('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP or>"

class LSP_end_token:
    lbp = 0
    def __init__(self):
        self.id = "END TOKEN"
    def __repr__(self):
        return "<END token>"

# -------------------------------------------------------------------------------------------------
# List of String Parser (LSP) Tokenizer
# See http://jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
# -------------------------------------------------------------------------------------------------
LSP_token_pat = re.compile("\s*(?:(and|or|not|has|lacks|\(|\))|(\"[ \.\w_\-\&\/]+\")|([\.\w_\-\&]+))")

def LSP_tokenize(program):
    # \s* -> Matches any number of blanks [ \t\n\r\f\v].
    # (?:...) -> A non-capturing version of regular parentheses.
    # \w -> Matches [a-zA-Z0-9_]
    for operator, q_string, string in LSP_token_pat.findall(program):
        if string:
            yield LSP_literal_token(string)
        elif q_string:
            if q_string[0] == '"': q_string = q_string[1:]
            if q_string[-1] == '"': q_string = q_string[:-1]
            yield LSP_literal_token(q_string)
        elif operator == "and":
            yield LSP_operator_and_token()
        elif operator == "or":
            yield LSP_operator_or_token()
        elif operator == "not":
            yield LSP_operator_not_token()
        elif operator == "has":
            yield LSP_operator_has_token()
        elif operator == "lacks":
            yield LSP_operator_lacks_token()
        elif operator == "(":
            yield LSP_operator_open_par_token()
        elif operator == ")":
            yield LSP_operator_close_par_token()
        else:
            raise SyntaxError("Unknown operator: '{0}'".format(operator))
    yield LSP_end_token()

# -------------------------------------------------------------------------------------------------
# List of String Parser (LSP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
# -------------------------------------------------------------------------------------------------
def LSP_expression(rbp = 0):
    global LSP_token

    t = LSP_token
    LSP_token = LSP_next()
    left = t.nud()
    while rbp < LSP_token.lbp:
        t = LSP_token
        LSP_token = LSP_next()
        left = t.led(left)
    return left

def LSP_parse_exec(program, search_list):
    global LSP_token, LSP_next, LSP_parser_search_list

    if debug_LSP_parse_exec:
        log_debug('LSP_parse_exec() Initialising program execution')
        log_debug('LSP_parse_exec() Search string "{0}"'.format(unicode(search_list)))
        log_debug('LSP_parse_exec() Program       "{0}"'.format(program))
    LSP_parser_search_list = search_list
    LSP_next = LSP_tokenize(program).next
    LSP_token = LSP_next()

    # --- Old function parse_exec() ---
    rbp = 0
    t = LSP_token
    LSP_token = LSP_next()
    left = t.nud()
    while rbp < LSP_token.lbp:
        t = LSP_token
        LSP_token = LSP_next()
        left = t.led(left)
    if debug_LSP_parse_exec:
        log_debug('LSP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# -------------------------------------------------------------------------------------------------
# Year Parser (YP) engine. Grammar token objects.
# Parser inspired by http://effbot.org/zone/simple-top-down-parsing.htm
#
# YP operators: ==, !=, >, <, >=, <=, and, or, not, '(', ')', literal.
# literal may be the special variable 'year' or a MAME number.
# -------------------------------------------------------------------------------------------------
debug_YP_parser = False
debug_YP_parse_exec = False

class YP_literal_token:
    def __init__(self, value):
        self.value = value
        self.id = "STRING"
    def nud(self):
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing LITERAL token value "{0}"'.format(self.value))
        if self.value == 'year':
            ret = YP_year
        else:
            ret = int(self.value)
        if debug_YP_parser: log_debug('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return '[LITERAL "{0}"]'.format(self.value)

def YP_advance(id = None):
    global YP_token

    if id and YP_token.id != id:
        raise SyntaxError("Expected {0}".format(id))
    YP_token = YP_next()

class YP_operator_open_par_token:
    lbp = 0
    def __init__(self):
        self.id = "OP ("
    def nud(self):
        expr = YP_expression()
        YP_advance("OP )")
        return expr
    def __repr__(self):
        return "[OP (]"

class YP_operator_close_par_token:
    lbp = 0
    def __init__(self):
        self.id = "OP )"
    def __repr__(self):
        return "[OP )]"

class YP_operator_not_token:
    lbp = 60
    def __init__(self):
        self.id = "OP NOT"
    def nud(self):
        self.first = YP_expression(50)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_YP_parser: log_debug('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP not]"

class YP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_YP_parser: log_debug('Executing AND token')
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_YP_parser: log_debug('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP and]"

class YP_operator_or_token:
    lbp = 10
    def __init__(self):
        self.id = "OP OR"
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_YP_parser: log_debug('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP or]"

class YP_operator_equal_token:
    lbp = 50
    def __init__(self):
        self.id = "OP =="
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing == token')
        ret = self.first.exec_token() == self.second.exec_token()
        if debug_YP_parser: log_debug('== token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP ==]"

class YP_operator_not_equal_token:
    lbp = 50
    def __init__(self):
        self.id = "OP !="
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing != token')
        ret = self.first.exec_token() != self.second.exec_token()
        if debug_YP_parser: log_debug('!= token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP !=]"

class YP_operator_great_than_token:
    lbp = 50
    def __init__(self):
        self.id = "OP >"
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing > token')
        ret = self.first.exec_token() > self.second.exec_token()
        if debug_YP_parser: log_debug('> token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP >]"

class YP_operator_less_than_token:
    lbp = 50
    def __init__(self):
        self.id = "OP <"
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing < token')
        ret = self.first.exec_token() < self.second.exec_token()
        if debug_YP_parser: log_debug('< token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP <]"

class YP_operator_great_or_equal_than_token:
    lbp = 50
    def __init__(self):
        self.id = "OP >="
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing >= token')
        ret = self.first.exec_token() >= self.second.exec_token()
        if debug_YP_parser: log_debug('>= token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP >=]"

class YP_operator_less_or_equal_than_token:
    lbp = 50
    def __init__(self):
        self.id = "OP <="
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing <= token')
        ret = self.first.exec_token() <= self.second.exec_token()
        if debug_YP_parser: log_debug('<= token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "[OP <=]"

class YP_end_token:
    lbp = 0
    def __init__(self):
        self.id = "END TOKEN"
    def __repr__(self):
        return "[END token]"

# -------------------------------------------------------------------------------------------------
# Year Parser Tokenizer
# See http://jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
# -------------------------------------------------------------------------------------------------
YP_token_pat = re.compile("\s*(?:(==|!=|>=|<=|>|<|and|or|not|\(|\))|([\w]+))")

def YP_tokenize(program):
    # \s* -> Matches any number of blanks [ \t\n\r\f\v].
    # (?:...) -> A non-capturing version of regular parentheses.
    # \w -> Matches [a-zA-Z0-9_]
    for operator, n_string in YP_token_pat.findall(program):
        if n_string:            yield YP_literal_token(n_string)
        elif operator == "==":  yield YP_operator_equal_token()
        elif operator == "!=":  yield YP_operator_not_equal_token()
        elif operator == ">":   yield YP_operator_great_than_token()
        elif operator == "<":   yield YP_operator_less_than_token()
        elif operator == ">=":  yield YP_operator_great_or_equal_than_token()
        elif operator == "<=":  yield YP_operator_less_or_equal_than_token()
        elif operator == "and": yield YP_operator_and_token()
        elif operator == "or":  yield YP_operator_or_token()
        elif operator == "not": yield YP_operator_not_token()
        elif operator == "(":   yield YP_operator_open_par_token()
        elif operator == ")":   yield YP_operator_close_par_token()
        else:                   raise SyntaxError("Unknown operator: '{0}'".format(operator))
    yield YP_end_token()

# -------------------------------------------------------------------------------------------------
# Year Parser (YP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
# -------------------------------------------------------------------------------------------------
def YP_expression(rbp = 0):
    global YP_token

    t = YP_token
    YP_token = YP_next()
    left = t.nud()
    while rbp < YP_token.lbp:
        t = YP_token
        YP_token = YP_next()
        left = t.led(left)
    return left

def YP_parse_exec(program, year_str):
    global YP_token, YP_next, YP_year

    # --- Transform year_str to an integer. year_str may be ill formed ---
    if re.findall(r'^[0-9]{4}$', year_str):
        year = int(year_str)
    elif re.findall(r'^[0-9]{4}\?$', year_str):
        year = int(year_str[0:4])
    else:
        year = 0

    if debug_YP_parse_exec:
        log_debug('YP_parse_exec() Initialising program execution')
        log_debug('YP_parse_exec() year     "{0}"'.format(year))
        log_debug('YP_parse_exec() Program  "{0}"'.format(program))
    YP_year = year
    YP_next = YP_tokenize(program).next
    YP_token = YP_next()

    # --- Old function parse_exec() ---
    rbp = 0
    t = YP_token
    YP_token = YP_next()
    left = t.nud()
    while rbp < YP_token.lbp:
        t = YP_token
        YP_token = YP_next()
        left = t.led(left)
    if debug_YP_parse_exec:
        log_debug('YP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# -------------------------------------------------------------------------------------------------
# MAME machine filters
# -------------------------------------------------------------------------------------------------
#
# Default filter removes device machines.
#
def filter_mame_Default(mame_xml_dic):
    log_debug('filter_mame_Default() Starting ...')
    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        if mame_xml_dic[m_name]['isDevice']:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Default() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Options_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Options_tag() Starting ...')
    options_list = f_definition['options']

    if not options_list:
        log_debug('filter_mame_Options_tag() Option list is empty.')
        return mame_xml_dic
    log_debug('Option list "{0}"'.format(options_list))

    # --- Compute bool variables ---
    # This must match OPTIONS_KEYWORK_LIST
    NoClones_bool     = True if 'NoClones' in options_list else False
    NoCoin_bool       = True if 'NoCoin' in options_list else False
    NoCoinLess_bool   = True if 'NoCoinLess' in options_list else False
    NoROMs_bool       = True if 'NoROMs' in options_list else False
    NoCHDs_bool       = True if 'NoCHDs' in options_list else False
    NoSamples_bool    = True if 'NoSamples' in options_list else False
    NoMature_bool     = True if 'NoMature' in options_list else False
    NoBIOS_bool       = True if 'NoBIOS' in options_list else False
    NoMechanical_bool = True if 'NoMechanical' in options_list else False
    NoImperfect_bool  = True if 'NoImperfect' in options_list else False
    NoNonWorking_bool = True if 'NoNonworking' in options_list else False
    NoVertical_bool   = True if 'NoVertical' in options_list else False
    NoHorizontal_bool = True if 'NoHorizontal' in options_list else False

    log_debug('NoClones_bool     {0}'.format(NoClones_bool))
    log_debug('NoCoin_bool       {0}'.format(NoCoin_bool))
    log_debug('NoCoinLess_bool   {0}'.format(NoCoinLess_bool))
    log_debug('NoROMs_bool       {0}'.format(NoROMs_bool))
    log_debug('NoCHDs_bool       {0}'.format(NoCHDs_bool))
    log_debug('NoSamples_bool    {0}'.format(NoSamples_bool))
    log_debug('NoMature_bool     {0}'.format(NoMature_bool))
    log_debug('NoBIOS_bool       {0}'.format(NoBIOS_bool))
    log_debug('NoMechanical_bool {0}'.format(NoMechanical_bool))
    log_debug('NoImperfect_bool  {0}'.format(NoImperfect_bool))
    log_debug('NoNonWorking_bool {0}'.format(NoNonWorking_bool))
    log_debug('NoVertical_bool   {0}'.format(NoVertical_bool))
    log_debug('NoHorizontal_bool {0}'.format(NoHorizontal_bool))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        # >> Remove Clone machines
        if NoClones_bool and mame_xml_dic[m_name]['isClone']:
            filtered_out_games += 1
            continue
        # >> Remove Coin machines
        if NoCoin_bool and mame_xml_dic[m_name]['coins'] > 0:
            filtered_out_games += 1
            continue
        # >> Remove CoinLess machines
        if NoCoinLess_bool and mame_xml_dic[m_name]['coins'] == 0:
            filtered_out_games += 1
            continue
        # >> Remove ROM machines
        if NoROMs_bool and mame_xml_dic[m_name]['hasROMs']:
            filtered_out_games += 1
            continue
        # >> Remove CHD machines
        if NoCHDs_bool and mame_xml_dic[m_name]['hasCHDs']:
            filtered_out_games += 1
            continue
        # >> Remove Samples machines
        if NoSamples_bool and mame_xml_dic[m_name]['hasSamples']:
            filtered_out_games += 1
            continue
        # >> Remove Mature machines
        if NoMature_bool and mame_xml_dic[m_name]['isMature']:
            filtered_out_games += 1
            continue
        # >> Remove BIOS machines
        if NoBIOS_bool and mame_xml_dic[m_name]['isBIOS']:
            filtered_out_games += 1
            continue
        # >> Remove Mechanical machines
        if NoMechanical_bool and mame_xml_dic[m_name]['isMechanical']:
            filtered_out_games += 1
            continue
        # >> Remove Imperfect machines
        if NoImperfect_bool and mame_xml_dic[m_name]['isImperfect']:
            filtered_out_games += 1
            continue
        # >> Remove NonWorking machines
        if NoNonWorking_bool and mame_xml_dic[m_name]['isNonWorking']:
            filtered_out_games += 1
            continue
        # >> Remove Vertical machines
        if NoVertical_bool and mame_xml_dic[m_name]['isVertical']:
            filtered_out_games += 1
            continue
        # >> Remove Horizontal machines
        if NoHorizontal_bool and mame_xml_dic[m_name]['isHorizontal']:
            filtered_out_games += 1
            continue
        # >> If machine was not removed then add it
        machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug(
        'filter_mame_Options_tag() Initial {0} | '.format(initial_num_games) + \
        'Removed {0} | '.format(filtered_out_games) + \
        'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Driver_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Driver_tag() Starting ...')
    filter_expression = f_definition['driver']

    if not filter_expression:
        log_debug('filter_mame_Driver_tag() User wants all drivers')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        search_list = [ mame_xml_dic[m_name]['driver'] ]
        bool_result = LSP_parse_exec(filter_expression, search_list)
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Driver_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Manufacturer_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Manufacturer_tag() Starting ...')
    filter_expression = f_definition['manufacturer']

    if not filter_expression:
        log_debug('filter_mame_Manufacturer_tag() User wants all manufacturers')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        bool_result = SP_parse_exec(filter_expression, mame_xml_dic[m_name]['manufacturer'])
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Manufacturer_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Genre_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Genre_tag() Starting ...')
    filter_expression = f_definition['genre']

    if not filter_expression:
        log_debug('filter_mame_Genre_tag() User wants all genres')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        search_list = [ mame_xml_dic[m_name]['genre'] ]
        bool_result = LSP_parse_exec(filter_expression, search_list)
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Genre_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Controls_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Controls_tag() Starting ...')
    filter_expression = f_definition['controls']

    if not filter_expression:
        log_debug('filter_mame_Controls_tag() User wants all genres')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        bool_result = LSP_parse_exec(filter_expression, mame_xml_dic[m_name]['control_list'])
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Controls_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_PluggableDevices_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_PluggableDevices_tag() Starting ...')
    filter_expression = f_definition['pluggabledevices']

    if not filter_expression:
        log_debug('filter_mame_PluggableDevices_tag() User wants all genres')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        # --- Update search list variable and call parser to evaluate expression ---
        bool_result = LSP_parse_exec(filter_expression, mame_xml_dic[m_name]['pluggable_device_list'])
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug(
        'filter_mame_PluggableDevices_tag() Initial {0} | '.format(initial_num_games) + \
        'Removed {0} | '.format(filtered_out_games) + \
        'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Year_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Year_tag() Starting ...')
    filter_expression = f_definition['year']

    if not filter_expression:
        log_debug('filter_mame_Year_tag() User wants all genres')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        # --- Update search int variable and call parser to evaluate expression ---
        bool_result = YP_parse_exec(filter_expression, mame_xml_dic[m_name]['year'])
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('filter_mame_Year_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Include_tag(mame_xml_dic, f_definition, machines_dic):
    # log_debug('filter_mame_Include_tag() Starting ...')
    log_debug('filter_mame_Include_tag() Include machines {0}'.format(unicode(f_definition['include'])))
    added_machines = 0
    machines_filtered_dic = mame_xml_dic.copy()
    # If no machines to include then skip processing
    if not f_definition['include']:
        log_debug('filter_mame_Include_tag() No machines to include. Exiting.')
        return machines_filtered_dic
    # First traverse all MAME machines, then traverse list of strings to include.
    for m_name in sorted(machines_dic):
        for f_name in f_definition['include']:
            if f_name == m_name:
                log_debug('filter_mame_Include_tag() Matched machine {0}'.format(f_name))
                if f_name in machines_filtered_dic:
                    log_debug('filter_mame_Include_tag() Machine {0} already in filtered list'.format(f_name))
                else:
                    log_debug('filter_mame_Include_tag() Adding machine {0}'.format(f_name))
                    machines_filtered_dic[m_name] = machines_dic[m_name]
                    added_machines += 1
    log_debug('filter_mame_Include_tag() Initial {0} | '.format(len(mame_xml_dic)) + \
              'Added {0} | '.format(added_machines) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Exclude_tag(mame_xml_dic, f_definition):
    # log_debug('filter_mame_Exclude_tag() Starting ...')
    log_debug('filter_mame_Exclude_tag() Exclude machines {0}'.format(unicode(f_definition['exclude'])))
    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = mame_xml_dic.copy()
    # If no machines to exclude then skip processing
    if not f_definition['exclude']:
        log_debug('filter_mame_Exclude_tag() No machines to exclude. Exiting.')
        return machines_filtered_dic
    # First traverse current set of machines, then traverse list of strings to include.
    for m_name in sorted(mame_xml_dic):
        for f_name in f_definition['exclude']:
            if f_name == m_name:
                log_debug('filter_mame_Exclude_tag() Matched machine {0}'.format(f_name))
                log_debug('filter_mame_Exclude_tag() Deleting machine {0}'.format(f_name))
                del machines_filtered_dic[f_name]
                filtered_out_games += 1
    log_debug('filter_mame_Exclude_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def filter_mame_Change_tag(mame_xml_dic, f_definition, machines_dic):
    # log_debug('filter_mame_Change_tag() Starting ...')
    log_debug('filter_mame_Change_tag() Change machines {0}'.format(unicode(f_definition['change'])))
    initial_num_games = len(mame_xml_dic)
    changed_machines = 0
    machines_filtered_dic = mame_xml_dic.copy()
    # If no machines to change then skip processing
    if not f_definition['change']:
        log_debug('filter_mame_Change_tag() No machines to swap. Exiting.')
        return machines_filtered_dic
    # First traverse current set of machines, then traverse list of strings to include.
    for m_name in sorted(mame_xml_dic):
        for (f_name, new_name) in f_definition['change']:
            if f_name == m_name:
                log_debug('filter_mame_Change_tag() Matched machine {0}'.format(f_name))
                if new_name in machines_dic:
                    log_debug('filter_mame_Change_tag() Changing machine {0} with {1}'.format(f_name, new_name))
                    del machines_filtered_dic[f_name]
                    machines_filtered_dic[new_name] = machines_dic[new_name]
                    changed_machines += 1
                else:
                    log_warning('filter_mame_Change_tag() New machine {0} not found on MAME machines.'.format(new_name))
    log_debug('filter_mame_Change_tag() Initial {0} | '.format(initial_num_games) + \
              'Changed {0} | '.format(changed_machines) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

# -------------------------------------------------------------------------------------------------
# Build MAME custom filters
# -------------------------------------------------------------------------------------------------
#
# Returns a list of dictionaries, each dictionary has the filter definition.
#
def filter_parse_XML(fname_str):
    __debug_xml_parser = False

    # If XML has errors (invalid characters, etc.) this will rais exception 'err'
    XML_FN = FileName(fname_str)
    if not XML_FN.exists():
        kodi_dialog_OK('Custom filter XML file not found.')
        return
    log_debug('filter_parse_XML() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
    log_debug('filter_parse_XML() Reading XML  P "{0}"'.format(XML_FN.getPath()))
    try:
        xml_tree = ET.parse(XML_FN.getPath())
    except IOError as ex:
        log_error('(Exception) {0}'.format(ex))
        log_error('(Exception) Syntax error in the XML file definition')
        raise Addon_Error('(Exception) ET.parse(XML_FN.getPath()) failed.')
    xml_root = xml_tree.getroot()
    define_dic = {}
    filters_list = []
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {0}'.format(root_element.tag))

        if root_element.tag == 'DEFINE':
            name_str = root_element.attrib['name']
            define_str = root_element.text if root_element.text else ''
            log_debug('DEFINE "{0}" := "{1}"'.format(name_str, define_str))
            define_dic[name_str] = define_str
        elif root_element.tag == 'MAMEFilter':
            this_filter_dic = {
                'name'             : '',
                'plot'             : '',
                'options'          : [], # List of strings
                'driver'           : '',
                'manufacturer'     : '',
                'genre'            : '',
                'controls'         : '',
                'pluggabledevices' : '',
                'year'             : '',
                'include'          : [], # List of strings
                'exclude'          : [], # List of strings
                'change'           : [], # List of tuples (change_orig string, change_dest string)
            }
            for filter_element in root_element:
                text_t = filter_element.text if filter_element.text else ''
                if filter_element.tag == 'Name':
                    this_filter_dic['name'] = text_t
                elif filter_element.tag == 'Plot':
                    this_filter_dic['plot'] = text_t
                elif filter_element.tag == 'Options':
                    t_list = _get_comma_separated_list(text_t)
                    if t_list:
                        this_filter_dic['options'].extend(t_list)
                elif filter_element.tag == 'Driver':
                    this_filter_dic['driver'] = text_t
                elif filter_element.tag == 'Manufacturer':
                    this_filter_dic['manufacturer'] = text_t
                elif filter_element.tag == 'Genre':
                    this_filter_dic['genre'] = text_t
                elif filter_element.tag == 'Controls':
                    this_filter_dic['controls'] = text_t
                elif filter_element.tag == 'PluggableDevices':
                    this_filter_dic['pluggabledevices'] = text_t
                elif filter_element.tag == 'Year':
                    this_filter_dic['year'] = text_t
                elif filter_element.tag == 'Include':
                    t_list = _get_comma_separated_list(text_t)
                    if t_list: this_filter_dic['include'].extend(t_list)
                elif filter_element.tag == 'Exclude':
                    t_list = _get_comma_separated_list(text_t)
                    if t_list: this_filter_dic['exclude'].extend(t_list)
                elif filter_element.tag == 'Change':
                    tuple_t = _get_change_tuple(text_t)
                    if tuple_t: this_filter_dic['change'].append(tuple_t)
                else:
                    m = '(Exception) Unrecognised tag <{0}>'.format(filter_element.tag)
                    log_debug(m)
                    raise Addon_Error(m)
            log_debug('Adding filter "{0}"'.format(this_filter_dic['name']))
            filters_list.append(this_filter_dic)

    # >> Resolve DEFINE tags (substitute by the defined value)
    for f_definition in filters_list:
        for initial_str, final_str in define_dic.iteritems():
            f_definition['driver']           = f_definition['driver'].replace(initial_str, final_str)
            f_definition['manufacturer']     = f_definition['manufacturer'].replace(initial_str, final_str)
            f_definition['genre']            = f_definition['genre'].replace(initial_str, final_str)
            f_definition['controls']         = f_definition['controls'].replace(initial_str, final_str)
            f_definition['pluggabledevices'] = f_definition['pluggabledevices'].replace(initial_str, final_str)
            # Replace strings in list of strings.
            for i, s_t in enumerate(f_definition['include']):
                f_definition['include'][i] = s_t.replace(initial_str, final_str)
            for i, s_t in enumerate(f_definition['exclude']):
                f_definition['exclude'][i] = s_t.replace(initial_str, final_str)
            # for i, s_t in enumerate(f_definition['change']):
            #     f_definition['change'][i] = s_t.replace(initial_str, final_str)

    return filters_list

#
# Returns a dictionary of dictionaries, indexed by the machine name.
# This includes all MAME machines, including parents and clones.
#
def filter_get_filter_DB(PATHS, machine_main_dic, machine_render_dic, assets_dic,
    machine_archives_dic):
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher', 'Building filter database ...')
    total_items = len(machine_main_dic)
    item_count = 0
    main_filter_dic = {}
    # Sets are used to check the integrity of the filters defined in the XML.
    drivers_set = set()
    genres_set = set()
    controls_set = set()
    pdevices_set = set()
    # Histograms
    # The driver histogram is too big and unuseful.
    genres_drivers_dic = {}
    controls_drivers_dic = {}
    pdevices_drivers_dic = {}
    for m_name in machine_main_dic:
        pDialog.update(int((item_count*100) / total_items))
        if 'att_coins' in machine_main_dic[m_name]['input']:
            coins = machine_main_dic[m_name]['input']['att_coins']
        else:
            coins = 0
        if m_name in machine_archives_dic:
            hasROMs = True if machine_archives_dic[m_name]['ROMs'] else False
        else:
            hasROMs = False
        if m_name in machine_archives_dic:
            hasCHDs = True if machine_archives_dic[m_name]['CHDs'] else False
        else:
            hasCHDs = False
        if m_name in machine_archives_dic:
            hasSamples = True if machine_archives_dic[m_name]['Samples'] else False
        else:
            hasSamples = False
        # If the machine has no displays then both isVertical and isHorizontal are False.
        isVertical, isHorizontal = False, False
        for drotate in machine_main_dic[m_name]['display_rotate']:
            if drotate == '0' or drotate == '180':
                isHorizontal = True
            elif drotate == '90' or drotate == '270':
                isVertical = True

        # >> Fix controls to match "Machines by Controls (Compact)" filter
        if machine_main_dic[m_name]['input']:
            raw_control_list = [
                ctrl_dic['type'] for ctrl_dic in machine_main_dic[m_name]['input']['control_list']
            ]
        else:
            raw_control_list = []
        pretty_control_type_list = misc_improve_mame_control_type_list(raw_control_list)
        control_list = misc_compress_mame_item_list_compact(pretty_control_type_list)
        if not control_list: control_list = [ 'None' ]

        # >> Fix this to match "Machines by Pluggable Devices (Compact)" filter
        raw_device_list = [ device['att_type'] for device in machine_main_dic[m_name]['devices'] ]
        pretty_device_list = misc_improve_mame_device_list(raw_device_list)
        pluggable_device_list = misc_compress_mame_item_list_compact(pretty_device_list)
        if not pluggable_device_list: pluggable_device_list = [ 'None' ]

        # --- Build filtering dictionary ---
        main_filter_dic[m_name] = {
            # --- Default filters ---
            'isDevice' : machine_render_dic[m_name]['isDevice'],
            # --- <Option> filters ---
            'isClone' : True if machine_render_dic[m_name]['cloneof'] else False,
            'coins' : coins,
            'hasROMs' : hasROMs,
            'hasCHDs' : hasCHDs,
            'hasSamples' : hasSamples,
            'isMature' : machine_render_dic[m_name]['isMature'],
            'isBIOS' : machine_render_dic[m_name]['isBIOS'],
            'isMechanical' : machine_main_dic[m_name]['isMechanical'],
            'isImperfect' : True if machine_render_dic[m_name]['driver_status'] == 'imperfect' else False,
            'isNonWorking' : True if machine_render_dic[m_name]['driver_status'] == 'preliminary' else False,
            'isHorizontal' : isHorizontal,
            'isVertical' : isVertical,
            # --- Other filters ---
            'driver' : machine_main_dic[m_name]['sourcefile'],
            'manufacturer' : machine_render_dic[m_name]['manufacturer'],
            'genre' : machine_render_dic[m_name]['genre'],
            'control_list' : control_list,
            'pluggable_device_list' : pluggable_device_list,
            'year' : machine_render_dic[m_name]['year'],
        }
        item_count += 1

        # --- Make sets of drivers, genres, controls, and pluggable devices ---
        mdict = main_filter_dic[m_name]
        drivers_set.add(mdict['driver'])
        genres_set.add(mdict['genre'])
        for control in mdict['control_list']: controls_set.add(control)
        for device in mdict['pluggable_device_list']: pdevices_set.add(device)
        # --- Histograms ---
        if mdict['genre'] in genres_drivers_dic:
            genres_drivers_dic[mdict['genre']] += 1
        else:
            genres_drivers_dic[mdict['genre']] = 1
        for control in mdict['control_list']:
            if control in controls_drivers_dic:
                controls_drivers_dic[control] += 1
            else:
                controls_drivers_dic[control] = 1
        for device in mdict['pluggable_device_list']:
            if device in pdevices_drivers_dic:
                pdevices_drivers_dic[device] += 1
            else:
                pdevices_drivers_dic[device] = 1
    pDialog.update(100)
    pDialog.close()

    # --- Write statistics report ---
    log_info('Writing report "{0}"'.format(PATHS.REPORT_CF_HISTOGRAMS_PATH.getPath()))
    with open(PATHS.REPORT_CF_HISTOGRAMS_PATH.getPath(), 'w') as file:
        rslist = [
            '*** Advanced MAME Launcher MAME histogram report ***',
            '',
        ]

        table_str = [
            ['right', 'right'],
            ['Genre', 'Number of machines'],
        ]
        for dname, dnumber in sorted(genres_drivers_dic.items(), key = lambda x: x[1], reverse = True):
            table_str.append(['{0}'.format(dname), '{0}'.format(dnumber)])
        rslist.extend(text_render_table_str(table_str))
        rslist.append('')

        table_str = [
            ['right', 'right'],
            ['Control', 'Number of machines'],
        ]
        for dname, dnumber in sorted(controls_drivers_dic.items(), key = lambda x: x[1], reverse = True):
            table_str.append(['{0}'.format(dname), '{0}'.format(dnumber)])
        rslist.extend(text_render_table_str(table_str))
        rslist.append('')

        table_str = [
            ['right', 'right'],
            ['Device', 'Number of machines'],
        ]
        for dname, dnumber in sorted(pdevices_drivers_dic.items(), key = lambda x: x[1], reverse = True):
            table_str.append(['{0}'.format(dname), '{0}'.format(dnumber)])
        rslist.extend(text_render_table_str(table_str))
        rslist.append('')

        file.write('\n'.join(rslist).encode('utf-8'))

    sets_dic = {
        'drivers_set' : drivers_set,
        'genres_set' : genres_set,
        'controls_set' : controls_set,
        'pdevices_set' : pdevices_set,
    }

    return (main_filter_dic, sets_dic)

#
# Returns a tuple (filter_list, options_dic).
#
def filter_custom_filters_load_XML(PATHS, settings, control_dic, main_filter_dic, sets_dic):
    filter_list = []
    options_dic = {
        # No errors by default until an error is found.
        'XML_errors' : False,
    }

    # --- Open custom filter XML and parse it ---
    cf_XML_path_str = settings['filter_XML']
    log_debug('cf_XML_path_str = "{0}"'.format(cf_XML_path_str))
    if not cf_XML_path_str:
        log_debug('Using default XML custom filter.')
        XML_FN = PATHS.CUSTOM_FILTER_PATH
    else:
        log_debug('Using user-defined in addon settings XML custom filter.')
        XML_FN = FileName(cf_XML_path_str)
    log_debug('filter_custom_filters_load_XML() Reading XML OP "{0}"'.format(XML_FN.getOriginalPath()))
    log_debug('filter_custom_filters_load_XML() Reading XML  P "{0}"'.format(XML_FN.getPath()))
    try:
        filter_list = filter_parse_XML(XML_FN.getPath())
    except Addon_Error as ex:
        kodi_notify_warn('{0}'.format(ex))
        return (filter_list, options_dic)
    else:
        log_debug('Filter XML read succesfully.')

    # --- Check XML for errors and write report ---
    # Filters sorted as defined in the XML.
    OPTIONS_KEYWORK_SET = set(OPTIONS_KEYWORK_LIST)
    r_full = []
    for filter_dic in filter_list:
        c_list = []

        # Check 1) Keywords in <Options> are correct.
        for option_keyword in filter_dic['options']:
            if option_keyword not in OPTIONS_KEYWORK_SET:
                c_list.append('<Options> keywork "{0}" unrecognised.'.format(option_keyword))

        # Check 2) Drivers in <Driver> exist.
        # <Driver> uses the LSP parser.
        keyword_list = []
        for token in SP_tokenize(filter_dic['driver']):
            if isinstance(token, SP_literal_token):
                keyword_list.append(token.value)
        for dname in keyword_list:
            if dname not in sets_dic['drivers_set']:
                c_list.append('<Driver> "{0}" not found.'.format(dname))

        # Check 3) Genres in <Genre> exist.
        # <Genre> uses the LSP parser.
        keyword_list = []
        for token in SP_tokenize(filter_dic['genre']):
            if isinstance(token, SP_literal_token):
                keyword_list.append(token.value)
        for dname in keyword_list:
            if dname not in sets_dic['genres_set']:
                c_list.append('<Genre> "{0}" not found.'.format(dname))

        # Check 4) Controls in <Controls> exist.
        # <Controls> uses the LSP parser.
        keyword_list = []
        for token in SP_tokenize(filter_dic['controls']):
            if isinstance(token, SP_literal_token):
                keyword_list.append(token.value)
        for dname in keyword_list:
            if dname not in sets_dic['controls_set']:
                c_list.append('<Controls> "{0}" not found.'.format(dname))

        # Check 5) Plugabble devices in <PluggableDevices> exist.
        # <PluggableDevices> uses the LSP parser.
        keyword_list = []
        for token in SP_tokenize(filter_dic['pluggabledevices']):
            if isinstance(token, SP_literal_token):
                keyword_list.append(token.value)
        for dname in keyword_list:
            if dname not in sets_dic['pdevices_set']:
                c_list.append('<PluggableDevices> "{0}" not found.'.format(dname))

        # Check 6) Machines in <Include> exist.
        for m_name in filter_dic['include']:
            if m_name not in main_filter_dic:
                c_list.append('<Include> machine "{0}" not found.'.format(m_name))

        # Check 7) Machines in <Exclude> exist.
        for m_name in filter_dic['exclude']:
            if m_name not in main_filter_dic:
                c_list.append('<Exclude> machine "{0}" not found.'.format(m_name))

        # Check 8) Machines in <Change> exist.
        for change_tuple in filter_dic['change']:
            if change_tuple[0] not in main_filter_dic:
                c_list.append('<Change> machine "{0}" not found.'.format(change_tuple[0]))
            if change_tuple[1] not in main_filter_dic:
                c_list.append('<Change> machine "{0}" not found.'.format(change_tuple[1]))

        # Build report
        r_full.append('Filter "{0}"'.format(filter_dic['name']))
        if not c_list:
            r_full.append('No issues found.')
        else:
            r_full.extend(c_list)
            # Error found, set the flag.
            options_dic['XML_errors'] = True
        r_full.append('')

    # --- Write MAME scanner reports ---
    log_info('Writing report "{0}"'.format(PATHS.REPORT_CF_XML_SYNTAX_PATH.getPath()))
    with open(PATHS.REPORT_CF_XML_SYNTAX_PATH.getPath(), 'w') as file:
        report_slist = [
            '*** Advanced MAME Launcher MAME custom filter XML syntax report ***',
            'There are {0} custom filters defined.'.format(len(filter_list)),
            'XML "{0}"'.format(XML_FN.getOriginalPath()),
            '',
        ]
        report_slist.extend(r_full)
        file.write('\n'.join(report_slist).encode('utf-8'))

    return (filter_list, options_dic)

#
# filter_index_dic = {
#     'name' : {
#         'display_name' : str,
#         'num_machines' : int,
#         'num_parents' : int,
#         'order' : int,
#         'plot' : str,
#         'rom_DB_noext' : str,
#     }
# }
# AML_DATA_DIR/filters/'rom_DB_noext'_render.json -> machine_render = {}
# AML_DATA_DIR/filters/'rom_DB_noext'_assets.json -> asset_dic = {}
#
def filter_build_custom_filters(PATHS, settings, control_dic,
    filter_list, main_filter_dic, machines_dic, render_dic, assets_dic):
    # --- Clean 'filters' directory JSON files ---
    log_info('filter_build_custom_filters() Cleaning dir "{0}"'.format(PATHS.FILTERS_DB_DIR.getPath()))
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced MAME Launcher', 'Cleaning old filter JSON files ...')
    pDialog.update(0)
    file_list = os.listdir(PATHS.FILTERS_DB_DIR.getPath())
    num_files = len(file_list)
    if num_files > 1:
        log_info('Found {0} files'.format(num_files))
        processed_items = 0
        for file in file_list:
            pDialog.update((processed_items*100) // num_files)
            if file.endswith('.json'):
                full_path = os.path.join(PATHS.FILTERS_DB_DIR.getPath(), file)
                # log_debug('UNLINK "{0}"'.format(full_path))
                os.unlink(full_path)
            processed_items += 1
    pDialog.update(100)
    pDialog.close()

    # --- Report header ---
    r_full = []
    r_full.append('Number of machines {0}'.format(len(main_filter_dic)))
    r_full.append('Number of filters {0}'.format(len(filter_list)))
    r_full.append('')

    # --- Traverse list of filters, build filter index and compute filter list ---
    pdialog_line1 = 'Building custom MAME filters'
    pDialog.create('Advanced MAME Launcher', pdialog_line1)
    Filters_index_dic = {}
    total_items = len(filter_list)
    processed_items = 0
    for f_definition in filter_list:
        # --- Initialise ---
        f_name = f_definition['name']
        log_debug('filter_build_custom_filters() Processing filter "{0}"'.format(f_name))
        # log_debug('f_definition = {0}'.format(unicode(f_definition)))

        # --- Initial progress ---
        pDialog.update((processed_items*100) // total_items, pdialog_line1, 'Filter "{0}" ...'.format(f_name))

        # --- Do filtering ---
        filtered_machine_dic = filter_mame_Default(main_filter_dic)
        filtered_machine_dic = filter_mame_Options_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Driver_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Manufacturer_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Genre_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Controls_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_PluggableDevices_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Year_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Include_tag(filtered_machine_dic, f_definition, machines_dic)
        filtered_machine_dic = filter_mame_Exclude_tag(filtered_machine_dic, f_definition)
        filtered_machine_dic = filter_mame_Change_tag(filtered_machine_dic, f_definition, machines_dic)

        # --- Make indexed catalog ---
        filtered_render_dic = {}
        filtered_assets_dic = {}
        for m_name in filtered_machine_dic:
            filtered_render_dic[m_name] = render_dic[m_name]
            filtered_assets_dic[m_name] = assets_dic[m_name]
        rom_DB_noext = hashlib.md5(f_name).hexdigest()
        this_filter_idx_dic = {
            'display_name' : f_definition['name'],
            'num_machines' : len(filtered_render_dic),
            'order'        : processed_items,
            'plot'         : f_definition['plot'],
            'rom_DB_noext' : rom_DB_noext
        }
        Filters_index_dic[f_name] = this_filter_idx_dic

        # --- Save filter database ---
        writing_ticks_start = time.time()
        output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_render.json')
        fs_write_JSON_file(output_FN.getPath(), filtered_render_dic, verbose = False)
        output_FN = PATHS.FILTERS_DB_DIR.pjoin(rom_DB_noext + '_assets.json')
        fs_write_JSON_file(output_FN.getPath(), filtered_assets_dic, verbose = False)
        writing_ticks_end = time.time()
        writing_time = writing_ticks_end - writing_ticks_start
        log_debug('JSON writing time {0:.4f} s'.format(writing_time))

        # --- Final progress ---
        processed_items += 1

        # --- Report ---
        r_full.append('Filter "{0}"'.format(f_name))
        r_full.append('{0} machines'.format(len(filtered_machine_dic)))
        r_full.append('')

    # --- Save custom filter index ---
    fs_write_JSON_file(PATHS.FILTERS_INDEX_PATH.getPath(), Filters_index_dic)
    pDialog.update(100, pdialog_line1, ' ')
    pDialog.close()

    # --- Update timestamp ---
    change_control_dic(control_dic, 't_Custom_Filter_build', time.time())
    fs_write_JSON_file(PATHS.MAIN_CONTROL_PATH.getPath(), control_dic)

    # --- Write MAME scanner reports ---
    log_info('Writing report "{0}"'.format(PATHS.REPORT_CF_DB_BUILD_PATH.getPath()))
    with open(PATHS.REPORT_CF_DB_BUILD_PATH.getPath(), 'w') as file:
        report_slist = [
            '*** Advanced MAME Launcher MAME custom filter XML syntax report ***',
            'File "{0}"'.format(PATHS.REPORT_CF_DB_BUILD_PATH.getPath()),
            '',
        ]
        report_slist.extend(r_full)
        file.write('\n'.join(report_slist).encode('utf-8'))
