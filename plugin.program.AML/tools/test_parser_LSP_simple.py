#!/usr/bin/python
#
import re

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
        if debug_LSP_parser: print('Executing LITERAL token value "{0}"'.format(self.value))
        ret = self.value
        if debug_LSP_parser: print('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_LSP_parser: print('Executing HAS token')
        ret = self.first.exec_token() in LSP_parser_search_list
        if debug_LSP_parser: print('HAS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_LSP_parser: print('Executing LACKS token')
        ret = self.first.exec_token() not in LSP_parser_search_list
        if debug_LSP_parser: print('LACKS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_LSP_parser: print('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_LSP_parser: print('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP not>"

class LSP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_LSP_parser: print('Executing AND token')
        self.first = left
        self.second = LSP_expression(10)
        return self
    def exec_token(self):
        if debug_LSP_parser: print('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_LSP_parser: print('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_LSP_parser: print('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_LSP_parser: print('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        print('LSP_parse_exec() Initialising program execution')
        print('LSP_parse_exec() Search string "{0}"'.format(unicode(search_list)))
        print('LSP_parse_exec() Program       "{0}"'.format(program))
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
        print('LSP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# --- main code -----------------------------------------------------------------------------------
# --- Input strings ---
i_list = ['Konami', 'Capcom']

# --- Programs ---
# p_str = 'Konami'
# p_str = 'not Konami'
# p_str = 'Konami or Namco'
# p_str = 'Konami and Namco'
# p_str = 'Namco or (Konami or Capcom)'
# p_str = 'Namco or (Konami or not Capcom)'
# p_str = 'Namco or (Konami or not (Capcom and Kaneko))'
# p_str = '"Capcom / Kaneko"'
# p_str = '"Capcom / Kaneko" or Namco'
p_str = 'lacks Capcom and lacks Kaneko and lacks Namco'
# p_str = 'lacks Capcom or lacks Kaneko or lacks Namco'

# --- Test ---
print("String  '{0}'".format(unicode(i_list)))
print("Program '{0}'".format(p_str))
t_counter = 0
for token in LSP_tokenize(p_str):
    print("Token {0:02d} '{1}'".format(t_counter, token))
    t_counter += 1
result = LSP_parse_exec(p_str, i_list)
print('Program result {0}'.format(result))
