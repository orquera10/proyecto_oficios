from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CategoriaJuzgado
from .forms_categoria import CategoriaJuzgadoForm
from .permissions import CoordinacionOPDWriteBlockMixin, CoordinacionOPDContextMixin


class CategoriaListView(CoordinacionOPDContextMixin, LoginRequiredMixin, ListView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nombre']
    paginate_by = 10


class CategoriaCreateView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, CreateView):
    model = CategoriaJuzgado
    form_class = CategoriaJuzgadoForm
    template_name = 'oficios/categoria_form.html'
    success_url = reverse_lazy('oficios:categoria_list')
    redirect_url_name = 'oficios:categoria_list'

    def form_valid(self, form):
        messages.success(self.request, 'La categoría fue creada correctamente.')
        return super().form_valid(form)


class CategoriaUpdateView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, UpdateView):
    model = CategoriaJuzgado
    form_class = CategoriaJuzgadoForm
    template_name = 'oficios/categoria_form.html'
    success_url = reverse_lazy('oficios:categoria_list')
    redirect_url_name = 'oficios:categoria_list'

    def form_valid(self, form):
        messages.success(self.request, 'La categoría fue actualizada correctamente.')
        return super().form_valid(form)


class CategoriaDetailView(CoordinacionOPDContextMixin, LoginRequiredMixin, DetailView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_detail.html'
    context_object_name = 'categoria'


class CategoriaDeleteView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, DeleteView):
    model = CategoriaJuzgado
    template_name = 'oficios/categoria_confirm_delete.html'
    success_url = reverse_lazy('oficios:categoria_list')
    redirect_url_name = 'oficios:categoria_list'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'La categoría fue eliminada correctamente.')
        return super().delete(request, *args, **kwargs)
