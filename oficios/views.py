from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, F

from .models import (
    Oficio, Institucion, Caratula, Juzgado
)
from personas.models import Nino
from .forms import OficioForm
from .filters import OficioFilter


def buscar_ninos(request):
    """
    Vista para buscar niños por nombre, apellido o documento.
    Devuelve resultados en formato JSON para ser usados en autocompletado.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Buscar por nombre, apellido o documento
    ninos = Nino.objects.filter(
        Q(nombres__icontains=query) |
        Q(apellidos__icontains=query) |
        Q(documento_identidad__icontains=query)
    ).distinct()[:10]  # Limitar a 10 resultados
    
    # Preparar los datos para la respuesta JSON
    results = [{
        'id': nino.id,
        'nombres': nino.nombres,
        'apellidos': nino.apellidos,
        'documento_identidad': nino.documento_identidad or '',
        'fecha_nacimiento': nino.fecha_nacimiento.strftime('%d/%m/%Y') if nino.fecha_nacimiento else ''
    } for nino in ninos]
    
    return JsonResponse(results, safe=False)

# Vista de listado de oficios
class OficioListView(LoginRequiredMixin, ListView):
    model = Oficio
    template_name = 'oficios/oficio_list.html'
    context_object_name = 'oficios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = OficioFilter(self.request.GET, queryset=queryset)
        # Orden por fecha de vencimiento ascendente (nulos al final), luego por emisión desc
        return (
            self.filterset.qs
            .select_related('institucion', 'juzgado', 'usuario')
            .order_by(F('fecha_vencimiento').asc(nulls_last=True), '-fecha_emision')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['filter'] = getattr(self, 'filterset', OficioFilter(queryset=self.get_queryset()))
        return context


class OficioEstadoListView(LoginRequiredMixin, ListView):
    model = Oficio
    template_name = 'oficios/oficio_list.html'
    context_object_name = 'oficios'
    paginate_by = 20

    def get_queryset(self):
        estado = self.kwargs.get('estado')
        base_qs = Oficio.objects.select_related('institucion', 'juzgado', 'usuario').filter(estado=estado)
        # Aplicar filtros enviados por GET sobre el queryset ya filtrado por estado
        self.filterset = OficioFilter(self.request.GET, queryset=base_qs)
        return self.filterset.qs.order_by(F('fecha_vencimiento').asc(nulls_last=True), '-fecha_emision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        # Reusar el mismo formulario de filtros, mostrando el filterset aplicado
        estado = self.kwargs.get('estado')
        context['filter'] = getattr(self, 'filterset', OficioFilter(self.request.GET, queryset=self.get_queryset()))
        context['estado_actual'] = estado
        return context

class OficioCreateView(LoginRequiredMixin, CreateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        caso_id = self.request.GET.get('caso')
        if caso_id:
            initial['caso'] = caso_id
        return initial
    
    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def form_valid(self, form):
        # Guardar el oficio
        self.object = form.save(commit=False)
        self.object.usuario = self.request.user
        self.object.save()
        messages.success(self.request, 'El oficio se ha creado correctamente.')
        return super().form_valid(form)


class OficioDetailView(LoginRequiredMixin, DetailView):
    model = Oficio
    template_name = 'oficios/oficio_detail.html'
    context_object_name = 'oficio'
    
    def get_queryset(self):
        return super().get_queryset().select_related('institucion', 'juzgado', 'usuario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar la fecha actual para comparar con la fecha de vencimiento
        from django.utils import timezone
        context['now'] = timezone.now()
        
        return context


class OficioUpdateView(LoginRequiredMixin, UpdateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    
    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'El oficio se ha guardado correctamente.')
        return super().form_valid(form)

        messages.success(self.request, 'El oficio se ha actualizado correctamente.')
        return super().form_valid(form)


class OficioDeleteView(LoginRequiredMixin, DeleteView):
    model = Oficio
    template_name = 'oficios/oficio_confirm_delete.html'
    success_url = reverse_lazy('oficios:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'El oficio se ha eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
