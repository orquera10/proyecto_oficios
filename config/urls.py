"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.forms import ProfesionalBlockAuthenticationForm
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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

# Configuraciones de autenticacion
LOGIN_REDIRECT_URL = 'oficios:list'
LOGOUT_REDIRECT_URL = 'login'  # Redirige al login despues del logout

# Configuracion para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
