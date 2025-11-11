from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Sector, UsuarioPerfil


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono')
    search_fields = ('nombre', 'direccion', 'telefono')
    ordering = ('nombre',)


@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'id_sector', 'id_institucion')
    search_fields = (
        'usuario__username', 'usuario__first_name', 'usuario__last_name',
        'id_sector__nombre', 'id_institucion__nombre'
    )
    autocomplete_fields = ('usuario', 'id_sector', 'id_institucion')


class UsuarioPerfilInline(admin.StackedInline):
    model = UsuarioPerfil
    can_delete = False
    fk_name = 'usuario'
    autocomplete_fields = ('id_sector', 'id_institucion')


class UserAdmin(BaseUserAdmin):
    inlines = (UsuarioPerfilInline,)


# Reemplaza el admin del usuario para editar la institución desde el propio usuario
try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), UserAdmin)
