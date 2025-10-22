import os
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from casos.models import Caso

def oficio_upload_path(instance, filename):
    # Guarda el archivo en: MEDIA_ROOT/oficios/oficio_<id>/<filename>
    return f'oficios/oficio_{instance.id}/{filename}'

User = get_user_model()

# Se han eliminado los modelos intermedios OficioParte y OficioNino
# ya que la relación ahora se manejará a través del modelo Caso

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
    descripcion = models.TextField(verbose_name='Descripción', blank=True, null=True)
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
    ESTADO_CHOICES = [
        ('cargado', 'Cargado'),
        ('asignado', 'Asignado'),
        ('respondido', 'Respondido'),
        ('enviado', 'Enviado'),
        ('devuelto', 'Devuelto'),
    ]
    nro_oficio = models.CharField(
        max_length=50,
        verbose_name='Número de Oficio',
        unique=True,
        blank=True,
        null=True
    )
    denuncia = models.CharField(
        max_length=50,
        verbose_name='Número de Denuncia',
        blank=True,
        null=True,
        help_text='Número de denuncia relacionada al oficio'
    )
    legajo = models.CharField(
        max_length=50,
        verbose_name='Número de Legajo',
        blank=True,
        null=True,
        help_text='Número de legajo relacionado al oficio'
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
    caratula_oficio = models.CharField(
        max_length=255,
        verbose_name='Carátula de Oficio',
        blank=True,
        null=True
    )
    creado = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado'
    )
    actualizado = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Relación con Caso
    caso = models.ForeignKey(
        Caso,
        on_delete=models.SET_NULL,
        related_name='oficios',
        verbose_name='Caso relacionado',
        null=True,
        blank=True,
        help_text='Caso al que pertenece este oficio'
    )

    class Meta:
        verbose_name = 'Oficio'
        verbose_name_plural = 'Oficios'
        ordering = ['-fecha_emision']

    def clean(self):
        super().clean()
        # Validar que si se proporciona un número de denuncia, no exista otro con el mismo número
        if self.denuncia:
            # Buscar si existe otro oficio con la misma denuncia (excluyendo el actual)
            queryset = Oficio.objects.filter(denuncia=self.denuncia)
            if self.pk:  # Si es una actualización, excluir el registro actual
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                raise ValidationError({
                    'denuncia': 'Ya existe un oficio con este número de denuncia.'
                })
                
        # Validar que si se proporciona un número de legajo, no exista otro con el mismo número
        if self.legajo:
            # Buscar si existe otro oficio con el mismo legajo (excluyendo el actual)
            queryset = Oficio.objects.filter(legajo=self.legajo)
            if self.pk:  # Si es una actualización, excluir el registro actual
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                raise ValidationError({
                    'legajo': 'Ya existe un oficio con este número de legajo.'
                })

    def save(self, *args, **kwargs):
        # Validar el modelo antes de guardar
        self.full_clean()
        
        # Si es un oficio nuevo (no tiene ID) y tiene plazo_horas, calcula la fecha de vencimiento
        if not self.id and self.plazo_horas:
            self.fecha_vencimiento = timezone.now() + timezone.timedelta(hours=self.plazo_horas)
        
        # Si el oficio ya existe, verifica si se modificó el plazo_horas
        elif self.id and self.plazo_horas:
            # Obtener el oficio actual de la base de datos
            old_instance = Oficio.objects.get(pk=self.id)
            if old_instance.plazo_horas != self.plazo_horas:
                self.fecha_vencimiento = timezone.now() + timezone.timedelta(hours=self.plazo_horas)
        
        # Si no se especifica un usuario, usar el usuario actual
        if not self.usuario_id and hasattr(self, '_current_user'):
            self.usuario = self._current_user
        
        # Si el oficio ya existe y tiene un archivo PDF, verificar si se está actualizando
        if self.id and self.archivo_pdf:
            try:
                # Obtener el oficio actual de la base de datos
                old_instance = Oficio.objects.get(pk=self.id)
                # Si el archivo ha cambiado, eliminar el archivo anterior
                if old_instance.archivo_pdf and old_instance.archivo_pdf != self.archivo_pdf:
                    # Eliminar el archivo anterior del sistema de archivos
                    if os.path.isfile(old_instance.archivo_pdf.path):
                        os.remove(old_instance.archivo_pdf.path)
            except Oficio.DoesNotExist:
                pass  # Es un nuevo oficio, no hay archivo anterior que eliminar
        
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
        return f"Oficio {self.id}"

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


class MovimientoOficio(models.Model):
    """
    Modelo para rastrear los movimientos y cambios de estado de los oficios.
    """
    # Usando los mismos estados que el modelo Oficio para mantener consistencia
    ESTADO_CHOICES = [
        ('cargado', 'Cargado'),
        ('asignado', 'Asignado'),
        ('respondido', 'Respondido'),
        ('enviado', 'Enviado'),
        ('devuelto', 'Devuelto'),
    ]
    
    oficio = models.ForeignKey(
        'Oficio',
        on_delete=models.CASCADE,
        related_name='movimientos',
        verbose_name='Oficio'
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        related_name='movimientos_oficios'
    )
    
    estado_anterior = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Estado Anterior'
    )
    
    estado_nuevo = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        verbose_name='Nuevo Estado'
    )
    
    detalle = models.TextField(
        verbose_name='Detalle del movimiento',
        help_text='Descripción detallada del movimiento o cambio realizado',
        blank=True
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    institucion = models.ForeignKey(
        'Institucion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Institución',
        related_name='movimientos_oficios'
    )
    
    class Meta:
        verbose_name = 'Movimiento de Oficio'
        verbose_name_plural = 'Movimientos de Oficios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Movimiento {self.id} - {self.get_estado_nuevo_display()} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Si es un movimiento nuevo y no tiene estado_anterior, usar el estado actual del oficio
        if not self.pk and not self.estado_anterior and self.oficio:
            self.estado_anterior = self.oficio.estado
        
        # Si se proporciona una institución, usarla, de lo contrario usar la del oficio
        if not self.institucion and self.oficio and self.oficio.institucion:
            self.institucion = self.oficio.institucion
            
        super().save(*args, **kwargs)
