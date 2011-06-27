'''
Created on 3 jun 2011

@author: Nick
'''
import simplejson as json #@UnresolvedImport

from base_parser import BaseParser
from domain.reddit_comment import RedditComment
from json.parser.get_posts_parser import GetPostsParser
from json.result.get_comments_result import GetCommentResult

class GetCommentsParser(BaseParser):
    
    def parse(self, jsonData):
        self.result = GetCommentResult()
        parsedData = json.loads(jsonData)

        if parsedData:
            post = parsedData[0]
            if post and "data" in post:
                data = post["data"]
                if "children" in data:
                    postList = data["children"]
                    self.result.RedditPost = GetPostsParser().parseListPosts(postList)
        
        commentsData = parsedData[1]
        
        if "kind" in commentsData and "data" in commentsData:
            listData = commentsData["data"]
            self.result.modHash = self.getByKey(listData, "modhash")
            self.result.after = self.getByKey(listData, "after")
            self.result.before = self.getByKey(listData, "before")
            
            list = self.getByKey(listData, "children")
            if list is not None:
                for item in list:
                    self.result.data.append(self.parseComment(item))

    def parseComment(self, redditPostData):
        commentData = self.getByKey(redditPostData, "data")
        if commentData is None:
            return None
        
        post = RedditComment()
        
        post.body = self.getByKey(commentData, "body")
        post.body_html = self.getByKey(commentData, "body_html")
        post.parent_id = self.getByKey(commentData, "parent_id")
        post.link_id = self.getByKey(commentData, "link_id")
        post.levenshtein = self.getByKey(commentData, "levenshtein")
        post.subreddit = self.getByKey(commentData, "subreddit")
        post.likes = self.getByKey(commentData, "likes")
        post.id = self.getByKey(commentData, "id")
        post.author = self.getByKey(commentData, "author")
        post.subreddit_id = self.getByKey(commentData, "subreddit_id")
        post.downs = self.getByKey(commentData, "downs")
        post.name = self.getByKey(commentData, "name")
        post.created = self.getByKey(commentData, "created")
        post.created_utc = self.getByKey(commentData, "created_utc")
        post.ups = self.getByKey(commentData, "ups")
        
        subComments = self.getByKey(commentData, "replies")
        if subComments and "kind" in subComments and "data" in subComments:
            listData = subComments["data"]
            
            list = self.getByKey(listData, "children")
            if list is not None:
                for item in list:
                    post.replies.append(self.parseComment(item))

        
        return post
    