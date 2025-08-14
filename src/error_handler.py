class TokenValidationError(Exception):
    """Custom exception for token validation errors."""
    pass

class MissingPermissionError(TokenValidationError):
    """Raised when a token is missing a required permission."""
    def __init__(self, permission):
        self.permission = permission
        super().__init__(f"Token is missing required permission: {permission}")
