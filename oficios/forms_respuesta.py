from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Respuesta


class UserFullNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full = (obj.get_full_name() or '').strip()
        return full if full else obj.username


class RespuestaForm(forms.ModelForm):
    # Campo no-modelo para indicar si se devuelve en lugar de responder
    devolver = forms.BooleanField(
        required=False,
        initial=False,
        label='Devolver',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    derivar = forms.BooleanField(
        required=False,
        initial=False,
        label='Derivación',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    id_profesional = UserFullNameChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label='Profesional'
    )
    class Meta:
        model = Respuesta
        fields = ['id_profesional', 'respuesta', 'respuesta_pdf', 'fecha_hora']
        widgets = {
            'id_profesional': forms.Select(),
            'respuesta': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escriba las observaciones o aclaraciones que acompañan la respuesta.'}),
            'respuesta_pdf': forms.FileInput(attrs={'accept': '.pdf'}),
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'id_institucion': 'Institución',
            'respuesta': 'Observaciones',
            'respuesta_pdf': 'Archivo PDF de la respuesta',
            'fecha_hora': 'Fecha y hora',
        }
        help_texts = {
            'respuesta_pdf': 'Sube un PDF (máximo 10MB).',
        }

    def __init__(self, *args, **kwargs):
        oficio = kwargs.pop('oficio', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('fecha_hora'):
            local_now = timezone.localtime(timezone.now())
            self.initial['fecha_hora'] = local_now.strftime('%Y-%m-%dT%H:%M')
        self.fields['respuesta_pdf'].required = False
        # Filtrar profesionales por institución del oficio
        try:
            institucion = None
            if oficio and getattr(oficio, 'institucion_id', None):
                institucion = oficio.institucion
            elif self.initial.get('id_institucion'):
                institucion = self.initial.get('id_institucion')
            elif getattr(self.instance, 'id_institucion_id', None):
                institucion = self.instance.id_institucion

            qs = get_user_model().objects.all()
            if institucion:
                from django.db.models import Q
                qs = qs.filter(
                    Q(perfil__instituciones=institucion) | Q(perfil__id_institucion=institucion),
                    perfil__es_profesional=True,
                    is_active=True
                ).distinct()
            else:
                qs = qs.none()
            self.fields['id_profesional'].queryset = qs.order_by('first_name', 'last_name', 'username')
        except Exception:
            self.fields['id_profesional'].queryset = get_user_model().objects.none()
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            # Usar form-select en selects y form-control en otros
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean(self):
        cleaned = super().clean()
        devolver = cleaned.get('devolver')
        derivar = cleaned.get('derivar')
        if devolver and derivar:
            raise forms.ValidationError('Selecciona solo una opción: Devolver o Derivación.')
        return cleaned
