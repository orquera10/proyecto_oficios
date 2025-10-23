from django import template

register = template.Library()

@register.filter(name='estado_badge_class')
def estado_badge_class(estado):
    """
    Returns the appropriate Bootstrap badge class for a given estado.
    """
    estado_map = {
        'ABIERTO': 'primary',
        'EN_PROCESO': 'warning',
        'CERRADO': 'success',
    }
    return estado_map.get(estado, 'secondary')
