from django.urls import path
from . import views
from .juzgado_views import (
    JuzgadoListView, JuzgadoCreateView, JuzgadoDetailView, JuzgadoUpdateView, JuzgadoDeleteView
)
from .institucion_views import (
    InstitucionListView, InstitucionCreateView, InstitucionDetailView, InstitucionUpdateView, InstitucionDeleteView
)
from .profesional_views import (
    ProfesionalListView, ProfesionalCreateView, ProfesionalDetailView, ProfesionalUpdateView, ProfesionalDeleteView
)

app_name = 'oficios'

urlpatterns = [
    path('', views.OficioListView.as_view(), name='list'),
    path('nuevo/', views.OficioCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OficioDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.OficioUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.OficioDeleteView.as_view(), name='delete'),
    path('<int:pk>/responder/', views.RespuestaCreateView.as_view(), name='responder'),
    # Listados por estado
    path('estado/<str:estado>/', views.OficioEstadoListView.as_view(), name='list_by_estado'),
    
    # API para búsqueda de niños
    path('api/ninos/buscar/', views.buscar_ninos, name='buscar_ninos'),
    
    # Acción para marcar oficio como enviado
    path('<int:pk>/enviar/', views.OficioEnviarView.as_view(), name='enviar'),

    # CRUD Juzgados (Agentes)
    path('juzgados/', JuzgadoListView.as_view(), name='juzgado_list'),
    path('juzgados/nuevo/', JuzgadoCreateView.as_view(), name='juzgado_create'),
    path('juzgados/<int:pk>/', JuzgadoDetailView.as_view(), name='juzgado_detail'),
    path('juzgados/<int:pk>/editar/', JuzgadoUpdateView.as_view(), name='juzgado_update'),
    path('juzgados/<int:pk>/eliminar/', JuzgadoDeleteView.as_view(), name='juzgado_delete'),

    # CRUD Instituciones
    path('instituciones/', InstitucionListView.as_view(), name='institucion_list'),
    path('instituciones/nuevo/', InstitucionCreateView.as_view(), name='institucion_create'),
    path('instituciones/<int:pk>/', InstitucionDetailView.as_view(), name='institucion_detail'),
    path('instituciones/<int:pk>/editar/', InstitucionUpdateView.as_view(), name='institucion_update'),
    path('instituciones/<int:pk>/eliminar/', InstitucionDeleteView.as_view(), name='institucion_delete'),

    # CRUD Profesionales (usuarios con perfil.es_profesional)
    path('profesionales/', ProfesionalListView.as_view(), name='profesional_list'),
    path('profesionales/nuevo/', ProfesionalCreateView.as_view(), name='profesional_create'),
    path('profesionales/<int:pk>/', ProfesionalDetailView.as_view(), name='profesional_detail'),
    path('profesionales/<int:pk>/editar/', ProfesionalUpdateView.as_view(), name='profesional_update'),
    path('profesionales/<int:pk>/eliminar/', ProfesionalDeleteView.as_view(), name='profesional_delete'),
]
