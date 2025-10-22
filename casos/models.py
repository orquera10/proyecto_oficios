from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
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
        verbose_name = 'Relación Caso-Niño'
        verbose_name_plural = 'Relaciones Caso-Niño'
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
    tipo_relacion = models.CharField(
        max_length=100,
        verbose_name='Tipo de relación',
        help_text='Ej: Padre, Madre, Tutor, Representante Legal, etc.'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Relación Caso-Parte'
        verbose_name_plural = 'Relaciones Caso-Parte'
        unique_together = ('caso', 'parte', 'tipo_relacion')  # Evita duplicados con el mismo tipo

    def __str__(self):
        return f"{self.caso} - {self.parte} ({self.tipo_relacion})"


class Caso(models.Model):
    TIPO_CHOICES = [
        ('MPA', 'MPA'),
        ('JUDICIAL', 'Judicial'),
    ]
    
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En Proceso'),
        ('CERRADO', 'Cerrado'),
    ]
    
    tipo = models.CharField(
        'Tipo de Caso',
        max_length=10,
        choices=TIPO_CHOICES,
        default='MPA'
    )
    
    expte = models.CharField('Expediente', max_length=50, unique=True, blank=True, null=True)
    
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
    
    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-creado']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.expte}"
        
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
