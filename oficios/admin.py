from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as DefaultUser
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from core.models import UsuarioPerfil

from .models import (
    Institucion, Caratula,
    Juzgado, Oficio, CaratulaOficio, Respuesta
)

User = get_user_model()

# Desregistrar el User admin por defecto si ya está registrado
if admin.site.is_registered(DefaultUser):
    admin.site.unregister(DefaultUser)

# Registrar nuestro User admin personalizado
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    class UsuarioPerfilInline(admin.StackedInline):
        model = UsuarioPerfil
        can_delete = False
        extra = 0
        fields = ('id_sector', 'id_institucion')
        autocomplete_fields = ('id_sector', 'id_institucion')

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    # Campos para la edición de usuario
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información personal'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Acciones personalizadas
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuarios han sido activados.", messages.SUCCESS)
    activate_users.short_description = "Activar usuarios seleccionados"
    
    def deactivate_users(self, request, queryset):
        # Evitar desactivar al superusuario actual
        if request.user in queryset:
            self.message_user(request, "No puedes desactivar tu propio usuario.", messages.ERROR)
            queryset = queryset.exclude(pk=request.user.pk)
        
        updated = queryset.update(is_active=False)
        if updated > 0:
            self.message_user(request, f"{updated} usuarios han sido desactivados.", messages.SUCCESS)
    deactivate_users.short_description = "Desactivar usuarios seleccionados"
    
    # Personalizar visualización de estado
    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if 'is_active' in list_display:
            list_display[list_display.index('is_active')] = 'user_status'
        return list_display
    
    def user_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    user_status.short_description = 'Estado'
    user_status.admin_order_field = 'is_active'
    inlines = [UsuarioPerfilInline]

# Resto de tus modelos admin...
@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'creado', 'actualizado')
    search_fields = ('nombre', 'direccion')
    list_filter = ('creado', 'actualizado')
    ordering = ('nombre',)

@admin.register(CaratulaOficio)
class CaratulaOficioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'creado', 'actualizado')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('creado', 'actualizado')
    ordering = ('nombre',)

@admin.register(Caratula)
class CaratulaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado', 'actualizado')
    search_fields = ('nombre', 'nota')
    list_filter = ('creado', 'actualizado')
    ordering = ('nombre',)


@admin.register(Juzgado)
class JuzgadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'creado', 'actualizado')
    search_fields = ('nombre', 'direccion', 'telefono')
    list_filter = ('creado', 'actualizado')
    ordering = ('nombre',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(Oficio)
class OficioAdmin(admin.ModelAdmin):
    class RespuestaInline(admin.TabularInline):
        model = Respuesta
        extra = 0
        fields = ('id_usuario', 'id_profesional', 'id_institucion', 'respuesta', 'respuesta_pdf', 'fecha_hora', 'creacion')
        readonly_fields = ('creacion', 'modificacion')

    list_display = ('id', 'denuncia', 'legajo', 'institucion', 'juzgado', 'estado_badge', 'fecha_emision', 'fecha_vencimiento', 'usuario', 'creado')
    list_filter = ('estado', 'institucion', 'juzgado', 'usuario', 'fecha_emision', 'fecha_vencimiento')
    search_fields = ('denuncia', 'legajo', 'institucion__nombre', 'juzgado__nombre', 'usuario__username')
    list_select_related = ('institucion', 'juzgado', 'usuario')
    readonly_fields = ('creado', 'actualizado', 'estado_badge')
    date_hierarchy = 'fecha_emision'
    ordering = ('-fecha_emision',)
    inlines = [RespuestaInline]

    def estado_badge(self, obj):
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            obj.get_estado_badge_class(),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('juzgado')


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_oficio', 'id_usuario', 'id_profesional', 'id_institucion', 'fecha_hora', 'creacion')
    list_filter = ('fecha_hora', 'creacion', 'id_usuario', 'id_profesional', 'id_institucion')
    search_fields = ('id_oficio__denuncia', 'id_oficio__legajo', 'id_usuario__username', 'id_profesional__username')
    readonly_fields = ('creacion', 'modificacion')
