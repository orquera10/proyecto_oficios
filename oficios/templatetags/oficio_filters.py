from django import template

register = template.Library()

@register.filter(name='estado_badge_class')
def estado_badge_class(estado):
    """Devuelve la clase de Bootstrap para el badge de estado."""
    estado_map = {
        'cargado': 'secondary',      # gris claro
        'asignado': 'warning',       # naranja
        'respondido': 'primary',     # azul
        'enviado': 'success',        # verde
        'devuelto': 'violet',        # violeta (custom)
    }
    return estado_map.get(estado, 'light')
