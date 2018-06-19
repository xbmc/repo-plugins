# -*- coding: utf-8 -*-
#
# Advanced MAME Launcher MAME filter engine.
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
# Division operator: https://www.python.org/dev/peps/pep-0238/
from __future__ import unicode_literals
from __future__ import division

import xml.etree.ElementTree as ET

# --- Modules/packages in this plugin ---
from constants import *
from utils import *
from utils_kodi import *
from mame import *

# -------------------------------------------------------------------------------------------------
# Parse filter XML definition
# -------------------------------------------------------------------------------------------------
def strip_str_list(t_list):
    for i, s_t in enumerate(t_list): t_list[i] = s_t.strip()

    return t_list

def _get_comma_separated_list(text_t):
    if not text_t:
        return []
    else:
        return strip_str_list(text_t.split(','))

#
# Parse a string 'XXXXXX with YYYYYY'
#
def _get_change_tuple(text_t):
    if not text_t:
        return ''
    tuple_list = re.findall(r'(\w+) with (\w+)', text_t)
    if tuple_list:
        return tuple_list
    else:
        log_error('_get_change_tuple() text_t = "{0}"'.format(text_t))
        m = '(Exception) Cannot parse <Change> "{0}"'.format(text_t)
        log_error(m)
        raise Addon_Error(m)

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
                'name'         : '',
                'plot'         : '',
                'options'      : [], # List of strings
                'driver'       : '',
                'manufacturer' : '',
                'genre'        : '',
                'controls'     : '',
                'devices'      : '',
                'year'         : '',
                'include'      : [], # List of strings
                'exclude'      : [], # List of strings
                'change'       : [], # List of tuples (change_orig, change_dest)
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
                elif filter_element.tag == 'Devices':
                    this_filter_dic['devices'] = text_t
                elif filter_element.tag == 'Year':
                    this_filter_dic['year'] = text_t
                elif filter_element.tag == 'Include':
                    t_list = _get_comma_separated_list(text_t)
                    if t_list:
                        this_filter_dic['include'].extend(t_list)
                elif filter_element.tag == 'Exclude':
                    t_list = _get_comma_separated_list(text_t)
                    if t_list:
                        this_filter_dic['exclude'].extend(t_list)
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
            f_definition['driver']       = f_definition['driver'].replace(initial_str, final_str)
            f_definition['manufacturer'] = f_definition['manufacturer'].replace(initial_str, final_str)
            f_definition['genre']        = f_definition['genre'].replace(initial_str, final_str)
            f_definition['controls']     = f_definition['controls'].replace(initial_str, final_str)
            f_definition['devices']      = f_definition['devices'].replace(initial_str, final_str)
            # f_definition['include']      = f_definition['include'].replace(initial_str, final_str)
            # f_definition['exclude']      = f_definition['exclude'].replace(initial_str, final_str)
            # f_definition['change']       = f_definition['change'].replace(initial_str, final_str)
    return filters_list

#
# Returns a dictionary of dictionaries.
#
def filter_get_filter_DB(machine_main_dic, machine_render_dic,
                         assets_dic, main_pclone_dic, machine_archives_dic, pDialog):
    pDialog.create('Advanced MAME Launcher', 'Building filter database ...')
    total_items = len(main_pclone_dic)
    item_count = 0
    main_filter_dic = {}
    for m_name in main_pclone_dic:
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

        # >> Fix this to match "Controls (Compact)" filter
        raw_control_list = machine_main_dic[m_name]['control_type']
        pretty_control_type_list = mame_improve_control_type_list(raw_control_list)
        control_list = mame_compress_item_list_compact(pretty_control_type_list)
        if not control_list: control_list = [ '[ No controls ]' ]

        # >> Fix this to match "Device (Compact)" filter
        raw_device_list = [ device['att_type'] for device in machine_main_dic[m_name]['devices'] ]
        pretty_device_list = mame_improve_device_list(raw_device_list)
        device_list = mame_compress_item_list_compact(pretty_device_list)
        if not device_list: device_list = [ '[ No devices ]' ]

        # --- Build filtering dictionary ---
        main_filter_dic[m_name] = {
            # --- Default filters ---
            'isDevice' : machine_render_dic[m_name]['isDevice'],
            # --- <Option> filters ---
            'coins' : coins,
            'hasROMs' : hasROMs,
            'hasCHDs' : hasCHDs,
            'hasSamples' : hasSamples,
            'isMature' : machine_render_dic[m_name]['isMature'],
            'isBIOS' : machine_render_dic[m_name]['isBIOS'],
            'isMechanical' : machine_main_dic[m_name]['isMechanical'],
            'isImperfect' : True if machine_render_dic[m_name]['driver_status'] == 'imperfect' else False,
            'isNonWorking' : True if machine_render_dic[m_name]['driver_status'] == 'preliminary' else False,
            # --- Other filters ---
            'driver' : machine_main_dic[m_name]['sourcefile'],
            'manufacturer' : machine_render_dic[m_name]['manufacturer'],
            'genre' : machine_render_dic[m_name]['genre'],
            'control_list' : control_list,
            'device_list' : device_list,
            'year' : machine_render_dic[m_name]['year'],
        }
        item_count += 1
    pDialog.update(100)
    pDialog.close()

    return main_filter_dic

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
# Tokenizer
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
# Manufacturer Parser (SP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
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
# Tokenizer
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
# Manufacturer Parser (LSP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
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
# YP operators: ==, <>, >, <, >=, <=, and, or, not, '(', ')', literal.
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
        return '<LITERAL "{0}">'.format(self.value)

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
        return "<OP (>"

