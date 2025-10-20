from django import forms
from django.utils import timezone
from .models import (
    Oficio, Institucion, Caratula, Juzgado, CaratulaOficio
)

class OficioForm(forms.ModelForm):
    class Meta:
        model = Oficio
        fields = [
            'tipo', 'nro_oficio', 'expte', 'institucion', 'juzgado',
            'plazo_horas', 'fecha_emision', 'caratula',
            'caratula_oficio', 'archivo_pdf'
        ]
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'nro_oficio': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'expte': forms.TextInput(attrs={'class': 'form-control'}),
            'plazo_horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'juzgado': forms.Select(attrs={'class': 'form-control'}),
            'archivo_pdf': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
            }),
        }
        labels = {
            'juzgado': 'Agente',
            'archivo_pdf': 'Archivo PDF del Oficio',
            'nro_oficio': 'Número de Oficio'
        }
        help_texts = {
            'archivo_pdf': 'Sube el archivo PDF del oficio. Tamaño máximo: 10MB.',
        }

    def clean_archivo_pdf(self):
        archivo = self.cleaned_data.get('archivo_pdf', False)
        if archivo:
            if archivo.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("El archivo es demasiado grande. El tamaño máximo permitido es 10MB.")
            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Solo se permiten archivos PDF.")
        return archivo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial fecha_emision to now if not set
        if not self.instance.pk:
            self.initial['fecha_emision'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name != 'fecha_emision':  # Already handled
                field.widget.attrs.update({'class': 'form-control'})
