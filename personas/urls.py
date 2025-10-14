from django.urls import path
from django.shortcuts import render
from django.urls import reverse
from . import views

def personas_home(request):
    context = {
        'ninos_url': reverse('personas:nino_list'),
        'partes_url': reverse('personas:parte_list'),
    }
    return render(request, 'personas/home.html', context)

app_name = 'personas'

urlpatterns = [
    path('', personas_home, name='home'),  # Página principal de personas
    # URLs para Niños
    path('ninos/', views.NinoListView.as_view(), name='nino_list'),
    path('ninos/ver/<int:pk>/', views.NinoDetailView.as_view(), name='nino_detail'),
    path('ninos/nuevo/', views.NinoCreateView.as_view(), name='nino_create'),
    path('ninos/editar/<int:pk>/', views.NinoUpdateView.as_view(), name='nino_update'),
    path('ninos/eliminar/<int:pk>/', views.NinoDeleteView.as_view(), name='nino_delete'),
    
    # URLs para Partes
    path('partes/', views.ParteListView.as_view(), name='parte_list'),
    path('partes/nuevo/', views.ParteCreateView.as_view(), name='parte_create'),
    path('partes/editar/<int:pk>/', views.ParteUpdateView.as_view(), name='parte_update'),
    path('partes/eliminar/<int:pk>/', views.ParteDeleteView.as_view(), name='parte_delete'),
]
