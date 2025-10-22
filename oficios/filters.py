import django_filters
from django import forms
from django.db.models import Q
from .models import Oficio, Institucion, Juzgado, Caratula

class OficioFilter(django_filters.FilterSet):
    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('cargado', 'Cargado'),
        ('asignado', 'Asignado'),
        ('respondido', 'Respondido'),
        ('enviado', 'Enviado'),
    ]
    
    # Filtro de búsqueda general
    busqueda = django_filters.CharFilter(
        method='filtro_busqueda',
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por número, descripción, etc.'
        })
    )
    
    # Filtros básicos
    estado = django_filters.ChoiceFilter(
        field_name='estado',
        label='Estado',
        choices=ESTADO_CHOICES,
        empty_label='Todos los estados',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    # Filtros por fechas
    fecha_desde = django_filters.DateFilter(
        field_name='fecha_emision',
        lookup_expr='gte',
        label='Fecha desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'Desde...'
        })
    )
    
    fecha_hasta = django_filters.DateFilter(
        field_name='fecha_emision',
        lookup_expr='lte',
        label='Fecha hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'Hasta...'
        })
    )
    
    # Filtros por relaciones
    institucion = django_filters.ModelChoiceFilter(
        field_name='institucion',
        queryset=Institucion.objects.all().order_by('nombre'),
        label='Institución',
        empty_label='Todas las instituciones',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-search',
            'data-placeholder': 'Buscar institución...'
        })
    )
    
    juzgado = django_filters.ModelChoiceFilter(
        field_name='juzgado',
        queryset=Juzgado.objects.all().order_by('nombre'),
        label='Juzgado',
        empty_label='Todos los juzgados',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-search',
            'data-placeholder': 'Buscar juzgado...'
        })
    )
    
    
    class Meta:
        model = Oficio
        fields = [
            'busqueda',
            'estado',
            'fecha_desde',
            'fecha_hasta',
            'institucion',
            'juzgado'
        ]
    
    def filtro_busqueda(self, queryset, name, value):
        """
        Filtro personalizado para búsqueda en múltiples campos
        """
        if value:
            return queryset.filter(
                Q(denuncia__icontains=value) |
                Q(legajo__icontains=value) |
                Q(institucion__nombre__icontains=value) |
                Q(juzgado__nombre__icontains=value) |
                Q(nro_oficio__icontains=value)
            ).distinct()
        return queryset
    
