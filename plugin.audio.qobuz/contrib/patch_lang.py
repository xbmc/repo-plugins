#!/usr/bin/python

import os
import re
import fileinput
old = []
ID = 30001

seed_id = {}

pat_string_id = re.compile(r'^\s*'
                           '<string id='
                           '["\'](\d+)[\"\']'
                           '\s*>(.*)</string>$', re.IGNORECASE)

pat_lang = re.compile(r'lang\((\d+?)\)', re.S)


for line in fileinput.input('strings.xml', inplace=True): 
    m = pat_string_id.match(line)
    if not m:
        print line.strip()
        continue
    newid = int(m.group(1))
#     if newid > 30000 and newid <= 30999:
#         print line.strip()
#         continue
    txt = m.group(2)
    if newid in seed_id:
        raise ValueError('DOUBLE ID: %s', id)
    seed_id[newid] = ID
    print '<string id="%s">%s</string>' % (ID, txt)
    ID += 1

for root, dirs, files in os.walk(os.path.join(os.path.pardir)):
    for file in files:
        if file != 'strings.xml':
            continue
        path = os.path.join(root, file)
        if path.endswith(os.path.join('English', 'strings.xml')):
            continue
        for line in fileinput.input(path, inplace=True):
            m = re.finditer(pat_string_id, line)
            for match in m:
                fid = int(match.group(1))

                if not fid in seed_id:
                    print "# ERROR: Missing translation for %s" % fid
                    continue
                line = line.replace(str(fid), str(seed_id[fid]))
            print line,

for root, dirs, files in os.walk(os.path.join(os.path.pardir, 
                                               os.path.pardir, 'lib', 'qobuz')):
    for file in files:
        if not file.endswith('.py'):
            continue
        path = os.path.join(root, file)
        print "Patching file %s" % path
        for line in fileinput.input(path, inplace=True):
            m = re.finditer(pat_lang, line)
            for match in m:
                fid = int(match.group(1))
                if not fid in seed_id:
                    print "# ERROR: Missing translation for %s" % fid
                    continue
                line = line.replace(str(fid), str(seed_id[fid]))
            print line,