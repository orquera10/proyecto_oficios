from django import forms
from .models import Juzgado


class JuzgadoForm(forms.ModelForm):
    class Meta:
        model = Juzgado
        fields = ['nombre', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre del Juzgado/Agente',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

