from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect

from .models import Institucion
from .forms_institucion import InstitucionForm


class InstitucionListView(LoginRequiredMixin, ListView):
    model = Institucion
    template_name = 'oficios/institucion_list.html'
    context_object_name = 'instituciones'
    paginate_by = 10
    ordering = ['nombre']


class InstitucionCreateView(LoginRequiredMixin, CreateView):
    model = Institucion
    form_class = InstitucionForm
    template_name = 'oficios/institucion_form.html'
    success_url = reverse_lazy('oficios:institucion_list')

    def form_valid(self, form):
        messages.success(self.request, 'La institucion fue creada correctamente.')
        return super().form_valid(form)


class InstitucionUpdateView(LoginRequiredMixin, UpdateView):
    model = Institucion
    form_class = InstitucionForm
    template_name = 'oficios/institucion_form.html'
    success_url = reverse_lazy('oficios:institucion_list')

    def form_valid(self, form):
        messages.success(self.request, 'La institucion fue actualizada correctamente.')
        return super().form_valid(form)


class InstitucionDetailView(LoginRequiredMixin, DetailView):
    model = Institucion
    template_name = 'oficios/institucion_detail.html'
    context_object_name = 'institucion'


class InstitucionDeleteView(LoginRequiredMixin, DeleteView):
    model = Institucion
    template_name = 'oficios/institucion_confirm_delete.html'
    success_url = reverse_lazy('oficios:institucion_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Evitar intentar borrar si hay oficios asociados (FK PROTECT)
        try:
            from .models import Oficio
            total = Oficio.objects.filter(institucion=self.object).count()
        except Exception:
            total = 0
        if total > 0:
            messages.error(request, f'No se puede eliminar porque tiene {total} oficio(s) asociado(s).')
            return redirect('oficios:institucion_detail', pk=self.object.pk)
        return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'La institucion fue eliminada correctamente.')
            return response
        except ProtectedError:
            try:
                from .models import Oficio
                total = Oficio.objects.filter(institucion=self.object).count()
            except Exception:
                total = 0
            messages.error(
                request,
                f'No se puede eliminar porque tiene {total} oficio(s) asociado(s).'
            )
            return redirect('oficios:institucion_detail', pk=self.object.pk)

