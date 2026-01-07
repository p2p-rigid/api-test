class UserNotFoundException(Exception):
    """Raised when a user is not found"""
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class UserAlreadyExistsException(Exception):
    """Raised when trying to create a user that already exists"""
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"User with {field}='{value}' already exists")
