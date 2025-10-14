"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include core app URLs
    path('oficios/', include(('oficios.urls', 'oficios'), namespace='oficios')),  # Include oficios app URLs with namespace
    path('personas/', include(('personas.urls', 'personas'), namespace='personas')),  # Include personas app URLs with namespace
    # URLs de autenticación
    path('accounts/', include('django.contrib.auth.urls')),
]

# Configuraciones de autenticación
LOGIN_REDIRECT_URL = 'oficios:list'
LOGOUT_REDIRECT_URL = 'login'  # Redirige al login después del logout
