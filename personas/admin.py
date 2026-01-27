from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Nino, Parte


@admin.register(Nino)
class NinoAdmin(SimpleHistoryAdmin):
    list_display = ('id_ninos', 'apellido', 'nombre', 'dni', 'edad', 'fecha_nac')
    search_fields = ('apellido', 'nombre', 'dni')
    ordering = ('apellido', 'nombre')


@admin.register(Parte)
class ParteAdmin(SimpleHistoryAdmin):
    list_display = ('id_partes', 'apellido', 'nombre', 'dni', 'telefono')
    search_fields = ('apellido', 'nombre', 'dni')
    ordering = ('apellido', 'nombre')


try:
    from .models import HistoricalNino, HistoricalParte

    @admin.register(HistoricalNino)
    class HistoricalNinoAdmin(admin.ModelAdmin):
        list_display = ('id_ninos', 'history_date', 'history_type', 'history_user', 'apellido', 'nombre', 'dni')
        list_filter = ('history_type', 'history_date')
        search_fields = ('apellido', 'nombre', 'dni')
        ordering = ('-history_date', '-history_id')
        readonly_fields = [f.name for f in HistoricalNino._meta.fields]

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    @admin.register(HistoricalParte)
    class HistoricalParteAdmin(admin.ModelAdmin):
        list_display = ('id_partes', 'history_date', 'history_type', 'history_user', 'apellido', 'nombre', 'dni', 'telefono')
        list_filter = ('history_type', 'history_date')
        search_fields = ('apellido', 'nombre', 'dni')
        ordering = ('-history_date', '-history_id')
        readonly_fields = [f.name for f in HistoricalParte._meta.fields]

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False
except Exception:
    pass
