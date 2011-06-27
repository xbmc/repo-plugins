'''
Created on 3 jun 2011

@author: Nick
'''
import simplejson as json #@UnresolvedImport

from base_parser import BaseParser
from domain.reddit_post import RedditPost
from json.result.get_posts_result import GetPostsResult

class GetPostsParser(BaseParser):
    
    def parse(self, jsonData):
        self.result = GetPostsResult()
        parsedData = json.loads(jsonData)
        
        if "kind" in parsedData and "data" in parsedData:
            listData = parsedData["data"]
            self.result.modHash = self.getByKey(listData, "modhash")
            self.result.after = self.getByKey(listData, "after")
            self.result.before = self.getByKey(listData, "before")
            self.result.data = self.parseListPosts(self.getByKey(listData, "children"))

    def parseListPosts(self, jsonPostList):
        postList = list()
        if jsonPostList:
            for item in jsonPostList:
                postList.append(self.parsePost(item))

        return postList

    def parsePost(self, redditPostData):
        post = RedditPost()
        
        post.kind = self.getByKey(redditPostData, "kind")
        
        postData = self.getByKey(redditPostData, "data")
        if postData is None:
            return None
        
        
        post.domain = self.getByKey(postData, "domain")
        post.levenshtein = self.getByKey(postData, "levenshtein")
        post.subreddit = self.getByKey(postData, "subreddit")
        post.selfText_html = self.getByKey(postData, "selfText_html")
        post.selfText = self.getByKey(postData, "selfText")
        post.likes = self.getByKey(postData, "likes")
        post.saved = self.getByKey(postData, "saved")
        post.id = self.getByKey(postData, "id")
        post.clicked = self.getByKey(postData, "clicked")
        post.author = self.getByKey(postData, "author")
        post.media = self.getByKey(postData, "media")
        post.score = self.getByKey(postData, "score")
        post.over_18 = self.getByKey(postData, "over_18")
        post.hidden = self.getByKey(postData, "hidden")
        post.thumbnail = self.getByKey(postData, "thumbnail")
        post.subreddit_id = self.getByKey(postData, "subreddit_id")
        post.downs = self.getByKey(postData, "downs")
        post.is_self = self.getByKey(postData, "is_self")
        post.permalink = self.getByKey(postData, "permalink")
        post.name = self.getByKey(postData, "name")
        post.created = self.getByKey(postData, "created")
        post.url = self.getByKey(postData, "url")
        post.title = self.getByKey(postData, "title")
        post.created_utc = self.getByKey(postData, "created_utc")
        post.num_comment = self.getByKey(postData, "num_comments")
        post.ups = self.getByKey(postData, "ups")
        
        return post
    