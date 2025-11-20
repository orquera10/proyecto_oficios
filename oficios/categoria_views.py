from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CategoriaJuzgado
from .forms_categoria import CategoriaJuzgadoForm


class CategoriaListView(LoginRequiredMixin, ListView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nombre']
    paginate_by = 10


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaJuzgado
    form_class = CategoriaJuzgadoForm
    template_name = 'oficios/categoria_form.html'
    success_url = reverse_lazy('oficios:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'La categoría fue creada correctamente.')
        return super().form_valid(form)


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaJuzgado
    form_class = CategoriaJuzgadoForm
    template_name = 'oficios/categoria_form.html'
    success_url = reverse_lazy('oficios:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'La categoría fue actualizada correctamente.')
        return super().form_valid(form)


class CategoriaDetailView(LoginRequiredMixin, DetailView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_detail.html'
    context_object_name = 'categoria'


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_confirm_delete.html'
    success_url = reverse_lazy('oficios:categoria_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'La categoría fue eliminada correctamente.')
        return super().delete(request, *args, **kwargs)

