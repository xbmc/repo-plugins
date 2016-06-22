
class RegisterMode:
    def __init__(self, mode):
        self.mode = mode

    def __call__(self, original_function):
        def new_function(*args, **kwargs):
            original_function(*args, **kwargs)

        new_function.mode = self.mode
        return new_function
