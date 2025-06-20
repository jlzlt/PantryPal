from django import template

register = template.Library()

@register.filter
def floatval(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0 

@register.filter
def star_fill_percents(rating, total=5):
    """
    Returns a list of fill percentages (1.0 = full, 0.0 = empty, 0.2 = 20% filled, etc.) for each star.
    """
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        rating = 0
    fills = []
    for i in range(1, total + 1):
        if rating >= i:
            fills.append(1.0)
        elif rating > i - 1:
            fills.append(round(rating - (i - 1), 2))
        else:
            fills.append(0.0)
    return fills 

@register.filter
def mul(value, arg):
    """Multiply the arg and the value."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 

@register.filter
def dict_get(d, key):
    return d.get(key, 0) 