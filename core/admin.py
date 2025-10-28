from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Sector, UsuarioPerfil


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono')
    search_fields = ('nombre', 'direccion', 'telefono')
    ordering = ('nombre',)


@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'id_sector')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'id_sector__nombre')
    autocomplete_fields = ('usuario', 'id_sector')
