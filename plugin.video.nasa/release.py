import zipfile
import os
import re
import xml.etree.ElementTree as xmltree

R_BLOCKED_PATTERNS = re.compile('(^.git|^pep|\.pyc$|\.pyo$|\.zip$|test)')


def get_files(source_dir, child_dir=''):
    addon_files = list()
    elements_list = os.listdir(source_dir)
    for element in elements_list:
        if re.search(R_BLOCKED_PATTERNS, element):
            continue
        if element == os.path.basename(__file__):
            continue
        element = os.path.join(child_dir, element)
        if os.path.isfile(element):
            addon_files.append(element)
        elif os.path.isdir(element):
            addon_files = addon_files + get_files(element, element)
    return addon_files


def create_zip(full_name, files_to_add, relative_dir):
    zf = zipfile.ZipFile(full_name, mode='w', compression=zipfile.ZIP_DEFLATED)
    for file_to_add in files_to_add:
        zf.write(file_to_add, os.path.join(relative_dir, file_to_add))
    zf.close()


def get_version(source_dir):
    return xmltree.parse('addon.xml').getroot().get('version')

if __name__ == '__main__':
    ADDON_DIR = os.getcwd()
    ADDON_NAME = os.path.basename(ADDON_DIR)
    ADDON_VERSION = get_version(ADDON_DIR)
    ADDON_FILES = get_files(ADDON_DIR)
    ADDON_ZIP_RELEASE_FILENAME = '%s-%s.zip' % (ADDON_NAME, ADDON_VERSION)
    create_zip(ADDON_ZIP_RELEASE_FILENAME, ADDON_FILES, ADDON_NAME)
    print 'Done.'