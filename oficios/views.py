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
            context['parte_formset'] = OficioParteFormSet(self.request.POST, prefix='partes')
        else:
            context['parte_formset'] = OficioParteFormSet(prefix='partes')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        parte_formset_post = context['parte_formset']

        # Validar formulario principal por las dudas
        if not form.is_valid():
            return self.form_invalid(form)

        # Guardar el oficio primero para tener instancia
        self.object = form.save(commit=False)
        self.object.usuario = self.request.user
        self.object.save()

        # Re-instanciar formset con la instancia recién creada
        parte_formset = OficioParteFormSet(self.request.POST, instance=self.object, prefix='partes')

        if parte_formset.is_valid():
            parte_formset.save()

            # Manejar niños seleccionados desde el campo oculto
            ninos_ids_str = self.request.POST.get('ninos_seleccionados', '').strip()
            if ninos_ids_str:
                try:
                    ninos_ids = [int(x) for x in ninos_ids_str.split(',') if x]
                except ValueError:
                    ninos_ids = []
                for nino_id in ninos_ids:
                    try:
                        nino_obj = Nino.objects.get(pk=nino_id)
                        OficioNino.objects.get_or_create(oficio=self.object, nino=nino_obj)
                    except Nino.DoesNotExist:
                        continue

            messages.success(self.request, 'El oficio se ha creado exitosamente.')
            return super().form_valid(form)
        else:
            # Mostrar errores de partes
            for i, error in enumerate(parte_formset.errors):
                if error:
                    for field, errors in error.items():
                        for error_msg in errors:
                            messages.error(self.request, f'Error en parte {i+1} - {field}: {error_msg}')
            return self.form_invalid(form)


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
            context['parte_formset'] = OficioParteFormSet(self.request.POST, instance=self.object, prefix='partes')
        else:
            context['parte_formset'] = OficioParteFormSet(instance=self.object, prefix='partes')
            # Proveer IDs de niños seleccionados para prellenar en el front
            context['ninos_seleccionados'] = ','.join(str(i) for i in self.object.ninos.values_list('id', flat=True))
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        parte_formset = context['parte_formset']

        if parte_formset.is_valid():
            self.object = form.save()

            # Actualizar niños desde el campo oculto
            ninos_ids_str = self.request.POST.get('ninos_seleccionados', '').strip()
            nuevos_ids = []
            if ninos_ids_str:
                try:
                    nuevos_ids = [int(x) for x in ninos_ids_str.split(',') if x]
                except ValueError:
                    nuevos_ids = []

            # Sincronizar relaciones OficioNino
            OficioNino.objects.filter(oficio=self.object).exclude(nino_id__in=nuevos_ids).delete()
            for nino_id in nuevos_ids:
                try:
                    nino_obj = Nino.objects.get(pk=nino_id)
                    OficioNino.objects.get_or_create(oficio=self.object, nino=nino_obj)
                except Nino.DoesNotExist:
                    continue

            # Guardar partes
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
