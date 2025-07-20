from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='lookup')
def lookup(dictionary, key):
    """Enable dictionary lookup by variable key in Django templates."""
    return dictionary.get(key)

@register.filter(name='get_status_display_from_value')
def get_status_display_from_value(status_value, status_choices):
    """ 
    Looks up the display name for a status value from a list of choices.
    status_choices is expected to be a list of (value, display_name) tuples.
    Returns the display_name if found, otherwise the original status_value.
    """
    if not status_choices:
        return status_value # Return original value if choices are not provided
    for value, display_name in status_choices:
        if value == status_value:
            return display_name
    return status_value # Fallback to original value if not found

@register.filter(name='highlight_keywords')
def highlight_keywords(text, keywords_string):
    if not text or not keywords_string:
        return text
    
    keywords = [kw.strip() for kw in keywords_string.split(',') if kw.strip()]
    highlighted_text = text
    for keyword in keywords:
        # Use regex to find whole words, case-insensitive
        # The re.escape is important if keywords might contain special regex characters
        pattern = r'\b(' + re.escape(keyword) + r')\b'
        highlighted_text = re.sub(pattern, r'<mark>\1</mark>', highlighted_text, flags=re.IGNORECASE)
        
    return mark_safe(highlighted_text)

@register.filter(name='get_insights_list')
def get_insights_list(insights_str):
    if not insights_str or insights_str == 'N/A':
        return []
    # Split by '* ', then filter out empty strings that might result from splitting
    return [item.strip() for item in insights_str.split('* ') if item.strip()] 

@register.simple_tag
def get_recent_sessions(user, count=5):
    """
    Retrieves the most recent 'count' match sessions for a given user.
    """
    if not user.is_authenticated:
        return []
    
    from ..models import MatchSession
    return MatchSession.objects.filter(user=user).order_by('-matched_at')[:count] 