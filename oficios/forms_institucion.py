from django import forms
from .models import Institucion


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['nombre', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre de la Institucion',
            'direccion': 'Direccion',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

