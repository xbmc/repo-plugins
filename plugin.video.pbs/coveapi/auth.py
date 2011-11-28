"""Module: `coveapi.auth`
Authorization classes for signing COVE API requests.
"""
import hmac
try:
    from hashlib import sha1
except ImportError:
    import sha as sha1
import time
from base64 import urlsafe_b64encode
from os import urandom


class PBSAuthorization(object):
    """Authorization class for signing COVE API requests.
    
    Keyword arguments:
    `api_app_id` -- your COVE API app id
    `api_app_secret` -- your COVE API secret key

    Returns:
    `coveapi.auth.PBSAuthorization` instance
    """
    def __init__(self, api_app_id, api_app_secret):
        self.api_app_id = api_app_id
        self.api_app_secret = api_app_secret
    
    
    def sign_request(self, request):
        """Sign request per PBSAuth specifications.
            
        Keyword arguments:
        `request` -- instance of `urllib2.Request`
            
        Returns:
        instance of `urllib2.Request` (signed)
        """
        timestamp = str(time.time())
        nonce = urlsafe_b64encode(urandom(32)).strip("=")
        
        query = request.get_full_url()
        to_be_signed = 'GET%s%s%s%s' % (query, timestamp,
                                        self.api_app_id, nonce)
        signature = hmac.new(self.api_app_secret.encode('utf-8'),
                             to_be_signed.encode('utf-8'),
                             sha1).hexdigest()
        
        request.add_header('X-PBSAuth-Timestamp', timestamp)
        request.add_header('X-PBSAuth-Consumer-Key', self.api_app_id)
        request.add_header('X-PBSAuth-Signature', signature)
        request.add_header('X-PBSAuth-Nonce', nonce)
    
        return request
