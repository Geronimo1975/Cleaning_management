from django import template
from django.utils.safestring import mark_safe
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """Replace or add a GET parameter to the current URL."""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()

@register.filter
def sub(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def stars_display(value):
    """Generate star icons for a rating value."""
    try:
        value = float(value)
        full_stars = int(value)
        half_star = value - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        html = ''
        # Full stars
        for _ in range(full_stars):
            html += '<i class="fas fa-star text-warning"></i>'
        
        # Half star
        if half_star:
            html += '<i class="fas fa-star-half-alt text-warning"></i>'
        
        # Empty stars
        for _ in range(empty_stars):
            html += '<i class="far fa-star text-warning"></i>'
            
        return mark_safe(html)
    except (ValueError, TypeError):
        # Return 5 empty stars if value is invalid
        return mark_safe('<i class="far fa-star text-warning"></i>' * 5)
    
@register.filter
def format_price(value, currency='€'):
    """Format a price with currency symbol."""
    try:
        return f"{currency}{float(value):.2f}"
    except (ValueError, TypeError):
        return f"{currency}0.00"