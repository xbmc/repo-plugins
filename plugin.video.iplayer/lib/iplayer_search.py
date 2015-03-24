#!/usr/bin/python

# Python libs
import xbmc
import sys

# sets deprecated in 2.6+
if sys.version_info <= (2,5):
    from sets import Set as set

def load_search(file, tvradio):
    # load the list of search terms for the current search type
    lines = open(file, 'rb').readlines()
    searchlist = []
    for line in lines:
        (type, term) = line.split(':')
        if type == None or term == None: continue
        if type == tvradio:
            term = term.strip()
            searchlist.append(term)

    # remove any duplicates
    searchlist = list(set(searchlist))

    # sort the list
    searchlist.sort()

    return searchlist

def delete_search(file, tvradio, search):
    # load the list of search terms and delete the selected term
    lines = open(file, 'rb').readlines()

    searchtext = []
    for line in lines:
        (type, term) = line.split(':')
        term = term.strip()
        if type != tvradio or term != search:
            searchtext.append(line)

    open(file, 'wb').writelines(searchtext)


def save_search(file, tvradio, search):
    # save a new search term
    f = open(file, 'rb')
    txt = f.read()
    f.close()

    f = open(file, 'wb')
    txt += "%s:%s\n"  % (tvradio, search.strip())

    f.write(txt)
    f.close()

def prompt_for_search():
    # prompt the user to input search text
    kb = xbmc.Keyboard('', 'Search for')

    kb.doModal()
    if not kb.isConfirmed():
        return None;

    searchterm = kb.getText().strip()
    return searchterm

