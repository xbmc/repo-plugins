#/*
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import random
import os

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.mozart')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Mozart"
__addonid__      = "plugin.audio.mozart"
__author__      = "Assen Totin <assen.totin@gmail.com>"

BASE_URL = 'ftp://ftp.cs.princeton.edu/pub/cs126/mozart/mozart.jar'
WAV_ZIP_FILENAME = 'mozart.jar'
DIR_RESOURCES = "resources"
DIR_FILES = "files"
DIR_LIB = "lib"
MIDI_ZIP_FILENAME = "midi.zip"

CHUNK_SIZE = 1048576

OUTPUT_FILENAME_WAV = "waltz.wav"

# Output file name for MIDI should, naturally, be "waltz.mid". 
# However, XBMC 10.0 (Dharma) using ModplugCodec for .mid extenstion, but it seems to be buggy - strange additional sounds are heard.
# For .kar (Karaoke files), XBMC uses built-in timidity which plays the MIDI files properly. 
# Details: http://forum.xbmc.org/showthread.php?t=88790&highlight=soundfont
# Therefore, as a workaround, we create the MIDI file with .kar extension.
#OUTPUT_FILENAME_MIDI = "waltz.mid"
OUTPUT_FILENAME_MIDI = "waltz.kar"

# Obtain the full path of "userdata/add_ons" directory
def getUserdataDir():
  path = xbmc.translatePath(__settings__.getAddonInfo('profile'))
  return path


# Obtain the full path to the MIDI ZIP file 
def getMidiZipFileName():
  path = xbmc.translatePath(__settings__.getAddonInfo('path'))
  path_resources = os.path.join(path, DIR_RESOURCES)
  path_files = os.path.join(path_resources, DIR_FILES)
  midi_zip_filename = os.path.join(path_files, MIDI_ZIP_FILENAME)
  return midi_zip_filename


# First run?
def firstRun(path):
  if os.path.exists(path): return 0
  else: return 1  


# Init on first run
def initOnFirstRun(have_midi, path):
  if not os.path.exists(path):  os.makedirs(path)

  if have_midi == 1: 
    res = getMidiFiles(path)
    if res == -1:
      cleanupOnCancel(path)
      return -1
    res = unzipFile(path, MIDI_ZIP_FILENAME)
    if res == -1:
      cleanupOnCancel(path)
      return -1

  else: 
    res = getWavFiles(path)
    if res == -1: 
      cleanupOnCancel(path)
      return -1
    res = unzipFile(path, WAV_ZIP_FILENAME)
    if res == -1:
      cleanupOnCancel(path)
      return -1

  return 0


def cleanupOnCancel(path):
  import shutil
  shutil.rmtree(path)


# Check for MIDI support
def checkMIDI():
  path1 = xbmc.translatePath('special://xbmc/system/players/paplayer/timidity/soundfont.sf2')
  path2 = xbmc.translatePath('special://masterprofile/timidity/soundfont.sf2')
  log(path1)
  log(path2)
  if os.path.exists(path1) or os.path.exists(path2): 
    log_notice("Using MIDI...")
    return 1
  log_notice("No MIDI support, reverting to WAV..."); 
  return 0


