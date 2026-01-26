from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect

from .models import Juzgado
from .forms_juzgado import JuzgadoForm
from .permissions import CoordinacionOPDWriteBlockMixin, CoordinacionOPDContextMixin


class JuzgadoListView(CoordinacionOPDContextMixin, LoginRequiredMixin, ListView):
    model = Juzgado
    template_name = 'oficios/juzgado_list.html'
    context_object_name = 'juzgados'
    paginate_by = 10
    ordering = ['nombre']


class JuzgadoCreateView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, CreateView):
    model = Juzgado
    form_class = JuzgadoForm
    template_name = 'oficios/juzgado_form.html'
    success_url = reverse_lazy('oficios:juzgado_list')
    redirect_url_name = 'oficios:juzgado_list'

    def form_valid(self, form):
        messages.success(self.request, 'El juzgado/agente fue creado correctamente.')
        return super().form_valid(form)


class JuzgadoUpdateView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, UpdateView):
    model = Juzgado
    form_class = JuzgadoForm
    template_name = 'oficios/juzgado_form.html'
    success_url = reverse_lazy('oficios:juzgado_list')
    redirect_url_name = 'oficios:juzgado_list'

    def form_valid(self, form):
        messages.success(self.request, 'El juzgado/agente fue actualizado correctamente.')
        return super().form_valid(form)


class JuzgadoDetailView(CoordinacionOPDContextMixin, LoginRequiredMixin, DetailView):
    model = Juzgado
    template_name = 'oficios/juzgado_detail.html'
    context_object_name = 'juzgado'


class JuzgadoDeleteView(CoordinacionOPDWriteBlockMixin, LoginRequiredMixin, DeleteView):
    model = Juzgado
    template_name = 'oficios/juzgado_confirm_delete.html'
    success_url = reverse_lazy('oficios:juzgado_list')
    redirect_url_name = 'oficios:juzgado_list'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Prevención: si tiene oficios asociados, no intentar borrar
        try:
            from .models import Oficio
            total = Oficio.objects.filter(juzgado=self.object).count()
        except Exception:
            total = 0
        if total > 0:
            messages.error(request, f'No se puede eliminar porque tiene {total} oficio(s) asociado(s).')
            return redirect('oficios:juzgado_detail', pk=self.object.pk)
        return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'El juzgado/agente fue eliminado correctamente.')
            return response
        except ProtectedError:
            # No permitir eliminación si tiene oficios asociados (FK PROTECT)
            try:
                from .models import Oficio
                total = Oficio.objects.filter(juzgado=self.object).count()
            except Exception:
                total = 0
            messages.error(
                request,
                f'No se puede eliminar porque tiene {total} oficio(s) asociado(s).'
            )
            return redirect('oficios:juzgado_detail', pk=self.object.pk)
