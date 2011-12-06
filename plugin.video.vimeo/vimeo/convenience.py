"""
Module providing convenience classes and methods for some basic API procedures.

In general, this module is more rigid than the base module, in that it relies
on some current API behavior (e.g. hard-coding some parameters in the Uploader
class) where the base module chooses to remain ambigous. While this module
shouldn't completely break either until Vimeo seriously changes their API, keep
in mind that if something in this module doesn't work, it still might work the
"conventional" way using just the base module.
"""
from os.path import getsize
from cStringIO import StringIO
from urllib import urlencode

import urllib2
import oauth2

from vimeo import VimeoClient, VimeoError, API_REST_URL
from httplib2wrap import Http

class VimeoUploader(object):
    """
    A convenience uploader class to be used alongside a client.

    The ticket is assumed to be a dict-like object, which means that if you
    aren't using a JSON client the ticket will need to be converted first.
    """
    def __init__(self, vimeo_client, ticket, **kwargs):
        self.vimeo_client = vimeo_client
        self.endpoint = ticket["endpoint"]
        self.ticket_id = ticket["id"]
        self.max_file_size = ticket["max_file_size"]
        self.chunk_id = 0

        self.user = getattr(vimeo_client, "user", None)

        quota = kwargs.pop("quota", {})
        self.has_sd_quota = bool(quota.get("sd_quota", None))
        self.has_hd_quota = bool(quota.get("hd_quota", None))
        self.upload_space = quota.get("upload_space", {})

    def _check_file_size(self, file_size):
        if file_size > self.upload_space.get("free", file_size):
            raise VimeoError("Not enough free space to upload the file.")
        elif file_size > self.max_file_size:
            raise VimeoError("File is larger than the maximum allowed size.")

    def _post_to_endpoint(self, open_file, **kwargs):
        params = {"chunk_id" : self.chunk_id,
                  "ticket_id" : self.ticket_id}

        headers = kwargs.get("headers",
                             dict(self.vimeo_client._CLIENT_HEADERS))

        request = oauth2.Request.from_consumer_and_token(
                                          consumer=self.vimeo_client.consumer,
                                          token=self.vimeo_client.token,
                                          http_method="POST",
                                          http_url=self.endpoint,
                                          parameters=params)

        request.sign_request(self.vimeo_client.signature_method,
                             self.vimeo_client.consumer,
                             self.vimeo_client.token)

        # httplib2 doesn't support uploading out of the box, so use our wrap
        return Http().request_with_files(url=self.endpoint,
                                         method="POST",
                                         body=request,
                                         body_files={"file_data" : open_file},
                                         headers=headers)

    def upload(self, file_path, chunk=False, chunk_size=2*1024*1024,
               chunk_complete_hook=lambda chunk_info : None):
        """
        Performs the steps of an upload. Checks file size and can handle
        splitting into chunks.
        """

        file_size = getsize(file_path)
        self._check_file_size(file_size)

        if chunk:
            video = open(file_path)
            this_chunk = video.read(chunk_size)
            while this_chunk:
                this_chunk = StringIO(this_chunk)
                self._post_to_endpoint(this_chunk)

                chunk_info = {"total_size" : file_size,
                              "chunk_size" : chunk_size,
                              "chunk_id" : self.chunk_id,
                              "file" : file_path}
                chunk_complete_hook(chunk_info)
                self.chunk_id += 1
                this_chunk = video.read(chunk_size)
        else:
            self._post_to_endpoint(open(file_path))
        return self.vimeo_client.vimeo_videos_upload_verifyChunks(
                                                ticket_id=self.ticket_id)

    def complete(self):
        """
        Finish an upload.
        """
        return self.vimeo_client.vimeo_videos_upload_complete(ticket_id=self.ticket_id)