# Unzip Files
def unzipFile(path, filename):
  import zipfile, time

  # Create a dialog
  dialog = xbmcgui.DialogProgress()
  dialog.create(__language__(30090), __language__(30092))
  dialog.update(1)

  zip_file_name = os.path.join(path, filename)
  myzip = zipfile.ZipFile(zip_file_name,'r')

  # Extract. On Python 2.6 and beterer, use the nice and cosy "extractall()" method
  try: myzip.extractall(path)
  except:
    # On older Python versions (incl. PPA builds of XBMC 10.0 for Ubuntu!), there is no reasonable support for extracting ZIP files, only for creating ones (?!)
    # So, use Doug Tolton's idea from http://code.activestate.com/recipes/252508-file-unzip/
    myzip_dirs = []
    for dir_name in myzip.namelist():
      if dir_name.endswith('/'): myzip_dirs.append(dir_name)
      myzip_dirs.sort()
    for new_dir in myzip_dirs:
      curdir = os.path.join(path, new_dir)
      if not os.path.exists(curdir): os.mkdir(curdir)
    for compressed_file_name in myzip.namelist():
      if not compressed_file_name.endswith('/'):
        output_file = open(os.path.join(path, compressed_file_name), 'wb')
        output_file.write(myzip.read(compressed_file_name))
        output_file.flush()
        output_file.close()

  os.remove(zip_file_name)

  dialog.update(100, __language__(30093))
  time.sleep(1)
  dialog.close()

  # Check if dialog was canceled during unzipping
  if (dialog.iscanceled()): return -1

  return 0


# Download WAV files
def getWavFiles(path):
  import urllib2, time

  tmp_file_name = os.path.join(path, WAV_ZIP_FILENAME)
  f = open(tmp_file_name,'wb')

  # Create a dialog
  dialog = xbmcgui.DialogProgress()
  dialog.create(__language__(30090), __language__(30091))
  dialog.update(1)

  # Download in chunks of CHUNK_SIZE, update the dialog
  # URL progress bar code taken from triptych (http://stackoverflow.com/users/43089/triptych):
  # See original code http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
  response = urllib2.urlopen(BASE_URL);
  total_size = response.info().getheader('Content-Length').strip()
  total_size = int(total_size)
  bytes_so_far = 0

  while 1:
    chunk = response.read(CHUNK_SIZE)
    bytes_so_far += len(chunk)

    if not chunk: break

    if (dialog.iscanceled()): return -1

    f.write(chunk)
    percent = float(bytes_so_far) / total_size
    val = int(percent * 100)
    if (val >= 98): val = 98
    dialog.update(val)

  response.close()
  f.close()

  dialog.update(100, __language__(30093))
  time.sleep(1)
  dialog.close()

  # Check if dialog was canceled during unzipping
  if (dialog.iscanceled()): return -1

  return 0

# Get MIDI Files
def getMidiFiles(path):
  import shutil
  zip_file_name = getMidiZipFileName()
  shutil.copy(zip_file_name, path)
  return 0

