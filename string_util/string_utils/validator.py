import re
from email_validator import validate_email, EmailNotValidError

def is_valid_email (email:str) -> bool:
    """Check if the string is a valid email address."""
    try:
        validate_email(email)
        return True
    except:
        EmailNotValidError
        return False

def valid_contact (contact: str) -> bool:
    """Check if the string is a valid phone number (digits, optional +)."""
    pattern =  r'^\+?\d{7,15}$'
    return re.match(pattern, contact) is not None

def valid_username (alias: str) -> bool:
    """Check if the username is 3–15 chars, only letters/numbers/underscores."""
    pattern =  r'^\w{3,15}$'
    return re.match(pattern, alias) is not None

def is_strong_password(password: str) -> bool:
    """Check password strength: at least 8 chars, one uppercase, one number, one symbol."""
    pattern = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return re.match(pattern, password) is not None