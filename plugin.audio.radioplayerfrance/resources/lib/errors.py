class ApiError(Exception):
    """Raised when the Radioplayer API fails."""
    pass

class NavigationError(Exception):
    """Raised when the navigation layer detects a problem."""
    pass
