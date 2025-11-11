from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, F
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import (
    Oficio, Institucion, Caratula, Juzgado, MovimientoOficio, Respuesta
)
from .forms import OficioForm
from .forms_respuesta import RespuestaForm
from .filters import OficioFilter


def buscar_ninos(request):
    """
    Vista para buscar niÃ±os por nombre, apellido o documento.
    Devuelve resultados en formato JSON para ser usados en autocompletado.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Buscar por nombre, apellido o documento
    ninos = Nino.objects.filter(
        Q(nombres__icontains=query) |
        Q(apellidos__icontains=query) |
        Q(documento_identidad__icontains=query)
    ).distinct()[:10]  # Limitar a 10 resultados
    
    # Preparar los datos para la respuesta JSON
    results = [{
        'id': nino.id,
        'nombres': nino.nombres,
        'apellidos': nino.apellidos,
        'documento_identidad': nino.documento_identidad or '',
        'fecha_nacimiento': nino.fecha_nacimiento.strftime('%d/%m/%Y') if nino.fecha_nacimiento else ''
    } for nino in ninos]
    
    return JsonResponse(results, safe=False)

# Vista de listado de oficios
class OficioListView(LoginRequiredMixin, ListView):
    model = Oficio
    template_name = 'oficios/oficio_list.html'
    context_object_name = 'oficios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = OficioFilter(self.request.GET, queryset=queryset)
        # Orden por fecha de vencimiento ascendente (nulos al final), luego por emisiÃ³n desc
        return (
            self.filterset.qs
            .select_related('institucion', 'juzgado', 'usuario')
            .order_by(F('fecha_vencimiento').asc(nulls_last=True), '-fecha_emision')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        context['filter'] = getattr(self, 'filterset', OficioFilter(queryset=self.get_queryset()))
        return context


class OficioEstadoListView(LoginRequiredMixin, ListView):
    model = Oficio
    template_name = 'oficios/oficio_list.html'
    context_object_name = 'oficios'
    paginate_by = 20

    def get_queryset(self):
        estado = self.kwargs.get('estado')
        base_qs = Oficio.objects.select_related('institucion', 'juzgado', 'usuario').filter(estado=estado)
        # Aplicar filtros enviados por GET sobre el queryset ya filtrado por estado
        self.filterset = OficioFilter(self.request.GET, queryset=base_qs)
        return self.filterset.qs.order_by(F('fecha_vencimiento').asc(nulls_last=True), '-fecha_emision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        # Reusar el mismo formulario de filtros, mostrando el filterset aplicado
        estado = self.kwargs.get('estado')
        context['filter'] = getattr(self, 'filterset', OficioFilter(self.request.GET, queryset=self.get_queryset()))
        context['estado_actual'] = estado
        return context

class OficioCreateView(LoginRequiredMixin, CreateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        caso_id = self.request.GET.get('caso')
        if caso_id:
            initial['caso'] = caso_id
        return initial
    
    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    def form_valid(self, form):
        instituciones = form.cleaned_data.get("instituciones")
        creados = []
        archivo = form.cleaned_data.get("archivo_pdf")
        for inst in instituciones:
            obj = form.save(commit=False)
            obj.pk = None
            obj.usuario = self.request.user
            obj.institucion = inst
            if archivo is not None:
                try:
                    archivo.seek(0)
                except Exception:
                    pass
                obj.archivo_pdf = archivo
            obj.save()

            try:
                MovimientoOficio.objects.create(
                    oficio=obj,
                    usuario=self.request.user,
                    estado_anterior=None,
                    estado_nuevo='cargado',
                    detalle='Oficio creado',
                    institucion=obj.institucion
                )
            except Exception:
                pass

            try:
                if obj.caso and getattr(obj.caso, 'estado', None) == 'ABIERTO':
                    obj.caso.estado = 'EN_PROCESO'
                    obj.caso.save()
            except Exception:
                pass
            creados.append(obj)

        if len(creados) == 1:
            self.object = creados[0]
            messages.success(self.request, 'El oficio se ha creado correctamente.')
            return HttpResponseRedirect(reverse('oficios:detail', kwargs={'pk': self.object.pk}))
        else:
            # Redirigir al caso si existe, si no al listado
            caso = None
            try:
                caso = creados[0].caso if creados and getattr(creados[0], 'caso', None) else None
            except Exception:
                caso = None
            messages.success(self.request, f'Se crearon {len(creados)} oficios correctamente.')
            if caso:
                return HttpResponseRedirect(reverse('casos:detail', kwargs={'pk': caso.pk}))
            return HttpResponseRedirect(reverse('oficios:list'))
class OficioDetailView(LoginRequiredMixin, DetailView):
    model = Oficio
    template_name = 'oficios/oficio_detail.html'
    context_object_name = 'oficio'
    
    def get_queryset(self):
        return super().get_queryset().select_related('institucion', 'juzgado', 'usuario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar la fecha actual para comparar con la fecha de vencimiento
        from django.utils import timezone
        from .models import Institucion
        
        context.update({
            'now': timezone.now(),
            'instituciones': Institucion.objects.all().order_by('nombre'),
        })
        return context


class OficioUpdateView(LoginRequiredMixin, UpdateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    
    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'El oficio se ha actualizado correctamente.')
        return super().form_valid(form)


class OficioEnviarView(LoginRequiredMixin, View):
    """
    Vista para manejar el movimiento de un oficio a un nuevo estado.
    """
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio, pk=kwargs['pk'])
        nuevo_estado = request.POST.get('nuevo_estado')
        institucion_id = request.POST.get('institucion')
        detalle = request.POST.get('detalle', '').strip()
        archivo_pdf = request.FILES.get('archivo_pdf')
        
        # Validar que el nuevo estado sea vÃ¡lido
        if nuevo_estado not in dict(oficio.ESTADO_CHOICES):
            messages.error(request, 'El estado seleccionado no es valido.')
            return redirect('oficios:detail', pk=oficio.pk)
            
        # Validar que el estado sea diferente al actual
        if nuevo_estado == oficio.estado:
            messages.warning(request, 'El oficio ya se encuentra en el estado seleccionado.')
            return redirect('oficios:detail', pk=oficio.pk)
        
        try:
            # Obtener la institucion
            institucion = Institucion.objects.get(pk=institucion_id)
            
            # Crear registro del movimiento (guardar PDF si se adjunta)
            MovimientoOficio.objects.create(
                oficio=oficio,
                usuario=request.user,
                estado_anterior=oficio.estado,
                estado_nuevo=nuevo_estado,
                institucion=institucion,
                detalle=detalle or f'Cambio de estado de {oficio.get_estado_display()} a {dict(oficio.ESTADO_CHOICES).get(nuevo_estado, nuevo_estado)} por {request.user.get_full_name() or request.user.username}',
                archivo_pdf=archivo_pdf if archivo_pdf else None,
            )
            
            # Actualizar estado del oficio (sin tocar el PDF del oficio)
            oficio.estado = nuevo_estado
            oficio.institucion = institucion
            oficio.save(update_fields=['estado', 'institucion'])
            
            messages.success(request, f'El oficio ha sido movido a "{dict(oficio.ESTADO_CHOICES).get(nuevo_estado, nuevo_estado)}" correctamente.')
            
        except institucion.DoesNotExist:
            messages.error(request, 'la institucion seleccionada no es vÃ¡lida.')
        except Exception as e:
            messages.error(request, f'Ocurrio ³ un error al procesar el movimiento: {str(e)}')
        
        return redirect('oficios:detail', pk=oficio.pk)


class OficioDeleteView(LoginRequiredMixin, DeleteView):
    model = Oficio
    template_name = 'oficios/oficio_confirm_delete.html'
    success_url = reverse_lazy('oficios:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'El oficio ha sido eliminado correctamente.')
        return super().delete(request, *args, **kwargs)


class RespuestaCreateView(LoginRequiredMixin, CreateView):
    model = Respuesta
    form_class = RespuestaForm
    template_name = 'oficios/respuesta_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Validar que el oficio exista
        self.oficio = get_object_or_404(Oficio, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        # Preseleccionar instituciÃ³n del oficio si estÃ¡ disponible
        if self.oficio and self.oficio.institucion_id:
            initial['id_institucion'] = self.oficio.institucion_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['oficio'] = self.oficio
        return context
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.id_oficio = self.oficio
        obj.id_usuario = self.request.user
        # Si no se envÃ­a instituciÃ³n, usar la del oficio por conveniencia
        if not obj.id_institucion and self.oficio.institucion:
            obj.id_institucion = self.oficio.institucion
        obj.save()

        # Registrar movimiento y, segÃºn opciÃ³n, mantener estado en 'asignado' o pasar a 'devuelto'
        try:
            institucion_mov = obj.id_institucion or self.oficio.institucion
            detalle_mov = obj.respuesta.strip()[:200] if obj.respuesta else 'Se registrÃ³ una respuesta.'
            devolver = form.cleaned_data.get('devolver')
            nuevo_estado = 'devuelto' if devolver else 'asignado'

            MovimientoOficio.objects.create(
                oficio=self.oficio,
                usuario=self.request.user,
                estado_anterior=self.oficio.estado,
                estado_nuevo=nuevo_estado,
                institucion=institucion_mov,
                detalle=detalle_mov,
            )

            # Actualizar estado solo si se devuelve; si no, mantener asignado
            update_fields = []
            if devolver:
                self.oficio.estado = 'devuelto'
                update_fields.append('estado')
            if institucion_mov and (self.oficio.institucion_id != getattr(institucion_mov, 'id', None)):
                self.oficio.institucion = institucion_mov
                update_fields.append('institucion')
            if update_fields:
                self.oficio.save(update_fields=update_fields)
        except Exception:
            # No bloquear el flujo por un error en el movimiento
            pass

        if form.cleaned_data.get('devolver'):
            messages.success(self.request, 'La respuesta se registrÃ³ y el oficio pasÃ³ a Devuelto.')
        else:
            messages.success(self.request, 'La respuesta se registrÃ³. El oficio permanece Asignado para revisiÃ³n.')
        return HttpResponseRedirect(reverse('oficios:detail', kwargs={'pk': self.oficio.pk}))




