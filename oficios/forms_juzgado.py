from django import forms
from .models import Juzgado, CategoriaJuzgado


class JuzgadoForm(forms.ModelForm):
    id_categoria = forms.ModelChoiceField(
        queryset=CategoriaJuzgado.objects.all().order_by('nombre'),
        required=False,
        label='Categoría',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Juzgado
        fields = ['nombre', 'telefono', 'direccion', 'id_categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre del Juzgado/Agente',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'id_categoria': 'Categoría',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'id_categoria':
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()