import unicodedata

from django.contrib import messages
from django.shortcuts import redirect


def is_coordinacion_opd(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        raw_nombre = getattr(sector, 'nombre', '') or ''
        norm = unicodedata.normalize('NFKD', raw_nombre)
        sector_nombre = ''.join(c for c in norm if not unicodedata.combining(c)).lower()
        return 'coordinacion opd' in sector_nombre
    except Exception:
        return False


class CoordinacionOPDWriteBlockMixin:
    redirect_url_name = None

    def dispatch(self, request, *args, **kwargs):
        if is_coordinacion_opd(request.user):
            messages.error(request, 'No tiene permisos para gestionar referencias.')
            target = self.redirect_url_name or 'oficios:institucion_list'
            return redirect(target)
        return super().dispatch(request, *args, **kwargs)


class CoordinacionOPDContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_referencias'] = not is_coordinacion_opd(self.request.user)
        return context
