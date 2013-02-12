#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.
from exception import QobuzXbmcError as Qerror
from gui.util import color, getSetting

class contextMenu():
    '''Creating context menu:
        add(path='test', cmd='foo' ...)
        add(path='test/test_one', cmd='bar', ...)
        ...
    '''
    def __init__(self):
        self.data = {}
        self.defaultSection = 'qobuz'
        self.color_default = getSetting('item_default_color')
        self.color_section = getSetting('item_section_color')
        formatStr = getSetting('item_section_format')
        try:
            test = formatStr % ('plop')
        except:
            formatStr = '[ %s ]'
        self.format_section = formatStr
    
    def get_section_path(self, **ka):
        path = self.defaultSection
        if 'path' in ka and ka['path']:
            path = ka['path']
        xPath = path.lower().split('/')
        section = xPath.pop(0)
        if len(xPath) == 0:
            path = None
        else:
            path = '-'.join(xPath)
        return section, path

    def add(self, **ka):
        '''Add menu entry
            Parameters:
                path: string, <section>/<id> (id juste need to be unique)
                cmd: string, xbmc command to run
                color: string, override default color
                pos: int, position in menu
        '''
        for key in  ['label', 'cmd']:
            if not key in ka:
                raise Qerror(who=self, 
                             what='missing_parameter', additional=key)
        section, path = self.get_section_path(**ka)
        root = self.data
        pos = 0
        if 'pos' in ka: 
            pos = ka['pos']
        cmd = ''
        if 'cmd' in ka: 
            cmd = ka['cmd']
        color = ''
        if 'color' in ka:
            color = ka['color']
        if not section in root:
            root[section] = {
                'label': section,
                'childs': [],
                'pos': pos,
                'cmd': cmd,
                'color': color
            }
        if not path:
            root[section]['label'] = ka['label']
            root[section]['cmd'] = cmd
            root[section]['pos'] = pos
            root[section]['color'] = color
        else:
            item = {'label': ka['label'],
                    'cmd': cmd,
                    'pos': pos,
                    'color': color }
            root[section]['childs'].append(item)
        return root

    def getTuples(self):
        menuItems = []
        def sectionSort(key):
            return self.data[key]['pos']
               
        def itemSort(item):
                return item['pos']        
        for section in sorted(self.data, key=sectionSort):
            colorItem = self.color_section
            data = self.data[section]
            if 'color' in data and data['color']: 
                colorItem = data['color']
            label = self.format_section % (color(colorItem, data['label']))
            #menuItems.append((label, data['cmd']))
            for item in sorted(data['childs'], key=itemSort):
                colorItem = self.color_default
                if 'color' in item and item['color']:
                    colorItem = item['color']
                label = '%s' % (color(colorItem, item['label']))
                menuItems.append((label, item['cmd']))
        return menuItems

if __name__ == '__main__':
    c = contextMenu()
    c.add(path='qobuz', label='Qobuz', cmd='playlist', pos = 1)
    c.add(path='playlist', label='Global', cmd='playlist', pos=2)
    c.add(path='friends', label='Global', cmd='toto', pos=3)
    c.add(path='friends/titi', label='Titi', cmd='nop', pos = 1)
    c.add(path='friends/toto', label='Toto', cmd='nop', pos = 4)
    c.add(path='friends/plop', label='Plop', cmd='nop', pos = 0)
    c.getTuples()
