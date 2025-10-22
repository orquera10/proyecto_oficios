from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .filters import NinoFilter
from oficios.models import Oficio
from oficios.filters import OficioFilter
from .models import Nino, Parte
from .forms import NinoForm, ParteForm

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
        return context

class NinoCreateView(SuccessMessageMixin, CreateView):
    model = Nino
    form_class = NinoForm
    template_name = 'personas/nino_form.html'
    success_url = reverse_lazy('personas:nino_list')
    success_message = _("El niño ha sido creado exitosamente.")

class NinoUpdateView(SuccessMessageMixin, UpdateView):
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
        
        return context

class NinoDeleteView(DeleteView):
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

class ParteCreateView(SuccessMessageMixin, CreateView):
    model = Parte
    form_class = ParteForm
    template_name = 'personas/parte_form.html'
    success_url = reverse_lazy('personas:parte_list')
    success_message = _("La parte ha sido creada exitosamente.")

class ParteUpdateView(SuccessMessageMixin, UpdateView):
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
        
        return context

class ParteDeleteView(DeleteView):
    model = Parte
    template_name = 'personas/parte_confirm_delete.html'
    success_url = reverse_lazy('personas:parte_list')
    success_message = _("La parte ha sido eliminada exitosamente.")
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
