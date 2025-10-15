from django.db import models

class Nino(models.Model):
    id_ninos = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    fecha_nac = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = 'Niño'
        verbose_name_plural = 'Niños'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Parte(models.Model):
    id_partes = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Parte'
        verbose_name_plural = 'Partes'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
