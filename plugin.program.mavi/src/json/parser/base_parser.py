class BaseParser:
    result = None
    
    def parse(self, json):
        # This function should be overridden by *ALL* subclasses
        return

    def getByKey(self, postData, key):
        if key in postData:
            return postData[key]
        
        return None