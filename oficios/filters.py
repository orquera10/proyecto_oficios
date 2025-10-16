import django_filters
from django import forms
from django.db.models import Q
from .models import Oficio, Institucion, Juzgado, Caratula, Nino, OficioNino

class OficioFilter(django_filters.FilterSet):
    TIPO_CHOICES = [
        ('', 'Todos'),
        ('MPA', 'MPA'),
        ('Judicial', 'Judicial'),
    ]
    
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
    tipo = django_filters.ChoiceFilter(
        field_name='tipo',
        label='Tipo de oficio',
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
    
    nino = django_filters.ModelChoiceFilter(
        field_name='oficio_ninos__nino',
        queryset=Nino.objects.all().order_by('apellido', 'nombre'),
        label='Niño',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-search',
            'data-placeholder': 'Buscar niño...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mejorar el queryset para incluir el documento en el display
        self.filters['nino'].field.queryset = Nino.objects.all().order_by('apellido', 'nombre')
        # Mejorar el formato de visualización de las opciones
        self.filters['nino'].field.label_from_instance = lambda obj: f"{obj.apellido}, {obj.nombre} - {obj.documento_identidad or 'Sin documento'}"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurarse de que el campo nino tenga el queryset correcto
        self.filters['nino'].field.queryset = Nino.objects.all().order_by('apellido', 'nombre')
        # Configuración de clases CSS para los campos
        for field_name, field in self.form.fields.items():
            if field_name not in ['fecha_desde', 'fecha_hasta', 'busqueda']:
                field.widget.attrs.update({'class': 'form-select form-select-sm'})
            
        # Ordenar los oficios por fecha de emisión descendente por defecto
        if not self.data:
            self.queryset = self.queryset.order_by('-fecha_emision')
        
        # Establecer valores por defecto
        self.form.initial = {
            'estado': '',  # Mostrar todos los estados por defecto
        }
    
    class Meta:
        model = Oficio
        fields = [
            'busqueda',
            'tipo',
            'estado',
            'fecha_desde',
            'fecha_hasta',
            'institucion',
            'juzgado',
            'nino'
        ]
    
    def filtro_busqueda(self, queryset, name, value):
        """
        Filtro personalizado para búsqueda en múltiples campos
        """
        if value:
            return queryset.filter(
                Q(expte__icontains=value) |
                Q(institucion__nombre__icontains=value) |
                Q(juzgado__nombre__icontains=value) |
                Q(oficio_ninos__nino__nombre__icontains=value) |
                Q(oficio_ninos__nino__apellido__icontains=value) |
                Q(oficio_partes__parte__nombre__icontains=value) |
                Q(oficio_partes__parte__apellido__icontains=value)
            ).distinct()
        return queryset
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuración de clases CSS para los campos
        for field_name, field in self.form.fields.items():
            if field_name not in ['fecha_desde', 'fecha_hasta', 'busqueda']:
                field.widget.attrs.update({'class': 'form-select form-select-sm'})
            
        # Ordenar los oficios por fecha de emisión descendente por defecto
        if not self.data:
            self.queryset = self.queryset.order_by('-fecha_emision')
        
        # Establecer valores por defecto
        self.form.initial = {
            'estado': '',  # Mostrar todos los estados por defecto
        }
