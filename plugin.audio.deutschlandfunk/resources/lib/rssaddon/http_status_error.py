class HttpStatusError(Exception):

    message = ""

    def __init__(self, msg):

        self.message = msg