from django import forms
from django.contrib.auth import get_user_model
from core.models import UsuarioPerfil
from .models import Institucion


User = get_user_model()


class ProfesionalForm(forms.ModelForm):
    id_institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.all().order_by('nombre'),
        required=False,
        label='Institución'
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
        # Inicializar institución desde el perfil
        perfil = getattr(self.instance, 'perfil', None)
        if perfil and perfil.id_institucion_id and 'id_institucion' in self.fields:
            self.fields['id_institucion'].initial = perfil.id_institucion_id
        # Estilos bootstrap
        for name, field in self.fields.items():
            base = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = (base + ' form-check-input').strip()
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
        # Asegurar perfil profesional e institución
        perfil, _ = UsuarioPerfil.objects.get_or_create(usuario=user)
        perfil.es_profesional = True
        perfil.id_institucion = self.cleaned_data.get('id_institucion')
        perfil.save(update_fields=['es_profesional', 'id_institucion'])
        return user