class YP_operator_close_par_token:
    lbp = 0
    def __init__(self):
        self.id = "OP )"
    def __repr__(self):
        return "<OP )>"

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
        return "<OP not>"

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
        return "<OP and>"

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
        return "<OP or>"

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
        return "<OP ==>"

class YP_operator_not_equal_token:
    lbp = 50
    def __init__(self):
        self.id = "OP <>"
    def led(self, left):
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: log_debug('Executing <> token')
        ret = self.first.exec_token() <> self.second.exec_token()
        if debug_YP_parser: log_debug('<> token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP <>>"

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
        return "<OP >>"

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
        return "<OP <>"

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
        return "<OP >=>"

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
        return "<OP <=>"

class YP_end_token:
    lbp = 0
    def __init__(self):
        self.id = "END TOKEN"
    def __repr__(self):
        return "<END token>"

# -------------------------------------------------------------------------------------------------
# Tokenizer
# See http://jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
# -------------------------------------------------------------------------------------------------
YP_token_pat = re.compile("\s*(?:(==|<>|>=|<=|>|<|and|or|not|\(|\))|([\w]+))")

def YP_tokenize(program):
    # \s* -> Matches any number of blanks [ \t\n\r\f\v].
    # (?:...) -> A non-capturing version of regular parentheses.
    # \w -> Matches [a-zA-Z0-9_]
    for operator, n_string in YP_token_pat.findall(program):
        if n_string:
            yield YP_literal_token(n_string)
        elif operator == "==":
            yield YP_operator_equal_token()
        elif operator == "<>":
            yield YP_operator_not_equal_token()
        elif operator == ">":
            yield YP_operator_great_than_token()
        elif operator == "<":
            yield YP_operator_less_than_token()
        elif operator == ">=":
            yield YP_operator_great_or_equal_than_token()
        elif operator == "<=":
            yield YP_operator_less_or_equal_than_token()
        elif operator == "and":
            yield YP_operator_and_token()
        elif operator == "or":
            yield YP_operator_or_token()
        elif operator == "not":
            yield YP_operator_not_token()
        elif operator == "(":
            yield YP_operator_open_par_token()
        elif operator == ")":
            yield YP_operator_close_par_token()
        else:
            raise SyntaxError("Unknown operator: '{0}'".format(operator))
    yield YP_end_token()

# -------------------------------------------------------------------------------------------------
# Manufacturer Parser (YP) inspired by http://effbot.org/zone/simple-top-down-parsing.htm
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
        log_debug('YP_parse_exec() year     {0}'.format(year))
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
# Default filter removes device machines
#
def mame_filter_Default(mame_xml_dic):
    log_debug('mame_filter_Default() Starting ...')
    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        if mame_xml_dic[m_name]['isDevice']:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('mame_filter_Default() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Options_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Options_tag() Starting ...')
    options_list = f_definition['options']

    if not options_list:
        log_debug('mame_filter_Options_tag() Option list is empty.')
        return mame_xml_dic
    log_debug('Option list "{0}"'.format(options_list))

    # --- Compute bool variables ---
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

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
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
        # >> If machine was not removed then add it
        machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('mame_filter_Options_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Driver_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Driver_tag() Starting ...')
    filter_expression = f_definition['driver']

    if not filter_expression:
        log_debug('mame_filter_Driver_tag() User wants all drivers')
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
    log_debug('mame_filter_Driver_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Manufacturer_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Manufacturer_tag() Starting ...')
    filter_expression = f_definition['manufacturer']

    if not filter_expression:
        log_debug('mame_filter_Manufacturer_tag() User wants all manufacturers')
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
    log_debug('mame_filter_Manufacturer_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Genre_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Genre_tag() Starting ...')
    filter_expression = f_definition['genre']

    if not filter_expression:
        log_debug('mame_filter_Genre_tag() User wants all genres')
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
    log_debug('mame_filter_Genre_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Controls_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Controls_tag() Starting ...')
    filter_expression = f_definition['controls']

    if not filter_expression:
        log_debug('mame_filter_Controls_tag() User wants all genres')
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
    log_debug('mame_filter_Controls_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Devices_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Devices_tag() Starting ...')
    filter_expression = f_definition['devices']

    if not filter_expression:
        log_debug('mame_filter_Devices_tag() User wants all genres')
        return mame_xml_dic
    log_debug('Expression "{0}"'.format(filter_expression))

    initial_num_games = len(mame_xml_dic)
    filtered_out_games = 0
    machines_filtered_dic = {}
    for m_name in sorted(mame_xml_dic):
        # --- Update search list variable and call parser to evaluate expression ---
        bool_result = LSP_parse_exec(filter_expression, mame_xml_dic[m_name]['device_list'])
        if not bool_result:
            filtered_out_games += 1
        else:
            machines_filtered_dic[m_name] = mame_xml_dic[m_name]
    log_debug('mame_filter_Devices_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic

def mame_filter_Year_tag(mame_xml_dic, f_definition):
    # log_debug('mame_filter_Year_tag() Starting ...')
    filter_expression = f_definition['year']

    if not filter_expression:
        log_debug('mame_filter_Year_tag() User wants all genres')
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
    log_debug('mame_filter_Year_tag() Initial {0} | '.format(initial_num_games) + \
              'Removed {0} | '.format(filtered_out_games) + \
              'Remaining {0}'.format(len(machines_filtered_dic)))

    return machines_filtered_dic
