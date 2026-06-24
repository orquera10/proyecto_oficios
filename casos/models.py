from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from simple_history.models import HistoricalRecords
from personas.models import Nino, Parte

User = get_user_model()


class CasoNino(models.Model):
    """
    Modelo intermedio para la relación muchos a muchos entre Caso y Nino.
    Permite agregar campos adicionales a la relación.
    """
    caso = models.ForeignKey(
        'Caso',
        on_delete=models.CASCADE,
        related_name='caso_ninos',
        verbose_name='Caso'
    )
    nino = models.ForeignKey(
        Nino,
        on_delete=models.CASCADE,
        related_name='caso_ninos',
        verbose_name='Niño'
    )
    fecha_relacion = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de relación'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Relacion Caso-Nino'
        verbose_name_plural = 'Relaciones Caso-Nino'
        unique_together = ('caso', 'nino')  # Evita duplicados


    def __str__(self):
        return f"{self.caso} - {self.nino}"


class CasoParte(models.Model):
    """
    Modelo intermedio para la relación muchos a muchos entre Caso y Parte.
    Permite agregar campos adicionales a la relación.
    """
    caso = models.ForeignKey(
        'Caso',
        on_delete=models.CASCADE,
        related_name='caso_partes',
        verbose_name='Caso'
    )
    parte = models.ForeignKey(
        Parte,
        on_delete=models.CASCADE,
        related_name='caso_partes',
        verbose_name='Parte'
    )
    fecha_relacion = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de relación'
    )
    
    TIPO_RELACION_CHOICES = [
        ('PADRE', 'Padre'),
        ('MADRE', 'Madre'),
        ('TUTOR', 'Tutor'),
        ('ABUELO/A', 'Abuelo/a'),
        ('REFERENTE_RESGUARDO', 'Referente de Resguardo'),
        ('REPRESENTANTE_LEGAL', 'Representante Legal'),
        ('ABOGADO', 'Abogado/a'),
        ('FAMILIAR', 'Familiar'),
        ('OTRO', 'Otro'),
    ]
    
    tipo_relacion = models.CharField(
        max_length=200,
        verbose_name='Tipo de relación',
        choices=TIPO_RELACION_CHOICES
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Relacion Caso-Parte'
        verbose_name_plural = 'Relaciones Caso-Parte'
        unique_together = ('caso', 'parte')

    def __str__(self):
        return f"{self.caso} - {self.parte} ({self.tipo_relacion})"


class Caso(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En Proceso'),
        ('CERRADO', 'Cerrado'),
    ]
    
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    
    estado = models.CharField(
        'Estado',
        max_length=15,
        choices=ESTADO_CHOICES,
        default='ABIERTO'
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='casos',
        verbose_name='Usuario'
    )
    
    ninos = models.ManyToManyField(
        Nino,
        through='CasoNino',
        through_fields=('caso', 'nino'),
        related_name='casos',
        verbose_name='Niños relacionados',
        blank=True
    )
    
    partes = models.ManyToManyField(
        Parte,
        through='CasoParte',
        through_fields=('caso', 'parte'),
        related_name='casos',
        verbose_name='Partes relacionadas',
        blank=True
    )

    creado = models.DateTimeField('Creado', auto_now_add=True)
    actualizado = models.DateTimeField('Actualizado', auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-creado']
    
    def __str__(self):
        referencia = self.codigo or self.pk
        return f"Caso {referencia}"

    @classmethod
    def generar_codigo_disponible(cls, anio=None, exclude_pk=None):
        anio = anio or timezone.now().year
        queryset = cls.objects.filter(codigo__startswith='CS-', codigo__endswith=f'-{anio}')
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        ultimo = queryset.order_by('-codigo').first()
        siguiente = 1

        if ultimo and ultimo.codigo:
            try:
                siguiente = int(ultimo.codigo.split('-')[1]) + 1
            except (IndexError, ValueError):
                siguiente = 1

        return f"CS-{siguiente:05d}-{anio}"

    def _generar_codigo(self):
        anio = (self.creado.year if self.creado else timezone.now().year)
        return self.generar_codigo_disponible(anio=anio, exclude_pk=self.pk)

    def save(self, *args, **kwargs):
        codigo_en_uso = (
            not self.pk
            and self.codigo
            and type(self).objects.filter(codigo=self.codigo).exists()
        )
        if not self.codigo or codigo_en_uso:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)
        
    def get_all_movimientos(self):
        """
        Obtiene todos los movimientos de los oficios relacionados con este caso.
        Retorna un queryset ordenado por fecha de creación descendente.
        """
        from oficios.models import MovimientoOficio
        return MovimientoOficio.objects.filter(
            oficio__caso=self
        ).select_related(
            'oficio', 'usuario', 'institucion'
        ).order_by('-fecha_creacion')
