from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import (
    Oficio, Institucion, Caratula, CaratulaOficio, Juzgado,
    OficioNino, OficioParte
)
from personas.models import Nino, Parte

class OficioNinoForm(forms.ModelForm):
    nino = forms.ModelChoiceField(
        queryset=Nino.objects.all().order_by('apellido', 'nombre'),
        label='Niño',
        widget=forms.Select(attrs={
            'class': 'form-select select2',
        }),
        required=True
    )
    
    class Meta:
        model = OficioNino
        fields = ['nino', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurarse de que el campo nino esté marcado como requerido
        self.fields['nino'].required = True

class OficioParteForm(forms.ModelForm):
    class Meta:
        model = OficioParte
        fields = ['parte', 'tipo_relacion', 'observaciones']
        widgets = {
            'parte': forms.Select(attrs={'class': 'form-select select2'}),
            'tipo_relacion': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

OficioNinoFormSet = inlineformset_factory(
    Oficio, OficioNino, 
    form=OficioNinoForm,
    extra=1, 
    can_delete=True
)

OficioParteFormSet = inlineformset_factory(
    Oficio, OficioParte,
    form=OficioParteForm,
    extra=1,
    can_delete=True
)

class OficioForm(forms.ModelForm):
    class Meta:
        model = Oficio
        fields = [
            'tipo', 'expte', 'institucion', 'juzgado',
            'plazo_horas', 'fecha_emision', 'caratula', 'caratula_oficio'
        ]
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'expte': forms.TextInput(attrs={'class': 'form-control'}),
            'plazo_horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'juzgado': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'juzgado': 'Agente'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial fecha_emision to now if not set
        if not self.instance.pk:
            self.initial['fecha_emision'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'fecha_emision':  # Already handled
                field.widget.attrs.update({'class': 'form-control'})
