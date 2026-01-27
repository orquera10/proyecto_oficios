from django import forms
from .models import CategoriaJuzgado


class CategoriaJuzgadoForm(forms.ModelForm):
    class Meta:
        model = CategoriaJuzgado
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre de la categoría',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            return nombre

        dup_qs = CategoriaJuzgado.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            dup_qs = dup_qs.exclude(pk=self.instance.pk)
        if dup_qs.exists():
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre
