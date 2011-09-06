# -*- coding: utf-8 -*-
'''
    NRK plugin for XBMC
    Copyright (C) 2010 Thomas Amland

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import urllib, os
from DataItem import DataItem

R_PATH = os.path.join(os.getcwd(), 'resources', 'images', )

def getGenres():
    genres = [('Barn',          '2',    'thm_kids.png'),
              ('Distrikt',      '13',   'thm_rgns.png'),
              ('Dokumentar',    '20',   'thm_docu.png'),
              ('Drama',         '3',    'thm_drma.png'),
              ('Fakta',         '4',    'thm_fact.png'),
              ('Kultur',        '5',    'thm_cult.png'),
              ('Livssyn',       '9',    'thm_life.png'),
              ('Mat',           '17',   'thm_food.png'),
              ('Musikk',        '6',    'thm_msic.png'),
              ('Natur',         '7',    'thm_ntur.png'),
              ('Nyheter',       '8',    'thm_news.png'),
              ('På samisk',     '19',   'thm_sami.png'),
              ('På tegnspråk',  '22',   'thm_sign.png'),
              ('Sport',         '10',   'thm_sprt.png'),
              ('Underholdning', '11',   'thm_entn.png'),
              ('Ung',           '21',   'thm_teen.png')]
    items = []
    for (name, id, icon) in genres:
        items.append(DataItem(title=name, thumb=os.path.join(R_PATH, icon) , url="/nett-tv/tema/" + id))
    return items


def getLetters():
    letters = [ord('1'), ord('2'), ord('3'), ord('7')]
    letters.extend(range(ord('a'), ord('w')))
    letters.extend([ ord('y'), 216, 229 ])
    enc = lambda ch: urllib.quote(unichr(ch).encode('latin-1'))
    return [ DataItem(title=unichr(ch).upper(), url="/nett-tv/bokstav/"+enc(ch)) for ch in letters ]

