import os
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from personas.models import Nino, Parte

def oficio_upload_path(instance, filename):
    # Guarda el archivo en: MEDIA_ROOT/oficios/oficio_<id>/<filename>
    return f'oficios/oficio_{instance.id}/{filename}'

User = get_user_model()

class OficioParte(models.Model):
    """
    Modelo intermedio para la relación muchos a muchos entre Oficio y Parte.
    Permite agregar campos adicionales a la relación.
    """
    oficio = models.ForeignKey(
        'Oficio',
        on_delete=models.CASCADE,
        related_name='oficio_partes',
        verbose_name='Oficio'
    )
    parte = models.ForeignKey(
        Parte,
        on_delete=models.CASCADE,
        related_name='oficio_partes',
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
        verbose_name = 'Relación Oficio-Parte'
        verbose_name_plural = 'Relaciones Oficio-Parte'
        unique_together = ('oficio', 'parte', 'tipo_relacion')  # Evita duplicados con el mismo tipo

    def __str__(self):
        return f"{self.oficio} - {self.parte} ({self.tipo_relacion})"

class OficioNino(models.Model):
    """
    Modelo intermedio para la relación muchos a muchos entre Oficio y Nino.
    Permite agregar campos adicionales a la relación.
    """
    oficio = models.ForeignKey(
        'Oficio',
        on_delete=models.CASCADE,
        related_name='oficio_ninos',
        verbose_name='Oficio'
    )
    nino = models.ForeignKey(
        Nino,
        on_delete=models.CASCADE,
        related_name='oficio_ninos',
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
        verbose_name = 'Relación Oficio-Niño'
        verbose_name_plural = 'Relaciones Oficio-Niño'
        unique_together = ('oficio', 'nino')  # Evita duplicados

    def __str__(self):
        return f"{self.oficio} - {self.nino}"

class Institucion(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Institución')
    direccion = models.TextField(verbose_name='Dirección', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Institución'
        verbose_name_plural = 'Instituciones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Caratula(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Carátula')
    nota = models.TextField(verbose_name='Notas', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carátula'
        verbose_name_plural = 'Carátulas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class CaratulaOficio(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Carátula de Oficio')
    nota = models.TextField(verbose_name='Notas', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carátula de Oficio'
        verbose_name_plural = 'Carátulas de Oficio'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Juzgado(models.Model):
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Juzgado')
    direccion = models.TextField(verbose_name='Dirección', blank=True, null=True)
    telefono = models.CharField(max_length=50, verbose_name='Teléfono', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Juzgado'
        verbose_name_plural = 'Juzgados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Oficio(models.Model):
    TIPO_CHOICES = [
        ('MPA', 'MPA'),
        ('Judicial', 'Judicial'),
    ]
    
    ESTADO_CHOICES = [
        ('cargado', 'Cargado'),
        ('asignado', 'Asignado'),
        ('respondido', 'Respondido'),
        ('enviado', 'Enviado'),
        ('devuelto', 'Devuelto'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Oficio'
    )
    expte = models.CharField(
        max_length=50,
        verbose_name='Expediente',
        blank=True,
        null=True
    )
    institucion = models.ForeignKey(
        Institucion,
        on_delete=models.PROTECT,
        verbose_name='Institución',
        null=True,
        blank=True,
        related_name='oficios'
    )
    juzgado = models.ForeignKey(
        Juzgado,
        on_delete=models.PROTECT,
        verbose_name='Juzgado',
        null=True,
        blank=True,
        related_name='oficios'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Usuario',
        related_name='oficios',
        null=True,
        blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='cargado',
        verbose_name='Estado'
    )
    plazo_horas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Plazo en horas',
        null=True,
        blank=True
    )
    fecha_emision = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de emisión'
    )
    fecha_vencimiento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de vencimiento'
    )
    caratula = models.ForeignKey(
        Caratula,
        on_delete=models.PROTECT,
        verbose_name='Carátula',
        null=True,
        blank=True,
        related_name='oficios'
    )
    caratula_oficio = models.ForeignKey(
        CaratulaOficio,
        on_delete=models.PROTECT,
        verbose_name='Carátula de oficio',
        null=True,
        blank=True,
        related_name='oficios'
    )
    creado = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado'
    )
    actualizado = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Relación muchos a muchos con Nino a través del modelo intermedio OficioNino
    ninos = models.ManyToManyField(
        Nino,
        through='OficioNino',
        through_fields=('oficio', 'nino'),
        related_name='oficios',
        verbose_name='Niños relacionados',
        blank=True
    )
    
    # Relación muchos a muchos con Parte a través del modelo intermedio OficioParte
    partes = models.ManyToManyField(
        Parte,
        through='OficioParte',
        through_fields=('oficio', 'parte'),
        related_name='oficios',
        verbose_name='Partes relacionadas',
        blank=True
    )

    class Meta:
        verbose_name = 'Oficio'
        verbose_name_plural = 'Oficios'
        ordering = ['-fecha_emision']

    def save(self, *args, **kwargs):
        """Guardar Oficio calculando fecha_vencimiento y gestionando archivo_pdf correctamente."""
        # Calcular fecha de vencimiento según plazo_horas y fecha_emision
        if self.plazo_horas and self.fecha_emision:
            # Si es actualización, solo recalcular si cambió plazo o fecha_emision
            if self.pk:
                try:
                    old = Oficio.objects.get(pk=self.pk)
                except Oficio.DoesNotExist:
                    old = None
                if (not old or self.plazo_horas != getattr(old, 'plazo_horas', None) or self.fecha_emision != getattr(old, 'fecha_emision', None)):
                    self.fecha_vencimiento = self.fecha_emision + timezone.timedelta(hours=self.plazo_horas)
            else:
                self.fecha_vencimiento = self.fecha_emision + timezone.timedelta(hours=self.plazo_horas)

        # Manejo especial de archivo_pdf para ubicarlo en carpeta con ID
        pdf_file = getattr(self, 'archivo_pdf', None)
        if not self.pk:
            if pdf_file:
                # Guardar primero sin archivo para obtener PK
                self.archivo_pdf = None
                super().save(*args, **kwargs)
                # Ahora guardar el archivo asignándolo tras tener PK
                self.archivo_pdf = pdf_file
                super().save(update_fields=['archivo_pdf'])
                return
            else:
                # No hay archivo, guardado normal
                super().save(*args, **kwargs)
                return
        else:
            # Actualización normal (con o sin cambio de archivo)
            super().save(*args, **kwargs)

    def get_estado_badge_class(self):
        """Devuelve la clase de Bootstrap para el badge de estado."""
        estado_map = {
            'cargado': 'secondary',      # gris claro
            'asignado': 'warning',       # naranja
            'respondido': 'primary',     # azul
            'enviado': 'success',        # verde
            'devuelto': 'violet',        # violeta (custom)
        }
        return estado_map.get(self.estado, 'light')

    archivo_pdf = models.FileField(
        upload_to=oficio_upload_path,
        verbose_name='Archivo PDF del oficio',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf'],
                message='Solo se permiten archivos PDF.'
            )
        ],
        help_text='Sube el archivo PDF del oficio. Tamaño máximo: 10MB.'
    )

    def __str__(self):
        return f"Oficio {self.id} - {self.get_tipo_display()}"

    # Nota: Se removió el segundo save duplicado que sobrescribía el cálculo de fecha_vencimiento

    def delete(self, *args, **kwargs):
        # Eliminar el archivo físico si existe
        if self.archivo_pdf:
            if os.path.isfile(self.archivo_pdf.path):
                os.remove(self.archivo_pdf.path)
                # Eliminar el directorio si está vacío
                directory = os.path.dirname(self.archivo_pdf.path)
                if os.path.exists(directory) and not os.listdir(directory):
                    os.rmdir(directory)
        super().delete(*args, **kwargs)
