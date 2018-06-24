# -*- coding: utf-8 -*-

'''
    Montreal Greek TV Add-on
    Author: greektimes

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re, hashlib, time

from resources.lib import control
from resources.lib.compat import str, database


def get(function_, time_out, *args, **table):
    try:
        response = None

        f = repr(function_)
        f = re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)

        a = hashlib.md5()
        for i in args:
            a.update(str(i))
        a = str(a.hexdigest())
    except BaseException:
        pass

    try:
        table = table['table']
    except BaseException:
        table = 'rel_list'

    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
        match = dbcur.fetchone()

        try:
            response = eval(match[2].encode('utf-8'))
        except AttributeError:
            response = eval(match[2])

        t1 = int(match[3])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(time_out)
        if not update:
            return response
    except BaseException:
        pass

    try:
        r = function_(*args)
        if (r is None or r == []) and response is not None:
            return response
        elif r is None or r == []:
            return r
    except BaseException:
        return

    try:
        r = repr(r)
        t = int(time.time())
        dbcur.execute("CREATE TABLE IF NOT EXISTS {} (""func TEXT, ""args TEXT, ""response TEXT, ""added TEXT, ""UNIQUE(func, args)"");".format(table))
        dbcur.execute("DELETE FROM {0} WHERE func = '{1}' AND args = '{2}'".format(table, f, a))
        dbcur.execute("INSERT INTO {} Values (?, ?, ?, ?)".format(table), (f, a, r, t))
        dbcon.commit()
    except BaseException:
        pass

    try:
        return eval(r.encode('utf-8'))
    except BaseException:
        return eval(r)


def timeout(function_, *args, **table):

    try:
        response = None

        f = repr(function_)
        f = re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)

        a = hashlib.md5()
        for i in args: a.update(str(i))
        a = str(a.hexdigest())
    except BaseException:
        pass

    try:
        table = table['table']
    except BaseException:
        table = 'rel_list'

    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM %s WHERE func = '%s' AND args = '%s'" % (table, f, a))
        match = dbcur.fetchone()
        return int(match[3])
    except BaseException:
        return


def clear(table=None, withyes=True):
    try:
        control.idle()

        if table is None:
            table = ['rel_list', 'rel_lib']
        elif not type(table) == list:
            table = [table]

        if withyes:

            try:
                yes = control.yesnoDialog(control.lang(30401).encode('utf-8'), '', '')
            except BaseException:
                yes = control.yesnoDialog(control.lang(30401), '', '')

            if not yes:
                return

        else:

            pass

        dbcon = database.connect(control.cacheFile)
        dbcur = dbcon.cursor()

        for t in table:
            try:
                dbcur.execute("DROP TABLE IF EXISTS %s" % t)
                dbcur.execute("VACUUM")
                dbcon.commit()
            except BaseException:
                pass

        control.infoDialog(control.lang(30402).encode('utf-8'))
    except BaseException:
        pass


def delete(dbfile=control.cacheFile, withyes=True):

    if withyes:

        yes = control.yesnoDialog(control.lang(30008).encode('utf-8'), '', '')

        if not yes:
            return

    else:

        pass

    control.deleteFile(dbfile)

    control.infoDialog(control.lang(30007).encode('utf-8'))
