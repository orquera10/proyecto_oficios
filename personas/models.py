from django.db import models

class Nino(models.Model):
    id_ninos = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    domicilio_principal = models.CharField(max_length=200, blank=True, null=True)
    domicilio_secundario = models.CharField(max_length=200, blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    fecha_nac = models.DateField(blank=True, null=True)
    edad = models.PositiveIntegerField(blank=True, null=True, help_text='Edad en años, si no se conoce la fecha de nacimiento')

    class Meta:
        verbose_name = 'Niño'
        verbose_name_plural = 'Niños'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.apellido:
            self.apellido = self.apellido.upper()
        if self.domicilio_principal:
            self.domicilio_principal = self.domicilio_principal.upper()
        if self.domicilio_secundario:
            self.domicilio_secundario = self.domicilio_secundario.upper()
        super().save(*args, **kwargs)
        
    @property
    def edad_calculada(self):
        # Si no hay fecha de nacimiento, devolver la edad manual si existe
        if not self.fecha_nac:
            return self.edad
            
        # Calcular edad a partir de la fecha de nacimiento
        from datetime import date
        today = date.today()
        age = today.year - self.fecha_nac.year - ((today.month, today.day) < (self.fecha_nac.month, self.fecha_nac.day))
        return max(0, age)

class Parte(models.Model):
    id_partes = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Parte'
        verbose_name_plural = 'Partes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.apellido:
            self.apellido = self.apellido.upper()
        if self.direccion:
            self.direccion = self.direccion.upper()
        super().save(*args, **kwargs)
