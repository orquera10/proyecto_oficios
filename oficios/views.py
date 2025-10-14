from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.db.models import Q

from .models import (
    Oficio, Institucion, Caratula, CaratulaOficio, Juzgado,
    OficioNino, OficioParte, Nino
)
from .forms import OficioForm, OficioNinoFormSet, OficioParteFormSet
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
        return self.filterset.qs.select_related('institucion', 'juzgado', 'usuario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['filter'] = getattr(self, 'filterset', OficioFilter(queryset=self.get_queryset()))
        return context


class OficioCreateView(LoginRequiredMixin, CreateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    
    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['nino_formset'] = OficioNinoFormSet(self.request.POST, prefix='nino')
            context['parte_formset'] = OficioParteFormSet(self.request.POST, prefix='parte')
        else:
            context['nino_formset'] = OficioNinoFormSet(prefix='nino')
            context['parte_formset'] = OficioParteFormSet(prefix='parte')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        nino_formset = context['nino_formset']
        parte_formset = context['parte_formset']
        
        if nino_formset.is_valid() and parte_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.usuario = self.request.user
            self.object.save()
            
            nino_formset.instance = self.object
            nino_formset.save()
            
            parte_formset.instance = self.object
            parte_formset.save()
            
            messages.success(self.request, 'El oficio se ha creado exitosamente.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OficioDetailView(LoginRequiredMixin, DetailView):
    model = Oficio
    template_name = 'oficios/oficio_detail.html'
    context_object_name = 'oficio'
    
    def get_queryset(self):
        return super().get_queryset().select_related('institucion', 'juzgado', 'usuario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oficio = self.get_object()
        
        # Obtener los niños relacionados con sus observaciones
        context['ninos'] = oficio.oficio_ninos.select_related('nino').all()
        
        # Obtener las partes relacionadas con sus observaciones
        context['partes'] = oficio.oficio_partes.select_related('parte').all()
        
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['nino_formset'] = OficioNinoFormSet(self.request.POST, instance=self.object, prefix='nino')
            context['parte_formset'] = OficioParteFormSet(self.request.POST, instance=self.object, prefix='parte')
        else:
            context['nino_formset'] = OficioNinoFormSet(instance=self.object, prefix='nino')
            context['parte_formset'] = OficioParteFormSet(instance=self.object, prefix='parte')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        nino_formset = context['nino_formset']
        parte_formset = context['parte_formset']
        
        if nino_formset.is_valid() and parte_formset.is_valid():
            self.object = form.save()
            nino_formset.save()
            parte_formset.save()
            messages.success(self.request, 'El oficio se ha actualizado exitosamente.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OficioDeleteView(LoginRequiredMixin, DeleteView):
    model = Oficio
    template_name = 'oficios/oficio_confirm_delete.html'
    success_url = reverse_lazy('oficios:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'El oficio se ha eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
