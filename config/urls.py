"""
URL configuration for core project.
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.forms import ProfesionalBlockAuthenticationForm
from django.conf import settings
from django.conf.urls.static import static

base_urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('oficios/', include(('oficios.urls', 'oficios'), namespace='oficios')),
    path('personas/', include(('personas.urls', 'personas'), namespace='personas')),
    path('casos/', include(('casos.urls', 'casos'), namespace='casos')),
    path('reportes/', include(('reportes.urls', 'reportes'), namespace='reportes')),
    path('accounts/login/', auth_views.LoginView.as_view(
        form_class=ProfesionalBlockAuthenticationForm,
        extra_context={'hide_navbar': True}
    ), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
]

URL_PREFIX = os.getenv('APP_URL_PREFIX', '').strip('/')
if URL_PREFIX:
    urlpatterns = [
        path(f"{URL_PREFIX}/", include((base_urlpatterns, 'config'))),
        *base_urlpatterns,
    ]
else:
    urlpatterns = base_urlpatterns

# Configuraciones de autenticacion
LOGIN_REDIRECT_URL = 'oficios:list'
LOGOUT_REDIRECT_URL = 'login'  # Redirige al login despues del logout

# Configuracion para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
