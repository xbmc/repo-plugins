# -*- coding: utf-8 -*-

'''
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


minute = 60
hour = 60 * minute
day = 24 * hour
week = 7 * day


def to_seconds(s):
    seconds = 0
    mult = 1
    for item in s.split(':')[::-1]:
        seconds += float(item) * mult
        mult *= 60
    return seconds


def to_str(seconds):
    s = ''
    if seconds >= week:
        weeks = int(seconds / week)
        unit = 'weeks' if weeks > 1 else 'week'
        s += '%s %s, ' % (weeks, unit)
        seconds -= weeks * week

    if seconds >= day:
        days = int(seconds / day)
        unit = 'days' if days > 1 else 'day'
        s += '%s %s, ' % (days, unit)
        seconds -= days * day

    mult = hour
    for i in xrange(2):
        item = int(seconds / mult)
        s += '%02d:' % (item)
        seconds -= item * mult
        mult /= 60
    s += '%06.3f' % (seconds)
    return s


