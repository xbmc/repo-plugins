from domain.reddit_post import RedditPost

class GetCommentResult:
    RedditPost = None
    
    modHash = None
    data = list()
    after = None
    before = None
    
    
    def isValid(self):
#        TODO
        return