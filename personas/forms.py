from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Nino, Parte

class NinoForm(forms.ModelForm):
    class Meta:
        model = Nino
        fields = ['nombre', 'apellido', 'dni', 'fecha_nac', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el nombre')
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el apellido')
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el DNI')
            }),
            'fecha_nac': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': _('Seleccione la fecha de nacimiento')
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ingrese la dirección')
            }),
        }
        labels = {
            'nombre': _('Nombre'),
            'apellido': _('Apellido'),
            'dni': _('DNI'),
            'fecha_nac': _('Fecha de Nacimiento'),
            'direccion': _('Dirección'),
        }

class ParteForm(forms.ModelForm):
    class Meta:
        model = Parte
        fields = ['nombre', 'apellido', 'dni', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el nombre')
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el apellido')
            }),
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el DNI')
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ingrese la dirección')
            }),
        }
        labels = {
            'nombre': _('Nombre'),
            'apellido': _('Apellido'),
            'dni': _('DNI'),
            'direccion': _('Dirección'),
        }
