from django.urls import path
from . import views

app_name = 'oficios'

urlpatterns = [
    path('', views.OficioListView.as_view(), name='list'),
    path('nuevo/', views.OficioCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OficioDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.OficioUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.OficioDeleteView.as_view(), name='delete'),
    # Listados por estado
    path('estado/<str:estado>/', views.OficioEstadoListView.as_view(), name='list_by_estado'),
    
    # API para búsqueda de niños
    path('api/ninos/buscar/', views.buscar_ninos, name='buscar_ninos'),
    
    # Acción para marcar oficio como enviado
    path('<int:pk>/enviar/', views.OficioEnviarView.as_view(), name='enviar'),
]
