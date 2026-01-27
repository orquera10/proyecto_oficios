from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import Sector, UsuarioPerfil


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono')
    search_fields = ('nombre', 'direccion', 'telefono')
    ordering = ('nombre',)


@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(SimpleHistoryAdmin):
    list_display = ('usuario', 'id_sector', 'es_profesional', 'id_institucion')
    search_fields = (
        'usuario__username', 'usuario__first_name', 'usuario__last_name',
        'id_sector__nombre', 'id_institucion__nombre'
    )
    autocomplete_fields = ('usuario', 'id_sector', 'id_institucion')
    list_filter = ('es_profesional', 'id_sector', 'id_institucion')


class UsuarioPerfilInline(admin.StackedInline):
    model = UsuarioPerfil
    can_delete = False
    fk_name = 'usuario'
    autocomplete_fields = ('id_sector', 'id_institucion')
    fields = ('id_sector', 'es_profesional', 'id_institucion')


class UserAdmin(BaseUserAdmin):
    inlines = (UsuarioPerfilInline,)


# Reemplaza el admin del usuario para editar la institución desde el propio usuario
try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), UserAdmin)


try:
    HistoricalUser = get_user_model().history.model

    @admin.register(HistoricalUser)
    class HistoricalUserAdmin(admin.ModelAdmin):
        list_display = ('id', 'history_date', 'history_type', 'history_user', 'username', 'email', 'is_active')
        list_filter = ('history_type', 'history_date', 'is_active', 'is_staff', 'is_superuser')
        search_fields = ('username', 'email', 'first_name', 'last_name')
        ordering = ('-history_date', '-history_id')
        readonly_fields = [f.name for f in HistoricalUser._meta.fields]

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False
except Exception:
    pass


try:
    from .models import HistoricalUsuarioPerfil

    @admin.register(HistoricalUsuarioPerfil)
    class HistoricalUsuarioPerfilAdmin(admin.ModelAdmin):
        list_display = ('id', 'history_date', 'history_type', 'history_user', 'usuario', 'id_sector', 'es_profesional', 'id_institucion')
        list_filter = ('history_type', 'history_date', 'es_profesional', 'id_sector')
        search_fields = (
            'usuario__username', 'usuario__first_name', 'usuario__last_name',
            'id_sector__nombre', 'id_institucion__nombre'
        )
        ordering = ('-history_date', '-history_id')
        readonly_fields = [f.name for f in HistoricalUsuarioPerfil._meta.fields]

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False
except Exception:
    pass
