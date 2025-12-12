"""
Application-wide constants.
"""

# Cookie names
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
ACCESS_TOKEN_COOKIE_NAME = "access_token"

# HTTP Headers
AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer"

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Error messages
ERROR_MISSING_AUTH_HEADER = "Missing Authorization header"
ERROR_INVALID_AUTH_SCHEME = "Invalid Authorization scheme"
ERROR_INVALID_TOKEN = "Invalid or expired token"
ERROR_USER_NOT_FOUND = "User not found"

# Response messages
MSG_LOGIN_SUCCESS = "Login successful"
MSG_LOGOUT_SUCCESS = "Logged out successfully"
MSG_TOKEN_REFRESHED = "Token refreshed successfully"
MSG_UNAUTHORIZED = "Unauthorized access"

# Database constraints
MAX_EMAIL_LENGTH = 255
MAX_NAME_LENGTH = 100
MAX_URL_LENGTH = 500
MAX_TOKEN_LENGTH = 1024

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100