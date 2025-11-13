from django.db import models
from django.conf import settings


class Sector(models.Model):
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    direccion = models.TextField(blank=True, null=True, verbose_name='Dirección')
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name='Teléfono')

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class UsuarioPerfil(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuario'
    )
    id_sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Sector'
    )
    es_profesional = models.BooleanField(
        default=False,
        verbose_name='Es profesional'
    )
    id_institucion = models.ForeignKey(
        'oficios.Institucion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfiles',
        verbose_name='Institucion'
    )

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
