from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Caso


@admin.register(Caso)
class CasoAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'tipo', 'expte', 'estado', 'usuario', 'creado', 'actualizado')
    list_filter = ('tipo', 'estado', 'creado', 'actualizado')
    search_fields = ('expte', 'usuario__username', 'usuario__first_name', 'usuario__last_name')
    ordering = ('-creado',)


try:
    from .models import HistoricalCaso

    @admin.register(HistoricalCaso)
    class HistoricalCasoAdmin(admin.ModelAdmin):
        list_display = ('id', 'history_date', 'history_type', 'history_user', 'tipo', 'expte', 'estado', 'usuario')
        list_filter = ('history_type', 'history_date', 'tipo', 'estado')
        search_fields = ('expte', 'usuario__username', 'usuario__first_name', 'usuario__last_name')
        ordering = ('-history_date', '-history_id')
        readonly_fields = [f.name for f in HistoricalCaso._meta.fields]

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False
except Exception:
    pass
