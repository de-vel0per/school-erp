from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """lets templates look up a dictionary value by key"""
    return dictionary.get(key)