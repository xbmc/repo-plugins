#!/usr/bin/python
#
import re

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
        if debug_YP_parser: print('Executing LITERAL token value "{0}"'.format(self.value))
        if self.value == 'year':
            ret = YP_year
        else:
            ret = int(self.value)
        if debug_YP_parser: print('LITERAL token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing NOT token')
        ret = not self.first.exec_token()
        if debug_YP_parser: print('NOT token returns {0} "{1}"'.format(type(ret), unicode(ret)))
        return ret
    def __repr__(self):
        return "<OP not>"

class YP_operator_and_token:
    lbp = 10
    def __init__(self):
        self.id = "OP AND"
    def led(self, left):
        if debug_YP_parser: print('Executing AND token')
        self.first = left
        self.second = YP_expression(10)
        return self
    def exec_token(self):
        if debug_YP_parser: print('Executing AND token')
        ret = self.first.exec_token() and self.second.exec_token()
        if debug_YP_parser: print('AND token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing OR token')
        ret = self.first.exec_token() or self.second.exec_token()
        if debug_YP_parser: print('OR token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing == token')
        ret = self.first.exec_token() == self.second.exec_token()
        if debug_YP_parser: print('== token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing <> token')
        ret = self.first.exec_token() <> self.second.exec_token()
        if debug_YP_parser: print('<> token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing > token')
        ret = self.first.exec_token() > self.second.exec_token()
        if debug_YP_parser: print('> token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing < token')
        ret = self.first.exec_token() < self.second.exec_token()
        if debug_YP_parser: print('< token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing >= token')
        ret = self.first.exec_token() >= self.second.exec_token()
        if debug_YP_parser: print('>= token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        if debug_YP_parser: print('Executing <= token')
        ret = self.first.exec_token() <= self.second.exec_token()
        if debug_YP_parser: print('<= token returns {0} "{1}"'.format(type(ret), unicode(ret)))
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
        print('YP_parse_exec() Initialising program execution')
        print('YP_parse_exec() year     {0}'.format(year))
        print('YP_parse_exec() Program  "{0}"'.format(program))
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
        print('YP_parse_exec() Init exec program in token {0}'.format(left))

    return left.exec_token()

# --- main code -----------------------------------------------------------------------------------
# --- Input strings ---
# >> Consider all ill-former year strings in MAME like incomplete years.
# year_str = '1992'

# >> This years are converted 1992? to int 1992
year_str = '1992?'

# >> All this years to int 0
# year_str = 'None'
# year_str = '????'
# year_str = '198?'
# year_str = '199?'
# year_str = '200?'
# year_str = '201?'
# year_str = '19??'
# year_str = '20??'

# --- Programs ---
# p_str = 'year == 1992'
# p_str = 'year == 1995'
# p_str = 'year <> 1992'
# p_str = 'year <> 1995'
# p_str = 'year > 1992'
# p_str = 'year < 1992'
# p_str = 'year >= 1992'
# p_str = 'year <= 1992'
# p_str = 'year < 1992 and (year <> 1970 or year <> 1960)'
# p_str = 'year < 1980'
p_str = 'year >= 1980 and year < 1990'
# p_str = 'year >= 1990 and year < 2000'
# p_str = 'year >= 2000'

# --- Test ---
print("year_str '{0}'".format(year_str))
print("Program  '{0}'".format(p_str))
t_counter = 0
for token in YP_tokenize(p_str):
    print("Token {0:02d} '{1}'".format(t_counter, token))
    t_counter += 1
result = YP_parse_exec(p_str, year_str)
print('Program result {0}'.format(result))
