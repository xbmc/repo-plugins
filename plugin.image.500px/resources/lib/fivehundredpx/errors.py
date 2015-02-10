class FiveHundredClientError(Exception):

    def __init__(self,error_message,status=None):
        self.error_message = error_message	
        self.status = status	

    def __str__(self):
        return self.error_message
