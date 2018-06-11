#!/usr/bin/python
#
import re

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
        if debug_SP_parser: print('Executing LITERAL token value "{0}"'.format(self.value))
        ret = self.value
        if debug_SP_parser: print('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_SP_parser: print('Executing HAS token')
        ret = True if SP_parser_search_string.find(self.first.exec_token()) >= 0 else False
        if debug_SP_parser: print('HAS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_SP_parser: print('Executing LACKS token')
        ret = False if SP_parser_search_string.find(self.first.exec_token()) >= 0 else True
        if debug_SP_parser: print('LACKS token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_SP_parser: print('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_SP_parser: print('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP not>"

class SP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_SP_parser: print('Executing AND token')
        self.first = left
        self.second = SP_expression(10)
        return self
    def exec_token(self):
        if debug_SP_parser: print('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_SP_parser: print('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_SP_parser: print('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_SP_parser: print('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        print('SP_parse_exec() Initialising program execution')
        print('SP_parse_exec() Search string "{0}"'.format(search_string))
        print('SP_parse_exec() Program       "{0}"'.format(program))
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
        print('SP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# --- main code -----------------------------------------------------------------------------------
# --- Input strings ---
i_str = 'Konami'

# --- Programs ---
# p_str = 'has Konami'
# p_str = 'lacks Konami'
# p_str = 'not has Konami'
# p_str = 'has Konami or has Namco'
# p_str = 'has Namco or has Konami'
# p_str = 'has Konami or not has Namco'
# p_str = 'has Konami or has Namco or has "Capcom / Kaneko"'
# p_str = 'nothas Konami or nothas Namco or nothas "Capcom / Kaneko"'
# p_str = 'lacks Konami and lacks Namco and lacks "Capcom / Kaneko"'
p_str = 'lacks Konami or lacks Namco or lacks "Capcom / Kaneko"'

# --- Test ---
print("String  '{0}'".format(i_str))
print("Program '{0}'".format(p_str))
t_counter = 0
for token in SP_tokenize(p_str):
    print("Token {0:02d} '{1}'".format(t_counter, token))
    t_counter += 1
result = SP_parse_exec(p_str, i_str)
print('Program result {0}'.format(result))
