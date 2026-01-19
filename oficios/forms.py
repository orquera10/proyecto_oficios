from django import forms
from django.utils import timezone
from .models import (
    Oficio, Institucion, Caratula, Juzgado, CaratulaOficio
)


class OficioForm(forms.ModelForm):
    instituciones = forms.ModelMultipleChoiceField(
        queryset=Institucion.objects.all().order_by('nombre'),
        required=False,
        label='Instituciones',
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Oficio
        fields = [
            'nro_oficio', 'denuncia', 'legajo', 'juzgado',
            'plazo_horas', 'fecha_emision', 'caratula',
            'caratula_oficio', 'archivo_pdf', 'caso',
            'instituciones'
        ]
        widgets = {
            'fecha_emision': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'nro_oficio': forms.TextInput(attrs={'class': 'form-control'}),
            'denuncia': forms.TextInput(attrs={'class': 'form-control'}),
            'legajo': forms.TextInput(attrs={'class': 'form-control'}),
            'plazo_horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'juzgado': forms.Select(attrs={'class': 'form-control'}),
            'archivo_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'caso': forms.HiddenInput(),
        }
        labels = {
            'juzgado': 'Agente',
            'archivo_pdf': 'Archivo PDF del Oficio',
            'nro_oficio': 'Numero de Oficio'
        }
        help_texts = {
            'archivo_pdf': 'Sube el archivo PDF del oficio. Tamano maximo: 10MB.',
        }

    def clean_archivo_pdf(self):
        archivo = self.cleaned_data.get('archivo_pdf', False)
        if archivo:
            if archivo.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("El archivo es demasiado grande. El tamano maximo permitido es 10MB.")
            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Solo se permiten archivos PDF.")
        return archivo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial fecha_emision to now if not set
        if not self.instance.pk:
            local_now = timezone.localtime(timezone.now())
            self.initial['fecha_emision'] = local_now.strftime('%Y-%m-%dT%H:%M')

        # Configurar campos opcionales
        self.fields['nro_oficio'].required = False
        self.fields['denuncia'].required = False
        self.fields['legajo'].required = False
        self.fields['juzgado'].required = False
        self.fields['plazo_horas'].required = False
        self.fields['caratula'].required = False
        self.fields['caratula_oficio'].required = False
        self.fields['archivo_pdf'].required = False

        # Agregar clases de Bootstrap a todos los campos (evitar checkbox)
        from django.forms import CheckboxInput
        for field_name, field in self.fields.items():
            if field_name == 'fecha_emision':  # Ya esta manejado
                continue
            if isinstance(field.widget, CheckboxInput):
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean(self):
        # No exigir instituciones: permitir crear sin institución
        return super().clean()
