

class Channel():
    id = ''
    title = ''
    filterList = []
    categoryList = []
    type = ''
    
    def __init__(self,id, title,filter,category):
        self.id = id
        self.title = title
        self.filterList = filter
        self.categoryList = category
        self.type = type
