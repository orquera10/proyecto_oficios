from django import forms
from django.utils import timezone
from .models import (
    Oficio, Institucion, Caratula, Juzgado, CaratulaOficio
)


class OficioForm(forms.ModelForm):
    PLAZO_UNIDAD_CHOICES = (
        ('horas', 'Horas'),
        ('dias', 'Dias'),
    )
    plazo_unidad = forms.ChoiceField(
        choices=PLAZO_UNIDAD_CHOICES,
        required=False,
        label='Unidad de plazo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
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
            'fecha_emision': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'placeholder': 'YYYY-MM-DD HH:MM'},
                format='%Y-%m-%dT%H:%M'
            ),
            'nro_oficio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1234/2025'}),
            'denuncia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Denuncia 5678'}),
            'legajo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Legajo 9012'}),
            'plazo_horas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas de plazo (opcional)'}),
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
        self.initial.setdefault('plazo_unidad', 'dias')
        self.initial.setdefault('plazo_horas', 5)

        # Configurar campos opcionales
        self.fields['nro_oficio'].required = False
        self.fields['denuncia'].required = False
        self.fields['legajo'].required = False
        self.fields['juzgado'].required = False
        self.fields['plazo_horas'].required = False
        self.fields['plazo_unidad'].required = False
        self.fields['caratula'].required = False
        self.fields['caratula_oficio'].required = False
        self.fields['archivo_pdf'].required = False

        # Quitar ayudas en campos con placeholder para evitar redundancia
        for field_name in ('denuncia', 'legajo'):
            if field_name in self.fields:
                self.fields[field_name].help_text = ''

        # Placeholders y labels vacios para selects opcionales
        if 'juzgado' in self.fields:
            self.fields['juzgado'].empty_label = 'Seleccione agente (opcional)'
        if 'caratula' in self.fields:
            self.fields['caratula'].empty_label = 'Seleccione caratula (opcional)'

        if 'caratula_oficio' in self.fields:
            self.fields['caratula_oficio'].widget.attrs.setdefault(
                'placeholder',
                'Ej: Caratula del oficio'
            )

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
        cleaned = super().clean()
        # No exigir instituciones: permitir crear sin institucion
        plazo_horas = cleaned.get('plazo_horas')
        plazo_unidad = cleaned.get('plazo_unidad') or 'horas'
        if plazo_horas and plazo_unidad == 'dias':
            cleaned['plazo_horas'] = plazo_horas * 24
        return cleaned
