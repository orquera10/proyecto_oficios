from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Nino, Parte


def _normalize_nombre(value: str) -> str:
    """Normaliza nombres y apellidos a formato capitalizado."""
    if not value:
        return value
    value = " ".join(part.strip() for part in value.split() if part.strip())
    return value.title()


class NinoForm(forms.ModelForm):
    class Meta:
        model = Nino
        fields = ['nombre', 'apellido', 'dni', 'fecha_nac', 'edad', 'domicilio_principal', 'domicilio_secundario']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el nombre'),
                'required': 'required'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el apellido'),
                'required': 'required'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el DNI (opcional)')
            }),
            'fecha_nac': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': _('Seleccione la fecha de nacimiento (opcional)')
            }),
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': _('Edad en años (opcional)')
            }),
            'domicilio_principal': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ingrese el domicilio principal (opcional)')
            }),
            'domicilio_secundario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ingrese el domicilio secundario (opcional)')
            }),
        }
        labels = {
            'nombre': _('Nombre *'),
            'apellido': _('Apellido *'),
            'dni': _('DNI (opcional)'),
            'fecha_nac': _('Fecha de Nacimiento (opcional)'),
            'edad': _('Edad (opcional)'),
            'domicilio_principal': _('Domicilio principal (opcional)'),
            'domicilio_secundario': _('Domicilio secundario (opcional)'),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        return _normalize_nombre(nombre)

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '')
        return _normalize_nombre(apellido)

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            # Eliminar puntos y espacios en blanco
            dni = dni.replace('.', '').replace(' ', '')
            # Verificar que solo contenga números
            if not dni.isdigit():
                raise forms.ValidationError('El DNI solo puede contener números y puntos')
        return dni or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que solo nombre y apellido sean obligatorios en el frontend
        self.fields['nombre'].required = True
        self.fields['apellido'].required = True
        self.fields['dni'].required = False
        self.fields['fecha_nac'].required = False
        self.fields['edad'].required = False
        self.fields['domicilio_principal'].required = False
        self.fields['domicilio_secundario'].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        apellido = (cleaned.get('apellido') or '').strip()
        if not nombre or not apellido:
            return cleaned

        dup_qs = Nino.objects.filter(
            nombre__iexact=nombre,
            apellido__iexact=apellido,
        )
        if self.instance and self.instance.pk:
            dup_qs = dup_qs.exclude(pk=self.instance.pk)
        if dup_qs.exists():
            raise forms.ValidationError('Ya existe un niño con el mismo nombre y apellido.')
        return cleaned

class ParteForm(forms.ModelForm):
    class Meta:
        model = Parte
        fields = ['nombre', 'apellido', 'dni', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el nombre'),
                'required': 'required'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el apellido'),
                'required': 'required'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el DNI (opcional)')
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el teléfono (opcional)')
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ingrese la dirección (opcional)')
            }),
        }
        labels = {
            'nombre': _('Nombre *'),
            'apellido': _('Apellido *'),
            'dni': _('DNI (opcional)'),
            'telefono': _('Teléfono (opcional)'),
            'direccion': _('Dirección (opcional)'),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        return _normalize_nombre(nombre)

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '')
        return _normalize_nombre(apellido)

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            # Eliminar puntos y espacios en blanco
            dni = dni.replace('.', '').replace(' ', '')
            # Verificar que solo contenga números
            if not dni.isdigit():
                raise forms.ValidationError('El DNI solo puede contener números y puntos')
        return dni or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que solo nombre y apellido sean obligatorios
        self.fields['nombre'].required = True
        self.fields['apellido'].required = True
        self.fields['dni'].required = False
        self.fields['telefono'].required = False
        self.fields['direccion'].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        apellido = (cleaned.get('apellido') or '').strip()
        if not nombre or not apellido:
            return cleaned

        dup_qs = Parte.objects.filter(
            nombre__iexact=nombre,
            apellido__iexact=apellido,
        )
        if self.instance and self.instance.pk:
            dup_qs = dup_qs.exclude(pk=self.instance.pk)
        if dup_qs.exists():
            raise forms.ValidationError('Ya existe una parte con el mismo nombre y apellido.')
        return cleaned
