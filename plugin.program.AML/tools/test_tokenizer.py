#!/usr/bin/python
#
import re

def tokenize(program):
    # \s* -> Matches any number of blanks [ \t\n\r\f\v].
    # (?:...) -> A non-capturing version of regular parentheses.
    # \b -> Matches the empty string, but only at the beginning or end of a word.
    # \w -> Matches [a-zA-Z0-9_]
    reg = "\s*(?:(and|or|not|\(|\))|(\"[ \.\w_\-\&]+\")|([\.\w_\-\&]+))"
    for operator, q_string, string in re.findall(reg, program):
        # print 'Tokenize >> Program -> "' + program + \
        #       '", String -> "' + string + '", Operator -> "' + operator + '"\n';
        if string:
            yield 'Literal "{0}"'.format(string)
        elif q_string:
            if q_string[0] == '"': q_string = q_string[1:]
            if q_string[-1] == '"': q_string = q_string[:-1]
            yield 'Literal quoted "{0}"'.format(q_string)
        elif operator == "and":
            yield 'Operator AND'
        elif operator == "or":
            yield 'Operator OR'
        elif operator == "not":
            yield 'Operator NOT'
        elif operator == "(":
            yield 'Operator ('
        elif operator == ")":
            yield 'Operator )'
        else:
            raise SyntaxError("Unknown operator: %r".format(operator))
    yield 'END Token'

# --- main code ---
# t_str = '"Ball & Paddle" or "Whac A Mole" or Climbing or Driving or Fighter or Platform or Puzzle or Shooter or Sports'
t_str = 'contains(Konami)'
print("String '{0}'".format(t_str))
t_counter = 0
for token in tokenize(t_str):
    print("Token {0:02d} '{1}'".format(t_counter, token))
    t_counter += 1
