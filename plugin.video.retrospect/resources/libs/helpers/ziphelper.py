#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import io
import shutil
import zipfile

from logger import Logger


class ZipHelper(object):
    def __init__(self):
        pass

    @staticmethod
    def unzip(path, destination):
        """ Unzips a file <path> to the folder <destination>

        @param path:        The path to the zipfile
        @param destination: The folder ot extract to

        """

        zip_file = None
        try:
            zip_file = zipfile.ZipFile(path)

            # now extract
            first = True
            Logger.debug("Extracting %s to %s", path, destination)
            for name in zip_file.namelist():
                if first:
                    folder = os.path.split(name)[0]
                    if os.path.exists(os.path.join(destination, folder)):
                        shutil.rmtree(os.path.join(destination, folder))
                    first = False

                if not name.endswith("/") and not name.endswith("\\"):
                    file_name = os.path.join(destination, name)
                    path = os.path.dirname(file_name)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    Logger.debug("Extracting %s", file_name)
                    with io.open(file_name, 'wb') as outfile:
                        outfile.write(zip_file.read(name))
        except zipfile.BadZipfile:
            Logger.error("Invalid zipfile: %s", path, exc_info=True)
            if os.path.isfile(path):
                os.remove(path)
        except:
            Logger.error("Error extracting file: %s", path, exc_info=True)
        finally:
            if zip_file:
                Logger.debug("Closing zipfile: %s", path)
                zip_file.close()
