from resources.lib import tor

class TorList:
    
    
    
    def __init__(self):
        self.posts = []
        self.time = 0
    
    
    def add_post(self, post):
        self.posts.append(post)
        self.posts = sorted(self.posts, key=lambda TorPost: TorPost.item.published, reverse=True)
    
    def get_post_list(self):
        '''
        result = []
        for post in self.posts:
            result.append(post.item.title)
        return result
        '''
        return self.posts
    
    def serialize(self):
        posts = []
        for post in self.posts:
            posts.append( post.serialize())
            
        output = {
            "time": self.time,
            "posts" : posts
        }
        
        return repr(output)
    
    def unserialize(self, object):
        self.time = object["time"]
        for oPost in object["posts"]:
            post = TorPost(None)
            post.unserialize(oPost)
            self.add_post(post)
            
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['posts']
        return d
    
    def __setstate__(self, d):
        self.__dict__.update(d)

class TorPost:
    
    def __init__(self, item):
        self.item = item

        
    def __getstate__(self):
        d = dict(self.__dict__)
        #del d['_logger']
        return d
    
    def __setstate__(self, d):
        self.__dict__.update(d)
        
    def serialize(self):
        
        output = {
            "item":{
                "item_id": self.item.item_id,
                "title" : self.item.title,
                "content" : self.item.content,
                "href" : self.item.href,
                "mediaUrl" : self.item.mediaUrl,
                "source" : self.item.source,
                "source_id" : self.item.source_id,
                "published": self.item.published
            }
        }
        return output
    
    def unserialize(self, object):
        self.item = tor.Item(None, object["item"]["item_id"])
        self.item.title = object["item"]["title"]
        self.item.content = object["item"]["content"]
        self.item.href = object["item"]["href"]
        self.item.mediaUrl = object["item"]["mediaUrl"]
        self.item.source = object["item"]["source"]
        self.item.source_id = object["item"]["source_id"]
        self.item.published = object["item"]["published"]
        
        