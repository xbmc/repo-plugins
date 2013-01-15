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

import os
import re
import xbmc
import requests
requests = requests.session(headers={'User-Agent':'xbmc.org'})

def get_subtitles(video_id):
  html = requests.get("http://tv.nrk.no/programsubtitles/%s" % video_id).text
  if not html:
    return None
  
  filename = os.path.join(xbmc.translatePath("special://temp"),'nrk.srt')
  with open(filename, 'w') as f:
    parts = re.compile(r'<p begin="(.*?)" dur="(.*?)".*?>(.*?)</p>',re.DOTALL).findall(html)
    i = 0
    for begint, dur, contents in parts:
      begin = _stringToTime(begint)
      dur = _stringToTime(dur)
      end = begin+dur
      i += 1
      f.write(str(i))
      f.write('\n%s' % _timeToString(begin))
      f.write(' --> %s\n' % _timeToString(end))
      f.write(re.sub('<br />\s*','\n',' '.join(contents.replace('<span style="italic">','<i>').replace('</span>','</i>').split())).encode('utf-8'))
      f.write('\n\n')
  return filename

def _stringToTime(txt):
  p = txt.split(':')
  return int(p[0])*3600+int(p[1])*60+float(p[2])

def _timeToString(time):
  return '%02d:%02d:%02d,%03d' % (time/3600,(time%3600)/60,time%60,(time%1)*1000)
