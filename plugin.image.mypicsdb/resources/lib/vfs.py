'''
    Convenience wrappers  and extensions for some commonly used VFS functions
    in XBMC addons.  This module exposes all the functionality of xbmcvfs plus
    some extra functions.

    Copyright (C) 2012 Patrick Carey

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

import json
import os
import xbmc
import xbmcvfs


def walk(path):

    '''
        Reimplementation of os.walk using XBMC's jsonrpc API.

        This has the nice added benefits of being able to walk remote
        directories and inside compressed files such as rars/zips.
    '''

    dir_tree = [[path]]

    current_depth = 0

    while True:

        if current_depth > -1:

            try:

                current_path = dir_tree[current_depth].pop(0)
                current_dirs, current_files = [], []

                for x in listdir(current_path, extra_metadata=True):

                    if x['filetype'] == 'directory':

                        current_dirs.append(x['file'])

                    else:

                        current_files.append(x['file'])

            except IndexError:

                current_depth -= 1

                dir_tree.pop()

            else:

                yield (current_path, current_dirs, current_files)

                if current_dirs:

                    current_depth += 1

                    dir_tree.append(current_dirs)

        else:

            break


def listdir(path, extra_metadata=False):

    '''
        Reimplementation of os.listdir using XBMC's jsonrpc API.

        Returns a list of file/directory names from the specified path

        Accepts an optional boolean 'extra_metadata' as the second argument
        which will cause the function to instead return a list of dictionaries
        containing all of the metadata about each file that was retrieved from
        XBMC.
    '''

    fileList = []

    json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } } , "id" : 1 }' % path.encode('utf-8').replace('\\', '\\\\'))

    jsonobject = json.loads(json_response)

    if jsonobject['result']['files']:

        for item in jsonobject['result']['files']:

            if extra_metadata:

                fileList.append(item)

            else:

                fileList.append(item['file'])

    return fileList


def copy(source, destination):

    """
    copy(source, destination) -- Copy file to destination, returns true/false.

    source          : file to copy.
    destination     : destination file

    example:
     - success = vfs.copy(source, destination)
    """

    return xbmcvfs.copy(source, destination)


def delete(path):

    """
    delete(file) -- Delete file

    file        : file to delete

    example:
     - vfs.delete(file)
    """

    return xbmcvfs.delete(path)


def exists(path):

    """
    exists(path) -- Check if file exists, returns true/false.

    path        : file or folder

    example:
     - success = vfs.exists(path)
    """

    return xbmcvfs.exists(path)


def mkdir(path):

    """
    mkdir(path) -- Create a folder.

    path        : folder

    example:
     - success = vfs.mkdir(path)
    """

    return xbmcvfs.mkdir(path)


def rename(source, target):

    """
    rename(file, newFileName) -- Rename file, returns true/false.

    file        : file to reaname
    newFileName : new filename, including the full path

    example:
     - success = vfs.rename(file, newFileName)
    """

    return xbmcvfs.rename(source, target)


def rmdir(path):

    """
    rmdir(path) -- Remove a folder.

    path        : folder

    example:
     - success = vfs.rmdir(path)
    """

    return xbmcvfs.rmdir(path)


def comparepathlists(list1, list2, fullpath=False):

    """
        comparepathlists(list1, list2) -- Compare two lists of paths

        list1 : list, contains paths (local or remote, absolute or relative)
        list2 : list, contains paths (local or remote, absolute or relative)
        fullpath : boolean, set True to compare perform straight comparison of lists
                            set False (default) to compare on filename portions of each list

        returns: dictionary:
            common_items: list, contains paths of items common to both lists
            list1_items: list, contains paths of items found only in list1
            list2_items: list, contains paths of items found only in list2

        example:
         - compare = comparepathlists(list1, list2)
    """

    # initialise dict to store results and temp data
    results = {}
    temp_data = {}

    if fullpath:

        temp_path = lambda x: x

    else:

        temp_path = lambda x: os.path.split(x)[1]

    for path in list1:

        temp_data['list1'].append(temp_path(path))

    for path in list2:

        temp_data['list2'].append(temp_path(path))

    # get items not in list 2
    results['list1_items'] = []
    gen = (i for i, x in enumerate(temp_data['list1']) if not x in temp_data['list2'])
    for i in gen:
        results['list1_items'].append(list1[i])

    # get items not in list 1
    results['list2_items'] = []
    gen = (i for i, x in enumerate(temp_data['list2']) if not x in temp_data['list1'])
    for i in gen:
        results['list2_items'].append(list2[i])

    return results
