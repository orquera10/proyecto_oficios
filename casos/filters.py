import django_filters
from django import forms
from django.db.models import Q
from .models import Caso, CasoNino, CasoParte
from personas.models import Nino, Parte

class CasoFilter(django_filters.FilterSet):
    TIPO_CHOICES = [
        ('', 'Todos'),
        ('MPA', 'MPA'),
        ('JUDICIAL', 'Judicial'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En Proceso'),
        ('CERRADO', 'Cerrado'),
    ]
    
    # Filtro de búsqueda general
    busqueda = django_filters.CharFilter(
        method='filtro_busqueda',
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por expediente, DNI, nombre o apellido de niño/parte...'
        })
    )
    
    # Filtros básicos
    tipo = django_filters.ChoiceFilter(
        field_name='tipo',
        label='Tipo de Caso',
        choices=TIPO_CHOICES,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    estado = django_filters.ChoiceFilter(
        field_name='estado',
        label='Estado',
        choices=ESTADO_CHOICES,
        empty_label='Todos los estados',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    # Filtros por fechas
    fecha_desde = django_filters.DateFilter(
        field_name='creado',
        lookup_expr='gte',
        label='Fecha desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'Desde...'
        })
    )
    
    fecha_hasta = django_filters.DateFilter(
        field_name='creado',
        lookup_expr='lte',
        label='Fecha hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'Hasta...'
        })
    )
    
    
    class Meta:
        model = Caso
        fields = [
            'busqueda',
            'tipo',
            'estado',
            'fecha_desde',
            'fecha_hasta'
        ]
    
    def filtro_busqueda(self, queryset, name, value):
        """
        Filtro personalizado para búsqueda en múltiples campos
        Incluye búsqueda por:
        - Número de expediente
        - DNI de niños
        - Nombres y apellidos de niños
        - DNI de partes
        - Nombres y apellidos de partes
        """
        if not value:
            return queryset
            
        # Búsqueda en campos directos del caso
        q_objects = Q(expte__icontains=value)
        
        # Búsqueda en niños relacionados
        ninos = Nino.objects.filter(
            Q(dni__icontains=value) |
            Q(nombre__icontains=value) |
            Q(apellido__icontains=value)
        ).values_list('id_ninos', flat=True)
        
        # Búsqueda en partes relacionadas
        partes = Parte.objects.filter(
            Q(dni__icontains=value) |
            Q(nombre__icontains=value) |
            Q(apellido__icontains=value)
        ).values_list('id_partes', flat=True)
        
        # Obtener los IDs de casos que tienen los niños o partes encontrados
        if ninos.exists():
            casos_con_ninos = CasoNino.objects.filter(nino_id__in=ninos).values_list('caso_id', flat=True)
            q_objects |= Q(id__in=casos_con_ninos)
            
        if partes.exists():
            casos_con_partes = CasoParte.objects.filter(parte_id__in=partes).values_list('caso_id', flat=True)
            q_objects |= Q(id__in=casos_con_partes)
        
        return queryset.filter(q_objects).distinct()
