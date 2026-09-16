import django_filters
from django import forms
from django.db.models import Q, Value
from django.db.models.functions import Replace
from .models import Caso, CasoNino, CasoParte
from personas.models import Nino, Parte


class CasoFilter(django_filters.FilterSet):
    busqueda = django_filters.CharFilter(
        method='filtro_busqueda',
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Identificador del caso (CS-00001-2026), DNI o nombre'
        })
    )

    estado = django_filters.ChoiceFilter(
        field_name='estado',
        label='Estado',
        choices=Caso.ESTADO_CHOICES,
        empty_label='Todos los estados',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    nino = django_filters.ModelChoiceFilter(
        label='Niño/a',
        queryset=Nino.objects.all().order_by('apellido', 'nombre'),
        field_name='caso_ninos__nino',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    dni_nino = django_filters.CharFilter(
        method='filtro_dni_nino',
        label='DNI del niño/a',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'DNI completo, con o sin puntos',
            'inputmode': 'numeric',
        })
    )

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

    codigo_oficio = django_filters.CharFilter(
        method='filtro_oficio', label='Identificador del oficio',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: OF-00010-2026'}),
    )
    numero_interno = django_filters.CharFilter(
        method='filtro_oficio', label='Número interno del oficio',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 7543'}),
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
            'estado',
            'nino',
            'dni_nino',
            'codigo_oficio',
            'numero_interno',
            'fecha_desde',
            'fecha_hasta'
        ]

    def filtro_oficio(self, queryset, name, value):
        from oficios.models import Oficio

        # Both identifiers must belong to the same related document.
        criterios = {
            f'{campo_modelo}__icontains': self.form.cleaned_data[campo]
            for campo, campo_modelo in (('codigo_oficio', 'codigo'), ('numero_interno', 'numero_interno'))
            if self.form.cleaned_data.get(campo)
        }
        oficios = Oficio.objects.filter(**criterios).exclude(caso_id=None)
        return queryset.filter(pk__in=oficios.values('caso_id'))

    def filtro_dni_nino(self, queryset, name, value):
        dni = value.replace('.', '').replace(' ', '')
        if not dni:
            return queryset.none()
        ninos = Nino.objects.annotate(
            dni_normalizado=Replace(Replace('dni', Value('.'), Value('')), Value(' '), Value(''))
        ).filter(dni_normalizado=dni)
        return queryset.filter(ninos__in=ninos).distinct()

    def filtro_busqueda(self, queryset, name, value):
        if not value:
            return queryset

        q_objects = Q(codigo__icontains=value)

        ninos = Nino.objects.filter(
            Q(dni__icontains=value) |
            Q(nombre__icontains=value) |
            Q(apellido__icontains=value)
        ).values_list('id_ninos', flat=True)

        partes = Parte.objects.filter(
            Q(dni__icontains=value) |
            Q(nombre__icontains=value) |
            Q(apellido__icontains=value)
        ).values_list('id_partes', flat=True)

        if ninos.exists():
            casos_con_ninos = CasoNino.objects.filter(nino_id__in=ninos).values_list('caso_id', flat=True)
            q_objects |= Q(id__in=casos_con_ninos)

        if partes.exists():
            casos_con_partes = CasoParte.objects.filter(parte_id__in=partes).values_list('caso_id', flat=True)
            q_objects |= Q(id__in=casos_con_partes)

        return queryset.filter(q_objects).distinct()
