#
#       Copyright (C) 2014
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmc
import xbmcgui

import zipfile
import os

import utils
import sfile

global CHANGELOG
CHANGELOG = None


ADDON    = utils.ADDON
ADDONID  = utils.ADDONID
HOME     = xbmc.translatePath(ADDON.getAddonInfo('profile')) #has to be a real path
ROOT     = utils.ROOT
REMOTE   = ADDON.getSetting('REMOTE').lower() == 'true'
LOCATION = ADDON.getSetting('LOCATION')
TITLE    = utils.TITLE


GETTEXT  = utils.GETTEXT
 
def main():
    toImport = True

    if len(sys.argv) > 1:
        toImport = sys.argv[1].lower() != 'false'

    if toImport:
        doImport()
    else:
        doExport()


def doImport():
    try:
        success = False

        if REMOTE:
            success = _doImportFromRemote()
        else:
            filename = getFile(GETTEXT(30134), 'zip')

            if not filename:
                return False

            success = _doImportFromLocal(filename)

        if success:
            utils.DialogOK(GETTEXT(30133))
            if CHANGELOG:
                utils.showText(TITLE, CHANGELOG, True)               
            return True
    except:
        pass

    utils.DialogOK(GETTEXT(30137))
    return False


def _doImportFromRemote():
    try:
        location = LOCATION.replace(' ', '%20')
        file     = os.path.join(HOME, '_sf_temp.zip')

        dp = utils.Progress(TITLE, line1 = GETTEXT(30140) % GETTEXT(30000), line2 = location.replace('%20', ' '), line3 = GETTEXT(30141))

        import download
        download.doDownload(location, file, TITLE)

        if os.path.exists(file):
            success = extractAll(file, dp, location.replace('%20', ' '))
            utils.DeleteFile(file)
            return success
    except Exception, e:
        utils.log(e)

    return False


def _doImportFromLocal(filename):
    try:
        dp = utils.Progress(TITLE, line1 = GETTEXT(30140) % GETTEXT(30000), line2 = filename, line3 = GETTEXT(30141))
        return extractAll(filename, dp, filename)

    except Exception, e:
        utils.log(e)

    return False



def doExport():
    try:
        include = utils.DialogYesNo(GETTEXT(30129), line2='', line3=GETTEXT(30130), noLabel=None, yesLabel=None)
        folder  = getFolder(GETTEXT(30131))

        if not folder:
            return False

        filename = os.path.join(folder, 'Super Favourites.zip')

        doZipfile(filename, include)
        utils.DialogOK(GETTEXT(30132))
        return True

    except Exception, e:
        utils.log(e)

    return False


def doZipfile(outputFile, includeSettings=True):
    zip = None

    source  = os.path.join(HOME, 'Temp')
    if sfile.exists(source):
        sfile.rmtree(source)
    sfile.copytree(ROOT, source)

    relroot = os.path.abspath(os.path.join(source, os.pardir))

    for root, dirs, files in os.walk(source):

        if zip == None:
            zip = zipfile.ZipFile(outputFile, 'w', zipfile.ZIP_DEFLATED)

        local = os.path.relpath(root, relroot).split(os.sep, 1)
        if len(local) < 2:
            continue
        local = local[-1]

        # add directory (this is needed for empty dirs)
        if local.lower() == 'c':
            continue
        zip.write(root, local)

        for file in files:    
            if file == 'settings.xml':
                continue

            arcname  = os.path.join(local, file)
            filename = os.path.join(root, file)           
            zip.write(filename, arcname)

    if includeSettings:
        if zip == None:
            zip = zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED)

        arcname  = 'settings.xml'
        filename = os.path.join(HOME, arcname)

        zip.write(filename, arcname)

    sfile.rmtree(source)

        
def extractAll(filename, dp, location):
    global CHANGELOG
    CHANGELOG = None

    zin = zipfile.ZipFile(filename, 'r')

    relroot = os.path.abspath(os.path.join(ROOT, os.pardir))

    root    = os.path.join(HOME, 'Temp')
    profile = os.path.join(root, 'Super Favourites')

    try:
        nItem = float(len(zin.infolist()))
        index = 0
        for item in zin.infolist():
            index += 1

            percent  = int(index / nItem *100)
            filename = item.filename

            if dp:
                dp.update(percent, GETTEXT(30140) % filename, location, GETTEXT(30141))

            if filename == 'settings.xml':
                if utils.DialogYesNo(GETTEXT(30135), line2='', line3=GETTEXT(30136), noLabel=None, yesLabel=None):
                    zin.extract(item, HOME)
            elif filename == 'changelog.txt':
                try:
                    zin.extract(item, root)      
                    filename  = os.path.join(root, filename)
                    CHANGELOG = sfile.read(filename)
                    utils.DeleteFile(filename)
                except Exception, e:
                    utils.log('Changelog error in extractAll')
                    utils.log(e)
            elif filename.lower().startswith('super favourites'):
                zin.extract(item, root)
            elif filename.lower().startswith('s'):
                zin.extract(item, root)
            elif filename.lower().startswith('h'):
                zin.extract(item, root)
            elif filename.lower().startswith('pl'):
                zin.extract(item, root)
            else:
                zin.extract(item, profile)

    except Exception, e:
        utils.log('Error whilst unzipping %s' % location)
        utils.log(e)
        return False

    sfile.copytree(root, ROOT)
    sfile.rmtree(root)
    return True


def getFile(title, ext):
    filename = xbmcgui.Dialog().browse(1, title, 'files', '.'+ext, False, False, '')

    if filename == 'NO FILE':
        return None

    return filename



def getFolder(title):
    folder = xbmcgui.Dialog().browse(3, title, 'files', '', False, False, os.sep)

    return xbmc.translatePath(folder)


if __name__ == '__main__':
    try:
        main()
        import xbmcaddon
        xbmcaddon.Addon(ADDONID).openSettings()
        xbmc.executebuiltin('Container.Refresh')

    except:
        pass