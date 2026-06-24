from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Caso, CasoNino, CasoParte
from personas.models import Nino, Parte


class CasoForm(ModelForm):
    class Meta:
        model = Caso
        fields = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name in self.errors:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' is-invalid'
                field.widget.attrs['style'] = 'border-color: #dc3545;'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.usuario = self.user
        if commit:
            instance.save()
        return instance


class CasoNinoForm(ModelForm):
    nino = forms.ModelChoiceField(
        queryset=Nino.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Niño'
    )

    class Meta:
        model = CasoNino
        fields = ['nino', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CasoParteForm(ModelForm):
    parte = forms.ModelChoiceField(
        queryset=Parte.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Parte'
    )

    class Meta:
        model = CasoParte
        fields = ['parte', 'tipo_relacion', 'observaciones']
        widgets = {
            'tipo_relacion': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


CasoNinoFormSet = inlineformset_factory(
    Caso,
    CasoNino,
    form=CasoNinoForm,
    extra=1,
    can_delete=True
)

CasoParteFormSet = inlineformset_factory(
    Caso,
    CasoParte,
    form=CasoParteForm,
    extra=1,
    can_delete=True
)
