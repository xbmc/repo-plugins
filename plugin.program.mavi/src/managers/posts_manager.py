'''
Created on 3 jun 2011

@author: Nick
'''
from json.parser.get_posts_parser import GetPostsParser
from json.parser.get_comments_parser import GetCommentsParser

class PostsManager:
    
    _baseUrl = "http://www.reddit.com/"
    _commentsUrl = _baseUrl + "comments/"
    _subRedditUrl = _baseUrl + "r/"
    
    connectionManager = None
    
    def __init__(self, connectionManager):
        self.connectionManager = connectionManager
        
    def getPosts(self, subreddit = None, after = None):
        if subreddit or not subreddit == "":
            url = self._subRedditUrl + subreddit + "/"
        else:
            url = self._baseUrl
            
        url += ".json"
        
        if after:
            url += "?after=" + after
        
        data = self.connectionManager.doRequest(url)
        
        parser = GetPostsParser()
        parser.parse(data)

        return parser.result
    
    def getComments(self, postId):
        data = self.connectionManager.doRequest(self._commentsUrl + postId + ".json")
        
        parser = GetCommentsParser()
        parser.parse(data)

        return parser.result
    