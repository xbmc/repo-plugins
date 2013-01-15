from exception import QobuzXbmcError as Qerror
from gui.util import color
        
class contextMenu():
    def __init__(self):
        self.data = {}
        self.defaultSection = 'qobuz'
        self.colorItemDefault = "FF59A9C5"
        self.colorItemSection = "FF59A0FF"
        
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
        for key in  ['label', 'cmd']:
            if not key in ka:
                raise Qerror(who=self, 
                             what='missing_parameter', additional=key)
        section, path = self.get_section_path(**ka)
        root = self.data
        pos = 0
        if 'pos' in ka: pos = ka['pos']
        cmd = ''
        if 'cmd' in ka: cmd = ka['cmd']
        if not section in root:
            root[section] = {
                'label': section,
                'childs': [],
                'pos': pos,
                'cmd': cmd
            }
        if not path:
            root[section]['label'] = ka['label']
            root[section]['cmd'] = cmd
            root[section]['pos'] = pos
        else:
            item = {
                    'label': ka['label'],
                    'cmd': cmd,
                    'pos': pos
                    }
            root[section]['childs'].append(item)
        return root
    
    def getTuples(self):
        menuItems = []
        def sectionSort(key):
            return self.data[key]['pos']
               
        def itemSort(item):
                return item['pos']        
        
        for section in sorted(self.data, key=sectionSort):
            colorItem = self.colorItemSection
            data = self.data[section]
            if 'color' in data: 
                colorItem = data['color']
            ch = '--- ---'
            label = '%soO[ %s ]Oo%s' % (ch, color(colorItem, data['label']), ch)
            menuItems.append((label, data['cmd']))
            for item in sorted(data['childs'], key=itemSort):
                colorItem = self.colorItemDefault
                if 'color' in item:
                    colorItem = item['color']
                label = '%s' % (color(colorItem, item['label']))
                menuItems.append((label, item['cmd']))
#        menuItems = []
#        for i in range(0, 20):
#            menuItems.append(('plop %s' % str(i), 'plop'))
#        import pprint
#        print pprint.pformat(menuItems)
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
    
        