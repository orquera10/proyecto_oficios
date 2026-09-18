from django import forms
from django.contrib.auth import get_user_model
from core.models import UsuarioPerfil
from .models import Institucion


User = get_user_model()


class ProfesionalForm(forms.ModelForm):
    instituciones = forms.ModelMultipleChoiceField(
        queryset=Institucion.objects.all().order_by('nombre'),
        required=False,
        label='Instituciones asignadas',
        help_text='Puede seleccionar una o varias instituciones (mantenga presionado Ctrl para seleccionar varias).'
    )
    password1 = forms.CharField(
        label='Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Email',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar instituciones desde el perfil
        perfil = getattr(self.instance, 'perfil', None)
        if perfil and 'instituciones' in self.fields:
            insts = list(perfil.instituciones.values_list('pk', flat=True))
            if not insts and perfil.id_institucion_id:
                insts = [perfil.id_institucion_id]
            self.fields['instituciones'].initial = insts
        # Estilos bootstrap
        for name, field in self.fields.items():
            base = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (base + ' form-check-input').strip()
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = (base + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (base + ' form-control').strip()

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 or p2:
            if p1 != p2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned

    def save(self, commit=True):
        is_new = self.instance.pk is None
        user = super().save(commit=False)
        if user.first_name:
            user.first_name = user.first_name.upper()
        if user.last_name:
            user.last_name = user.last_name.upper()
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        # Asegurar perfil profesional e instituciones
        perfil, _ = UsuarioPerfil.objects.get_or_create(usuario=user)
        perfil.es_profesional = True
        insts = self.cleaned_data.get('instituciones')
        if insts is not None:
            perfil.instituciones.set(insts)
            perfil.id_institucion = insts.first() if insts.exists() else None
        perfil.save(update_fields=['es_profesional', 'id_institucion'])
        return user
