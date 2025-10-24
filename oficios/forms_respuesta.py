from django import forms
from django.utils import timezone
from .models import Respuesta


class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['id_institucion', 'respuesta', 'respuesta_pdf', 'fecha_hora']
        widgets = {
            'respuesta': forms.Textarea(attrs={'rows': 4}),
            'respuesta_pdf': forms.FileInput(attrs={'accept': '.pdf'}),
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'id_institucion': 'Institución',
            'respuesta': 'Respuesta',
            'respuesta_pdf': 'Archivo PDF de la respuesta',
            'fecha_hora': 'Fecha y hora',
        }
        help_texts = {
            'respuesta_pdf': 'Sube un PDF (máximo 10MB).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('fecha_hora'):
            self.initial['fecha_hora'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        self.fields['id_institucion'].required = False
        self.fields['respuesta_pdf'].required = False
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

