from django import template

register = template.Library()

@register.filter(name='lookup')
def lookup(dictionary, key):
    """Enable dictionary lookup by variable key in Django templates."""
    return dictionary.get(key) 