import os
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from casos.models import Caso

def oficio_upload_path(instance, filename):
    # Guarda el archivo en: MEDIA_ROOT/oficios/oficio_<id>/<filename>
    return f'oficios/oficio_{instance.id}/{filename}'

def respuesta_upload_path(instance, filename):
    # Guarda el archivo en: MEDIA_ROOT/respuestas/oficio_<oficio_id>/<filename>
    oficio_id = (
        instance.id_oficio_id
        if hasattr(instance, 'id_oficio_id') else (
            instance.id_oficio.id if getattr(instance, 'id_oficio', None) else 'sin_oficio'
        )
    )
    return f'respuestas/oficio_{oficio_id}/{filename}'

def movimiento_upload_path(instance, filename):
    # Guarda el archivo en: MEDIA_ROOT/movimientos/oficio_<oficio_id>/<filename>
    oficio_id = instance.oficio_id or (instance.oficio.id if getattr(instance, 'oficio', None) else 'sin_oficio')
    return f'movimientos/oficio_{oficio_id}/{filename}'

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
    # Nueva relación a categoría de juzgado
    id_categoria = models.ForeignKey(
        'CategoriaJuzgado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='juzgados',
        verbose_name='Categoría',
        db_column='id_categoria'
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Juzgado'
        verbose_name_plural = 'Juzgados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CategoriaJuzgado(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la categoría')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de Juzgado'
        verbose_name_plural = 'Categorías de Juzgado'
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
    fecha_envio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de envio'
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
        # Validar que si se proporciona un número de legajo, no exista otro con el mismo número

    def save(self, *args, **kwargs):
        if self.legajo:
            self.legajo = self.legajo.upper()
        if self.caratula_oficio:
            self.caratula_oficio = self.caratula_oficio.upper()
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

        # Completar fecha_envio cuando cambia a 'enviado'
        try:
            if self.id:
                prev = Oficio.objects.get(pk=self.id)
                if prev.estado != 'enviado' and self.estado == 'enviado' and not getattr(self, 'fecha_envio', None):
                    self.fecha_envio = timezone.now()
        except Oficio.DoesNotExist:
            pass

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

        # Actualizar estado del caso segun estados de sus oficios
        try:
            if self.caso_id:
                caso = self.caso
                qs = caso.oficios.all()
                # Si todos los oficios del caso estan 'enviado' => CERRADO
                if qs.exists() and not qs.filter(~Q(estado='enviado')).exists():
                    if caso.estado != 'CERRADO':
                        caso.estado = 'CERRADO'
                        caso.save(update_fields=['estado'])
                else:
                    # Si estaba CERRADO y se agrega/cambia un oficio a otro estado => EN_PROCESO
                    if caso.estado == 'CERRADO':
                        caso.estado = 'EN_PROCESO'
                        caso.save(update_fields=['estado'])
        except Exception:
            # No bloquear el guardado del oficio por errores al actualizar el caso
            pass

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
    
    archivo_pdf = models.FileField(
        upload_to=movimiento_upload_path,
        verbose_name='Archivo PDF del movimiento',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf'],
                message='Solo se permiten archivos PDF.'
            )
        ]
    )
    
    class Meta:
        verbose_name = 'Movimiento de Oficio'
        verbose_name_plural = 'Movimientos de Oficios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Movimiento {self.id} - {self.get_estado_nuevo_display()} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Si es un movimiento nuevo y no tiene estado_anterior, solo asignar si no es el estado inicial 'cargado'
        if not self.pk and not self.estado_anterior and self.oficio and self.estado_nuevo != 'cargado':
            self.estado_anterior = self.oficio.estado
        
        # Si se proporciona una institución, usarla, de lo contrario usar la del oficio
        if not self.institucion and self.oficio and self.oficio.institucion:
            self.institucion = self.oficio.institucion

        if self.detalle:
            self.detalle = self.detalle.upper()
            
        super().save(*args, **kwargs)


class Respuesta(models.Model):
    """
    Modelo para registrar respuestas a un Oficio.
    Campos: id, id_oficio, id_usuario, id_institucion, respuesta, respuesta_pdf, fecha_hora, creacion, modificacion.
    """
    id_oficio = models.ForeignKey(
        'Oficio',
        on_delete=models.CASCADE,
        related_name='respuestas',
        verbose_name='Oficio'
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        related_name='respuestas'
    )
    id_institucion = models.ForeignKey(
        'Institucion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Institución',
        related_name='respuestas'
    )
    respuesta = models.TextField(
        verbose_name='Respuesta',
        blank=True
    )
    respuesta_pdf = models.FileField(
        upload_to=respuesta_upload_path,
        verbose_name='Archivo PDF de la respuesta',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf'],
                message='Solo se permiten archivos PDF.'
            )
        ],
        help_text='Sube el archivo PDF de la respuesta. Tamaño máximo: 10MB.'
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora de la respuesta'
    )
    creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creación'
    )
    modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Modificación'
    )

    id_profesional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Profesional',
        related_name='respuestas_como_profesional'
    )

    class Meta:
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'
        ordering = ['-fecha_hora', '-creacion']

    def __str__(self):
        return f"Respuesta {self.id} de Oficio {self.id_oficio_id}"

    def save(self, *args, **kwargs):
        if self.respuesta:
            self.respuesta = self.respuesta.upper()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Eliminar el archivo fÃ­sico si existe
        if self.respuesta_pdf and hasattr(self.respuesta_pdf, 'path'):
            try:
                if os.path.isfile(self.respuesta_pdf.path):
                    os.remove(self.respuesta_pdf.path)
                    directory = os.path.dirname(self.respuesta_pdf.path)
                    if os.path.exists(directory) and not os.listdir(directory):
                        os.rmdir(directory)
            except Exception:
                pass
        super().delete(*args, **kwargs)
