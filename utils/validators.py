from email_validator import validate_email as check_email, EmailNotValidError
from datetime import datetime
import re

def validate_email(email: str) -> bool:
    """Validate email format."""
    try:
        check_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone(phone: str) -> bool:
    """
    Validate phone number.
    Accepts various formats, strips non-digits.
    """
    # Simple regex for basic phone validation
    # Allow digits, spaces, dashes, plus sign
    pattern = re.compile(r"^[\d\s\-\+\(\)]+$")
    if not pattern.match(phone):
        return False
    
    # Check if has at least 7 digits
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 7

def validate_future_datetime(dt: datetime) -> bool:
    """Ensure datetime is in the future."""
    return dt > datetime.now()
