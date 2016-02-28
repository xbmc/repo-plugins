from fivehundredpx       import settings
from fivehundredpx.auth  import *
from fivehundredpx.bind  import bind_api
from fivehundredpx.utils import FileUtil

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

    #### Photo API
    # https://github.com/500px/api-documentation/tree/master/endpoints/photo
    photos 		           = bind_api(path='/photos')
    photos_search          = bind_api(path='/photos/search')
    photos_id 	           = bind_api(path='/photos/{id}', allowed_params=['id'])
    photos_post            = bind_api(path='/photos', method='POST', require_auth=True)
    photos_update          = bind_api(path='/photos/{id}', method='PUT', require_auth=True, as_query=False)
    photos_delete          = bind_api(path='/photos/{id}', method='DELETE', allowed_params=['id'],require_auth=True)
    photos_comments        = bind_api(path='/photos/{id}/comments', allowed_params=['id'])
    photos_comments_post   = bind_api(path='/photos/{id}/comments', method='POST', allowed_params=['id'], require_auth=True)
    photos_favorites       = bind_api(path='/photos/{id}/favorites', allowed_params=['id'], require_auth=True)
    photos_favorite_post   = bind_api(path='/photos/{id}/favorite', method='POST', allowed_params=['id'], require_auth=True)
    photos_favorite_delete = bind_api(path='/photos/{id}/favorite', method='DELETE', allowed_params=['id'], require_auth=True)
    photos_tags_post       = bind_api(path='/photos/{id}/tags', method='POST', allowed_params=['id'], require_auth=True)
    photos_tags_delete     = bind_api(path='/photos/{id}/tags', method='DELETE', allowed_params=['id'], require_auth=True, as_query=True)
    photos_votes           = bind_api(path='/photos/{id}/votes', allowed_params=['id'], require_auth=True)
    photos_vote_post       = bind_api(path='/photos/{id}/vote', method='POST', allowed_params=['id'], require_auth=True, as_query=True)
    photos_report          = bind_api(path='/photos/{id}/report', method='POST', allowed_params=['id'], require_auth=True)

    def upload_photo(self, filename=None,fp=None,file_type=None, **kwargs):
        headers,body = FileUtil.create_body_by_filepath(filename,'file',kwargs) if fp==None else FileUtil.create_body_by_fp(fp, 'file', file_type, kwargs) 
        return bind_api(
            path = '/upload',
            method = 'POST'
        )(self,http_body=body, headers=headers)

    #### User API
    # https://github.com/500px/api-documentation/tree/master/endpoints/user
    users                = bind_api(path='/users', require_auth=True)
    users_show           = bind_api(path='/users/show')
    users_search         = bind_api(path='/users/search')
    users_friends        = bind_api(path='/users/{id}/friends', allowed_params=['id'])
    users_followers      = bind_api(path='/users/{id}/followers', allowed_params=['id'])
    users_friends_post   = bind_api(path='/users/{id}/friends', method='POST', allowed_params=['id'])
    users_friends_delete = bind_api(path='/users/{id}/friends', method='DELETE', allowed_params=['id'])

    #### Blog API
    # https://github.com/500px/api-documentation/tree/master/endpoints/blog
    blogs               = bind_api(path='/blogs')
    blogs_id            = bind_api(path='/blogs/{id}', allowed_params=['id'])
    blogs_comments      = bind_api(path='/blogs/{id}/comments', allowed_params=['id'])
    blogs_comments_post = bind_api(path='/blogs/{id}/comments', require_auth=True, allowed_params=['id'], method='POST')
    blogs_post          = bind_api(path='/blogs', require_auth=True, method='POST')
    blogs_update        = bind_api(path='/blogs/{id}', require_auth=True, allowed_params=['id'], method='PUT')
    blogs_delete        = bind_api(path='/blogs/{id}', require_auth=True, allowed_params=['id'], method='DELETE')
    
    #### Comment API
    # https://github.com/500px/api-documentation/tree/master/endpoints/comments
    comments_post = bind_api(path='/comments/{id}/comments', require_auth=True, allowed_params=['id'], method='POST')

    #### Collection API
    # https://github.com/500px/api-documentation/tree/master/endpoints/collections
    collections        = bind_api(path='/collections', require_auth=True)
    collections_id     = bind_api(path='/collections/{id}', require_auth=True, allowed_params=['id'])
    collections_post   = bind_api(path='/collections', require_auth=True, method='POST', as_query=True)
    collections_update = bind_api(path='/collections/{id}', require_auth=True, method='PUT', allowed_params=['id'], as_query=True)
    collections_delete = bind_api(path='/collections/{id}', require_auth=True, method='DELETE', allowed_params=['id'], as_query=True)

    #### Galleries API
    # https://github.com/500px/api-documentation/blob/master/endpoints/galleries
    galleries    = bind_api(path='/users/{user_id}/galleries', allowed_params=['user_id'])
    galleries_id = bind_api(path='/users/{user_id}/galleries/{id}', allowed_params=['user_id', 'id'])
    galleries_id_items = bind_api(path='/users/{user_id}/galleries/{id}/items', allowed_params=['user_id', 'id'])
    # galleries_id_share_url = bind_api(path='/users/{user_id}/galleries/{id}/share_url', require_auth=True, allowed_params=['user_id', 'id'])
    # galleries_post = bind_api(path='/users/{user_id}/galleries', require_auth=True, method='POST', allowed_params=['user_id'], as_query=True)
    # galleries_id_update = None
    # galleries_id_items_update = None 
    # galleries_id_reposition_update = None
    # galleries_id_delete = None

