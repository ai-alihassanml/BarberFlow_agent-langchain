from datetime import datetime, timedelta
from dateutil import parser
from typing import Optional

def parse_natural_datetime(text: str) -> Optional[datetime]:
    """
    Parse natural language time expressions.
    This is a simplified version - in production we might use a more robust NLP parser
    or rely on the LLM to extract ISO strings.
    """
    try:
        # Basic parsing using dateutil
        dt = parser.parse(text, fuzzy=True)
        
        # If the parsed time is in the past, assume it's for tomorrow/next occurrence
        # unless specific date was given. This is a heuristic.
        if dt < datetime.now():
            # If it's just a time "3pm", dateutil defaults to today. 
            # If today 3pm passed, user probably means tomorrow.
            if dt.date() == datetime.now().date():
                dt = dt + timedelta(days=1)
                
        return dt
    except Exception:
        return None

def format_datetime_friendly(dt: datetime) -> str:
    """Format datetime in human-readable way."""
    return dt.strftime("%b %d, %Y at %I:%M %p")

def get_day_name(dt: datetime) -> str:
    """Get lowercase day name (monday, tuesday, etc)."""
    return dt.strftime("%A").lower()

# a fuction that return current date and time
def get_current_date_and_time() -> datetime:
    """Get current date and time."""
    return datetime.now()
