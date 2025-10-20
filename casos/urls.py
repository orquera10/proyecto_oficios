from django.urls import path
from . import views

app_name = 'casos'

urlpatterns = [
    path('', views.CasoListView.as_view(), name='list'),
    path('nuevo/', views.CasoCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CasoDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.CasoUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.CasoDeleteView.as_view(), name='delete'),
]
