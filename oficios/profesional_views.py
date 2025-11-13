from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from core.models import UsuarioPerfil
from .forms_profesional import ProfesionalForm


User = get_user_model()


class ProfesionalListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'oficios/profesional_list.html'
    context_object_name = 'profesionales'
    paginate_by = 10

    def get_queryset(self):
        return (
            User.objects.filter(perfil__es_profesional=True)
            .select_related('perfil')
            .order_by('first_name', 'last_name', 'username')
        )


class ProfesionalCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = ProfesionalForm
    template_name = 'oficios/profesional_form.html'
    success_url = reverse_lazy('oficios:profesional_list')

    def form_valid(self, form):
        messages.success(self.request, 'El profesional fue creado correctamente.')
        return super().form_valid(form)


class ProfesionalUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfesionalForm
    template_name = 'oficios/profesional_form.html'
    success_url = reverse_lazy('oficios:profesional_list')

    def get_queryset(self):
        return User.objects.filter(perfil__es_profesional=True)

    def form_valid(self, form):
        messages.success(self.request, 'El profesional fue actualizado correctamente.')
        return super().form_valid(form)


class ProfesionalDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'oficios/profesional_detail.html'
    context_object_name = 'profesional'

    def get_queryset(self):
        return User.objects.filter(perfil__es_profesional=True).select_related('perfil')


class ProfesionalDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'oficios/profesional_confirm_delete.html'
    success_url = reverse_lazy('oficios:profesional_list')

    def get_queryset(self):
        return User.objects.filter(perfil__es_profesional=True)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Evitar eliminar si tiene respuestas asociadas como profesional
        try:
            from .models import Respuesta
            total = Respuesta.objects.filter(id_profesional=self.object).count()
        except Exception:
            total = 0
        if total > 0:
            messages.error(request, f'No se puede eliminar porque tiene {total} respuesta(s) asociada(s).')
            return redirect('oficios:profesional_detail', pk=self.object.pk)
        messages.success(request, 'El profesional fue eliminado correctamente.')
        return super().post(request, *args, **kwargs)