# Roll all dice, return list of pieces
def diceRoll(have_midi):
  # Init Menuet table (16 bars, 2 dice)
  m1 = {'2':96, '3':32, '4':69, '5':40, '6':148, '7':104, '8':152, '9':119, '10':98, '11':3, '12':54}
  m2 = {'2':22, '3':6, '4':95, '5':17, '6':74, '7':157, '8':60, '9':84, '10':142, '11':87, '12':130}
  m3 = {'2':141, '3':128, '4':158, '5':113, '6':163, '7':27, '8':171, '9':114, '10':42, '11':165, '12':10}
  m4 = {'2':41, '3':63, '4':13, '5':85, '6':45, '7':167, '8':53, '9':50, '10':156, '11':61, '12':103}
  m5 = {'2':105, '3':146, '4':153, '5':161, '6':80, '7':154, '8':99, '9':140, '10':75, '11':135, '12':28}
  m6 = {'2':122, '3':46, '4':55, '5':2, '6':97, '7':68, '8':133, '9':86, '10':129, '11':47, '12':106}
  m7 = {'2':11, '3':134, '4':110, '5':159, '6':36, '7':118, '8':21, '9':169, '10':62, '11':147, '12':106}
  m8 = {'2':30, '3':81, '4':24, '5':100, '6':107, '7':91, '8':127, '9':94, '10':123, '11':33, '12':5}
  m9 = {'2':70, '3':117, '4':66, '5':90, '6':25, '7':138, '8':16, '9':120, '10':65, '11':102, '12':35}
  m10 = {'2':121, '3':39, '4':139, '5':176, '6':143, '7':71, '8':155, '9':88, '10':77, '11':4, '12':20}
  m11 = {'2':26, '3':126, '4':15, '5':7, '6':64, '7':150, '8':57, '9':48, '10':19, '11':31, '12':108}
  m12 = {'2':9, '3':56, '4':132, '5':34, '6':125, '7':29, '8':175, '9':166, '10':82, '11':164, '12':92}
  m13 = {'2':112, '3':174, '4':73, '5':67, '6':76, '7':101, '8':43, '9':51, '10':137, '11':144, '12':12}
  m14 = {'2':49, '3':18, '4':58, '5':160, '6':136, '7':162, '8':168, '9':115, '10':38, '11':59, '12':124}
  m15 = {'2':109, '3':116, '4':145, '5':52, '6':1, '7':23, '8':89, '9':72, '10':149, '11':173, '12':44}
  m16 = {'2':14, '3':83, '4':79, '5':170, '6':93, '7':151, '8':172, '9':111, '10':8, '11':78, '12':131}

  # Trio table (16 bars, 1 dice):
  t1 = {'1':72, '2':56, '3':75, '4':40, '5':83, '6':18}
  t2 = {'1':6, '2':82, '3':39, '4':73, '5':3, '6':45}
  t3 = {'1':59, '2':42, '3':54, '4':16, '5':28, '6':62}
  t4 = {'1':25, '2':74, '3':1, '4':68, '5':53, '6':38}
  t5 = {'1':81, '2':14, '3':65, '4':29, '5':37, '6':5}
  t6 = {'1':41, '2':7, '3':43, '4':55, '5':17, '6':28}
  t7 = {'1':89, '2':26, '3':15, '4':2, '5':44, '6':52}
  t8 = {'1':13, '2':71, '3':80, '4':61, '5':70, '6':94}
  t9 = {'1':36, '2':76, '3':9, '4':22, '5':63, '6':11}
  t10 = {'1':5, '2':20, '3':34, '4':67, '5':85, '6':92}
  t11 = {'1':46, '2':64, '3':93, '4':49, '5':32, '6':24}
  t12 = {'1':79, '2':84, '3':48, '4':77, '5':96, '6':86}
  t13 = {'1':30, '2':8, '3':69, '4':57, '5':12, '6':51}
  t14 = {'1':95, '2':35, '3':58, '4':87, '5':23, '6':60}
  t15 = {'1':19, '2':47, '3':90, '4':33, '5':50, '6':78}
  t16 = {'1':66, '2':88, '3':21, '4':10, '5':91, '6':31}

  infiles = []

  files_dir = getUserdataDir()

  if (have_midi == 1):  suffix = "mid"
  else: suffix = "wav"

  for i in range (1, 17):
    # This could have been one single call, but this will make it more true to the spirit of the game
    d1 = random.randrange(6) + 1
    d2 = random.randrange(6) + 1
    d = d1 + d2
    dd = str(d)
    if i == 1: m = m1
    elif i == 2: m = m2
    elif i == 3: m = m3
    elif i == 4: m = m4
    elif i == 5: m = m5
    elif i == 6: m = m6
    elif i == 7: m = m7
    elif i == 8: m = m8
    elif i == 9: m = m9
    elif i == 10: m = m10
    elif i == 11: m = m11
    elif i == 12: m = m12
    elif i == 13: m = m13
    elif i == 14: m = m14
    elif i == 15: m = m15
    elif i == 16: m = m16
    filename = "M%s.%s" % (m[dd], suffix)
    filename = os.path.join(files_dir,filename)
    infiles.append(filename)

  for i in range (1, 17):
    d = random.randrange(6) + 1
    dd = str(d)
    if i == 1: t = t1
    elif i == 2: t = t2
    elif i == 3: t = t3
    elif i == 4: t = t4
    elif i == 5: t = t5
    elif i == 6: t = t6
    elif i == 7: t = t7
    elif i == 8: t = t8
    elif i == 9: t = t9
    elif i == 10: t = t10
    elif i == 11: t = t11
    elif i == 12: t = t12
    elif i == 13: t = t13
    elif i == 14: t = t14
    elif i == 15: t = t15
    elif i == 16: t = t16
    filename = "T%s.%s" % (t[dd], suffix)
    filename = os.path.join(files_dir,filename)
    infiles.append(filename)

  return infiles

