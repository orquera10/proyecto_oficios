from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction

from .models import Caso, CasoNino, CasoParte
from .forms import CasoForm, CasoNinoFormSet, CasoParteFormSet

class CasoListView(LoginRequiredMixin, ListView):
    model = Caso
    template_name = 'casos/caso_list.html'
    context_object_name = 'casos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por usuario a menos que sea superusuario
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset.order_by('-creado')

class CasoCreateView(LoginRequiredMixin, CreateView):
    model = Caso
    form_class = CasoForm
    template_name = 'casos/caso_form.html'
    success_url = reverse_lazy('casos:list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['nino_formset'] = CasoNinoFormSet(self.request.POST, prefix='ninos')
            context['parte_formset'] = CasoParteFormSet(self.request.POST, prefix='partes')
        else:
            context['nino_formset'] = CasoNinoFormSet(prefix='ninos')
            context['parte_formset'] = CasoParteFormSet(prefix='partes')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        ninos = context['nino_formset']
        partes = context['parte_formset']
        
        # Check if both formsets are valid
        if not (ninos.is_valid() and partes.is_valid()):
            return self.form_invalid(form)
            
        try:
            with transaction.atomic():
                # Save the main form
                self.object = form.save(commit=False)
                self.object.usuario = self.request.user
                self.object.save()
                
                # Save the formsets
                ninos.instance = self.object
                ninos.save()
                
                partes.instance = self.object
                partes.save()
                
                messages.success(self.request, 'Caso guardado exitosamente.')
                return super().form_valid(form)
                
        except Exception as e:
            messages.error(self.request, f'Error al guardar el caso: {str(e)}')
            return self.form_invalid(form)

class CasoUpdateView(LoginRequiredMixin, UpdateView):
    model = Caso
    form_class = CasoForm
    template_name = 'casos/caso_form.html'
    success_url = reverse_lazy('casos:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['nino_formset'] = CasoNinoFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='ninos'
            )
            context['parte_formset'] = CasoParteFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='partes'
            )
        else:
            context['nino_formset'] = CasoNinoFormSet(
                instance=self.object,
                prefix='ninos'
            )
            context['parte_formset'] = CasoParteFormSet(
                instance=self.object,
                prefix='partes'
            )
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        ninos = context['nino_formset']
        partes = context['parte_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if ninos.is_valid() and partes.is_valid():
                ninos.instance = self.object
                ninos.save()
                partes.instance = self.object
                partes.save()
                messages.success(self.request, 'Caso actualizado exitosamente.')
                return super().form_valid(form)
            else:
                return self.render_to_response(self.get_context_data(form=form))

class CasoDetailView(LoginRequiredMixin, DetailView):
    model = Caso
    template_name = 'casos/caso_detail.html'
    context_object_name = 'caso'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        
        # Prefetch related data to avoid N+1 queries
        return queryset.prefetch_related(
            'caso_ninos__nino',
            'caso_partes__parte',
            'usuario'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        caso = self.get_object()
        
        # No se necesita contexto adicional, la plantilla accederá a las relaciones
        # directamente a través del objeto caso usando caso.caso_ninos.all() y caso.caso_partes.all()
        return context

class CasoDeleteView(LoginRequiredMixin, DeleteView):
    model = Caso
    template_name = 'casos/caso_confirm_delete.html'
    success_url = reverse_lazy('casos:list')
    context_object_name = 'caso'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Caso eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)