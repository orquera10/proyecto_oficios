from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from .models import Nino, Parte

class NinoAPIView(View):
    """API view para obtener la lista de niños con búsqueda"""
    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '').strip()
        
        # Construir la consulta de búsqueda
        query = Q()
        if search:
            query &= (
                Q(nombre__icontains=search) |
                Q(apellido__icontains=search) |
                Q(dni__icontains=search)
            )
        
        # Obtener los niños que coincidan con la búsqueda
        ninos = Nino.objects.filter(query).order_by('apellido', 'nombre')
        
        # Preparar los datos para la respuesta JSON
        data = [{
            'id': nino.id_ninos,  # Usamos id_ninos en lugar de id
            'nombre': nino.nombre,
            'apellido': nino.apellido,
            'dni': nino.dni or '',
        } for nino in ninos]
        
        return JsonResponse(data, safe=False)

class ParteAPIView(View):
    """API view para obtener la lista de partes con búsqueda"""
    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '').strip()

        query = Q()
        if search:
            query &= (
                Q(nombre__icontains=search) |
                Q(apellido__icontains=search) |
                Q(dni__icontains=search)
            )

        partes = Parte.objects.filter(query).order_by('apellido', 'nombre')

        data = [{
            'id': parte.id_partes,
            'nombre': parte.nombre,
            'apellido': parte.apellido,
            'dni': parte.dni or '',
        } for parte in partes]

        return JsonResponse(data, safe=False)