# Concat all WAV file sinto one single WAV file
def buildFileWav(infiles, files_dir):
  import wave
  outfile = os.path.join(files_dir,OUTPUT_FILENAME_WAV)

  data= []
  wav_frames_total = 0

  for infile in infiles:
    log(infile)
    w = wave.open(infile, 'rb')
    wav_frames_total += w.getnframes()
    data.append( [w.getparams(), w.readframes(w.getnframes())] )
    w.close()

  output = wave.open(outfile, 'wb')
  log(data[0][0])
  output.setparams(data[0][0])

  # On older (buggy?) Python versions like XBMC's built-in 2.4 .writeframes() seems not to update the "nframes" field of the WAV header 
  # and the resulting output file is a truncated mess. Therefore, force the nframes for the header and only write raw data. 
  #
  # To give developers even more fun, trying to manually build the full header on python 2.4 is an epic fail:
  # - when you read the docs for wave module (python 2.4 and all next versions) it says .setcomptype() takes 2 parameters;
  # - when you call .readcomptype() you get a list of two elements;
  # - when you feed this list to .setcomptype(), it raises an error that it takes "exactly 3 parameters"!
  #
  # On a modern Python version, just skip the .setnframes() and inside the loop, call .writeframes() instead of .writeframesraw()
  output.setnframes(wav_frames_total)

  for i in range(0, 32):
    output.writeframesraw(data[i][1])
  output.close()

  return outfile


# Concat all MIDI files into one single MIDI file
def buildFileMidi(infiles, files_dir):
  path = xbmc.translatePath(__settings__.getAddonInfo('path'))
  path_resources = os.path.join(path, DIR_RESOURCES)
  path_lib = os.path.join(path_resources, DIR_LIB)
  sys.path.append(path_lib)

  import midi

  midi_file_out = midi.MidiFile()
  midi_file_out.format = 0
  midi_file_out.ticksPerQuarterNote = 480

  t0 = midi.MidiTrack(0)
  midi_file_out.tracks.append(t0)

  cnt = 0;
  for infile in infiles:
    is_first = 0
    is_last = 0
    if cnt == 0:
      is_first = 1
    elif cnt == 31:
      is_last = 1
    cnt = cnt + 1

    midi_file_tmp = midi.MidiFile()
    midi_file_tmp.open(infile)
    midi_file_tmp.readEvents(is_first, is_last)

    for trk in midi_file_tmp.tracks:
      for e in trk.events:
        midi_file_out.tracks[0].events.append(e)

    midi_file_tmp.close()

  outfile = os.path.join(files_dir,OUTPUT_FILENAME_MIDI)
  midi_file_out.open(outfile, "wb")
  midi_file_out.write()
  midi_file_out.close()
  return outfile


# Logging
def log(msg):
  xbmc.log("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGDEBUG )


# Log NOTICE
def log_notice(msg):
  xbmc.log("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGNOTICE )


# MAIN
have_midi = checkMIDI()

files_dir = getUserdataDir()

res = 0
first_run = firstRun(files_dir)
if first_run == 1: 
  res = initOnFirstRun(have_midi, files_dir)

if res == 0:
  infiles = diceRoll(have_midi)

  if have_midi == 1: 
    outfile = buildFileMidi(infiles, files_dir)
  else: 
    outfile = buildFileWav(infiles, files_dir)

  xbmc.Player().play(outfile)


