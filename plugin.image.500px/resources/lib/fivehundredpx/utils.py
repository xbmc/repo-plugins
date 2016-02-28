from fivehundredpx.settings import *
from fivehundredpx.errors   import *
import os, mimetypes
import urllib

class Util(object):
    @staticmethod
    def replace_space(value):
        return str(value).replace(" ", "+")

    @staticmethod
    def encode_string(value):
        return value.encode('utf-8') if isinstance(value,unicode) else str(value)

class FileUtil(object):
    @staticmethod
    def create_body_by_filepath(filepath,name,parameters):
        file_type = mimetypes.guess_type(filepath)
        if file_type[0] not in ALLOWED_FILE_TYPES:
            raise FiveHundredsClientError('Invalid file type for image: %s' % file_type[0])

        fp = open(filepath,'rb')
        headers,body = FileUtil._create_body(fp,name,file_type[0],parameters)
        fp.close()
        return headers,body

    @staticmethod
    def create_body_by_fp(fp,name,file_type,parameters):
        if file_type not in ALLOWED_FILE_TYPES:
            raise FiveHundredsClientError('Invalid file type for image: %s' % file_type)
        return FileUtil._create_body(fp, name, file_type, parameters)

    @staticmethod
    def _create_body(fp,name,filetype,parameters):
        BOUNDARY = 'fsdeklzzpo4oopsp'
        body = []
        body.append('--' +  BOUNDARY)
        for key,value in parameters.iteritems():
            body.append('Content-Disposition: form-data; name="%s"' % key )
            body.append('')
            body.append(str(value))
            body.append('--' + BOUNDARY)
            body.append('')

        body.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (name,name) )
        body.append('Content-Type: %s' % filetype)
        body.append('')
        body.append(fp.read())
        body.append('--' + BOUNDARY + '--')
        body.append('')
        body = '\r\n'.join(body)

        headers = {
            'Content-Type' : 'multipart/form-data; boundary=%s' % BOUNDARY,
            'Content-Length' : str(len(body))
        }
        return headers,body

    @staticmethod
    def create_body(parameters):
        BOUNDARY = 'fsdeklzzpo4oopsp'
        body = []
        for key,value in parameters.iteritems():
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="%s"' % key )
            body.append('')
            body.append(str(value))      
            body.append('')

        body.append('--' + BOUNDARY + '--')
        body = '\r\n'.join(body)
        headers = {
            'Content-Type' : 'multipart/form-data; boundary=%s' % BOUNDARY,
            'Content-Length' : str(len(body))
        }
        return headers,body