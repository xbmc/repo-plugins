from fivehundredpx       import settings
from fivehundredpx.auth  import *
from fivehundredpx.bind  import bind_api
from fivehundredpx.utils import *

class FiveHundredPXAPI(object):

    def __init__(self,auth_handler=None,host=None,secure=True,version=None,retry_count=None,retry_delay=None,retry_errors=None):
        self.format		  = 'json'
        self.auth_handler = auth_handler
        self.secure 	  = secure
        self.host 		  = host 		or settings.API_HOST
        self.version      = version 	or settings.API_VERSION
        self.retry_count  = retry_count or settings.RETRY_COUNT
        self.retry_delay  = retry_delay or settings.RETRY_DELAY
        self.retry_errors = retry_errors

    photos 		           = bind_api(path='/photos')
    photos_search          = bind_api(path='/photos/search')
    photos_id 	           = bind_api(path='/photos/{id}', allowed_params=['id'])
    photos_post            = bind_api(path='/photos', method='POST', require_auth=True)
    photos_delete          = bind_api(path='/photos/{id}', method='DELETE', allowed_params=['id'],require_auth=True)
    photos_comments        = bind_api(path='/photos/{id}/comments', allowed_params=['id'])
    photos_comments_post   = bind_api(path='/photos/{id}/comments', method='POST', allowed_params=['id'], require_auth=True)
    photos_favorite_post   = bind_api(path='/photos/{id}/favorite', method='POST', allowed_params=['id'], require_auth=True)
    photos_favorite_delete = bind_api(path='/photos/{id}/favorite', method='DELETE', allowed_params=['id'], require_auth=True)
    photos_tags_post       = bind_api(path='/photos/{id}/tags', method='POST', allowed_params=['id'], require_auth=True)
    photos_tags_delete     = bind_api(path='/photos/{id}/tags', method='DELETE', allowed_params=['id'], require_auth=True)
    photos_vote_post       = bind_api(path='/photos/{id}/vote', method='POST', allowed_params=['id'], require_auth=True)

    def upload_photo(self, filename=None,fp=None,file_type=None, **kwargs):
        headers,body = create_body_by_filepath(filename,'file',kwargs) if fp==None else create_body_by_fp(fp, 'file', file_type, kwargs) 
        return bind_api(
            path = '/upload',
            method = 'POST',
            require_auth = True
        )(self,http_body=body, headers=headers)

    def photos_update(self, id, **kwargs):
        headers,body = create_body(kwargs)
        return bind_api(
            path='/photos/{id}',
            method = 'PUT',
            allowed_params=['id'],
            require_auth = True
        )(self,id=id, http_body=body, headers=headers)

    users                = bind_api(path='/users', require_auth=True)
    users_show           = bind_api(path='/users/show')
    users_friends        = bind_api(path='/users/{id}/friends', allowed_params=['id'])
    users_followers      = bind_api(path='/users/{id}/followers', allowed_params=['id'])
    users_friends_post   = bind_api(path='/users/{id}/friends', method='POST', allowed_params=['id'])
    users_friends_delete = bind_api(path='/users/{id}/friends', method='DELETE', allowed_params=['id'])

    blogs               = bind_api(path='/blogs')
    blogs_id            = bind_api(path='/blogs/{id}', allowed_params=['id'])
    blogs_comments      = bind_api(path='/blogs/{id}/comments', allowed_params=['id'])
    blogs_comments_post = bind_api(path='/blogs/{id}/comments', require_auth=True, allowed_params=['id'], method='POST')
    blogs_post          = bind_api(path='/blogs', require_auth=True, method='POST')
    blogs_delete        = bind_api(path='/blogs/{id}', require_auth=True, allowed_params=['id'], method='DELETE')

    def blogs_update(self, id, **kwargs):
        headers,body = create_body(kwargs)
        return bind_api(
            path='/blogs/{id}',
            method = 'PUT',
            allowed_params=['id'],
            require_auth = True
        )(self,id=id, http_body=body, headers=headers)

    collections        = bind_api(path='/collections')
    collections_id     = bind_api(path='/collections/{id}', allowed_params=['id'])
    collections_post   = bind_api(path='/collections', require_auth=True, method='POST')
    collections_update = bind_api(path='/collections/{id}', require_auth=True, method='POST', allowed_params=['id'])
    collections_delete = bind_api(path='/collections/{id}', require_auth=True, method='DELETE', allowed_params=['id'])
