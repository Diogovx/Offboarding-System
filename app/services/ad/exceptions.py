from fastapi import HTTPException, status


class ADServiceError(Exception):
    """Basic error for AD service."""
    pass


class ADConnectionError(ADServiceError):
    """Connection error with AD"""
    pass


class UserNotFoundError(HTTPException):
    """User not found in AD"""
    def __init__(self, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {identifier}"
        )


class MultipleUsersFoundError(HTTPException):
    """Multiple users found"""
    def __init__(self, identifier: str, count: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{count} users found with identifier '{identifier}'. "
                   "Refine your search to get a unique result."
        )


class ADOperationError(HTTPException):
    """Error executing operation in AD."""
    def __init__(self, operation: str, details: str | None = None):
        detail = f"Ffailed to execute operation: {operation}"
        if details:
            detail += f". Details: {details}"

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class InvalidInputError(HTTPException):
    """Invalid Input"""
    def __init__(self, field: str, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field '{field}': {reason}"
        )
