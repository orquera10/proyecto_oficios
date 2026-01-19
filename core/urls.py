from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='casos:list', permanent=False)),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('oficios/', include('oficios.urls')),  
    path('casos/', include('casos.urls', namespace='casos')),  
    path('perfil/', views.perfil, name='perfil'),
    path('manual/', views.manual_usuario, name='manual_usuario'),
]

# Add this to set the default login redirect URL
LOGIN_REDIRECT_URL = 'oficios:list'

# If you want to customize the login view, you can add:
# from django.contrib.auth.views import LoginView
# urlpatterns += [
#     path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
# ]


