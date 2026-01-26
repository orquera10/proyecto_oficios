import unicodedata

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from .filters import NinoFilter, ParteFilter
from oficios.models import Oficio
from oficios.filters import OficioFilter
from .models import Nino, Parte
from .forms import NinoForm, ParteForm


def _is_coordinacion_opd(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        raw_nombre = getattr(sector, 'nombre', '') or ''
        norm = unicodedata.normalize('NFKD', raw_nombre)
        sector_nombre = ''.join(c for c in norm if not unicodedata.combining(c)).lower()
        return 'coordinacion opd' in sector_nombre
    except Exception:
        return False


class CoordinacionOPDWriteBlockMixin:
    def dispatch(self, request, *args, **kwargs):
        if _is_coordinacion_opd(request.user):
            messages.error(request, 'No tiene permisos para gestionar personas.')
            return redirect('personas:nino_list')
        return super().dispatch(request, *args, **kwargs)


def personas_home(request):
    context = {
        'ninos_url': reverse_lazy('personas:nino_list'),
        'partes_url': reverse_lazy('personas:parte_list'),
        'can_manage_personas': not _is_coordinacion_opd(request.user),
    }
    return render(request, 'personas/home.html', context)

# Vistas para el modelo Nino
class NinoListView(ListView):
    model = Nino
    template_name = 'personas/nino_list.html'
    context_object_name = 'ninos'
    paginate_by = 10
    ordering = ['apellido', 'nombre']

    def get_queryset(self):
        base_qs = super().get_queryset().order_by('apellido', 'nombre')
        self.filterset = NinoFilter(self.request.GET, queryset=base_qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = getattr(self, 'filterset', NinoFilter(self.request.GET, queryset=self.get_queryset()))
        context['can_manage_personas'] = not _is_coordinacion_opd(self.request.user)
        return context

class NinoCreateView(CoordinacionOPDWriteBlockMixin, SuccessMessageMixin, CreateView):
    model = Nino
    form_class = NinoForm
    template_name = 'personas/nino_form.html'
    success_url = reverse_lazy('personas:nino_list')
    success_message = _("El niño ha sido creado exitosamente.")

class NinoUpdateView(CoordinacionOPDWriteBlockMixin, SuccessMessageMixin, UpdateView):
    model = Nino
    form_class = NinoForm
    template_name = 'personas/nino_form.html'
    success_url = reverse_lazy('personas:nino_list')
    success_message = _("El niño ha sido actualizado exitosamente.")

class NinoDetailView(DetailView):
    model = Nino
    template_name = 'personas/nino_detail.html'
    context_object_name = 'nino'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related('casos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener los casos relacionados con el niño
        casos = self.object.casos.all().select_related('usuario').order_by('-creado')
        
        context['casos'] = casos
        
        # Agregar parámetros para la paginación si es necesario
        get_copy = self.request.GET.copy()
        if 'page' in get_copy:
            del get_copy['page']
        context['get_copy'] = get_copy
        context['can_manage_personas'] = not _is_coordinacion_opd(self.request.user)
        
        return context

class NinoDeleteView(CoordinacionOPDWriteBlockMixin, DeleteView):
    model = Nino
    template_name = 'personas/nino_confirm_delete.html'
    success_url = reverse_lazy('personas:nino_list')
    success_message = _("El niño ha sido eliminado exitosamente.")
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

# Vistas para el modelo Parte
class ParteListView(ListView):
    model = Parte
    template_name = 'personas/parte_list.html'
    context_object_name = 'partes'
    paginate_by = 10
    ordering = ['apellido', 'nombre']

    def get_queryset(self):
        base_qs = super().get_queryset().order_by('apellido', 'nombre')
        self.filterset = ParteFilter(self.request.GET, queryset=base_qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = getattr(self, 'filterset', ParteFilter(self.request.GET, queryset=self.get_queryset()))
        context['can_manage_personas'] = not _is_coordinacion_opd(self.request.user)
        return context

class ParteCreateView(CoordinacionOPDWriteBlockMixin, SuccessMessageMixin, CreateView):
    model = Parte
    form_class = ParteForm
    template_name = 'personas/parte_form.html'
    success_url = reverse_lazy('personas:parte_list')
    success_message = _("La parte ha sido creada exitosamente.")

class ParteUpdateView(CoordinacionOPDWriteBlockMixin, SuccessMessageMixin, UpdateView):
    model = Parte
    form_class = ParteForm
    template_name = 'personas/parte_form.html'
    success_url = reverse_lazy('personas:parte_list')
    success_message = _("La parte ha sido actualizada exitosamente.")

class ParteDetailView(DetailView):
    model = Parte
    template_name = 'personas/parte_detail.html'
    context_object_name = 'parte'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related('casos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener los casos relacionados con la parte
        casos = self.object.casos.all().select_related('usuario').order_by('-creado')
        
        context['casos'] = casos
        
        # Agregar parámetros para la paginación si es necesario
        get_copy = self.request.GET.copy()
        if 'page' in get_copy:
            del get_copy['page']
        context['get_copy'] = get_copy
        context['can_manage_personas'] = not _is_coordinacion_opd(self.request.user)
        
        return context

class ParteDeleteView(CoordinacionOPDWriteBlockMixin, DeleteView):
    model = Parte
    template_name = 'personas/parte_confirm_delete.html'
    success_url = reverse_lazy('personas:parte_list')
    success_message = _("La parte ha sido eliminada exitosamente.")
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
