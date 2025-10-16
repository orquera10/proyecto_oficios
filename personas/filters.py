import django_filters
from django import forms
from django.db.models import Q
from .models import Nino

class NinoFilter(django_filters.FilterSet):
    # Búsqueda general en múltiples campos
    busqueda = django_filters.CharFilter(
        method='filtro_busqueda',
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'DNI, Apellido, Nombre, Dirección'
        })
    )

    # Rango de fecha de nacimiento
    fecha_desde = django_filters.DateFilter(
        field_name='fecha_nac',
        lookup_expr='gte',
        label='Fecha nac. desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
        })
    )
    fecha_hasta = django_filters.DateFilter(
        field_name='fecha_nac',
        lookup_expr='lte',
        label='Fecha nac. hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
        })
    )

    class Meta:
        model = Nino
        fields = ['busqueda', 'fecha_desde', 'fecha_hasta']

    def filtro_busqueda(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(dni__icontains=value) |
                Q(apellido__icontains=value) |
                Q(nombre__icontains=value) |
                Q(direccion__icontains=value)
            ).distinct()
        return queryset
