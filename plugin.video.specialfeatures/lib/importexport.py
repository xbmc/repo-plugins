# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
"""
Import/Export module

This module handles importing and exporting sfnfo data

This file is part of Special Features.

Special Features is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

Special Features is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Special Features. If not, see <http://www.gnu.org/licenses/>.

@author: smitchell6879
@author: evertiro
@license: GPL-3.0
"""

from lib.sys_init import *


def initTree(path):
    global tree
    tree = ET.parse(path)
    global root
    root = tree.getroot()


class exPort_sfnfo:
    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def buildTree(self, t, st, p, f):
        if st == 'None':
            st = ""
        if p == 'None':
            p = ""
        self.header = ET.Element('specialfeatures')
        self.title = ET.SubElement(self.header, 'title')
        self.title.text = '{}'.format(t)
        self.sorttitle = ET.SubElement(self.header, 'sorttitle')
        self.sorttitle.text = '{}'.format(st)
        self.plot = ET.SubElement(self.header, 'plot')
        self.plot.text = '{}'.format(p)
        self.indent(self.header)
        self.sfnfo = ET.ElementTree(self.header)
        self.sfnfo.write(f, xml_declaration=True, encoding='utf-8', method="xml")

    def updateTree(self, path, tag, text):
        initTree(path)
        child = root.find('{}'.format(tag))
        child.text = '{}'.format(text)
        tree.write(path)

    def writeTree(self, iterate):
        if dialog.yesno(lang(30000), lang(30063)) == 1:
            self.cst = 1
            bgdc(lang(30000), lang(30064))
            for self.item in iterate:
                self.pct = float(self.cst)/float(len(iterate))*100
                bgdu(int(self.pct), lang(30000), "{0} {1}{2}{3}".format(lang(30064), self.cst, lang(30052), len(iterate)))
                try:
                    if mysql == 'true':
                        self.buildTree(self.item['title'], self.item['sorttitle'], self.item['plot'], os.path.splitext(self.item['bpath'])[0]+'.sfnfo')
                    else:
                        self.buildTree(self.item[1], self.item[3], self.item[4], os.path.splitext(self.item[2])[0]+'.sfnfo')
                except:
                    error('Could not write to file directory, check your write permissions')
                self.cst += 1
            bgdcc()
        else:
            self.cst = 1
            bgdc(lang(30000), lang(30064))
            for self.item in iterate:
                if mysql == 'true':
                    if xbmcvfs.exists(os.path.splitext(self.item['bpath'])[0]+'.sfnfo') == 0:
                        self.pct = float(self.cst)/float(len(iterate))*100
                else:
                    if xbmcvfs.exists(os.path.splitext(self.item[2])[0]+'.sfnfo') == 0:
                        self.pct = float(self.cst)/float(len(iterate))*100
                    bgdu(int(self.pct), lang(30000), "{0} {1}{2}{3}".format(lang(30064), self.cst, lang(30052), len(iterate)))
                    try:
                        if mysql == 'true':
                            self.buildTree(self.item['title'], self.item['sorttitle'], self.item['plot'], os.path.splitext(self.item['bpath'])[0]+'.sfnfo')
                        else:
                            self.buildTree(self.item[1], self.item[3], self.item[4], os.path.splitext(self.item[2])[0]+'.sfnfo')
                    except:
                        error('Could not write to file directory, check your write permissions')
                    self.cst += 1
            bgdcc()


class imPort_sfnfo:
    def upDate(self, path):
        if self.checkout(path) == 1:
            initTree(self.path)
            self.vars()
            return {'title': self.title, 'path': path, 'sorttitle': self.sorttitle, 'plot': self.plot}
        else:
            return None

    def vars(self):
        self.title = root.find('title').text
        self.sorttitle = root.find('sorttitle').text
        self.plot = root.find('plot').text

    def checkout(self, path):
        self.path = os.path.splitext(path)[0]
        self.path = self.path+'.sfnfo'
        return xbmcvfs.exists(self.path)
