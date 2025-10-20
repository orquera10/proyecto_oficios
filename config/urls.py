"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('oficios/', include(('oficios.urls', 'oficios'), namespace='oficios')),
    path('personas/', include(('personas.urls', 'personas'), namespace='personas')),
    path('casos/', include(('casos.urls', 'casos'), namespace='casos')),  # Añade esta línea
    path('accounts/login/', auth_views.LoginView.as_view(extra_context={'hide_navbar': True}), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Configuraciones de autenticación
LOGIN_REDIRECT_URL = 'oficios:list'
LOGOUT_REDIRECT_URL = 'login'  # Redirige al login después del logout

# Configuración para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
