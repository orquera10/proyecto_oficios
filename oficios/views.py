from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, F
from django.views.decorators.http import require_http_methods
import unicodedata
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render

from .models import (
    Oficio, OficioMPA, OficioJudicial, Nota, Institucion, Caratula, Juzgado, MovimientoOficio, Respuesta
)
from casos.models import Caso
from .forms import OficioForm, OficioMPAForm, OficioJudicialForm, NotaForm
from .forms_respuesta import RespuestaForm
from .filters import OficioFilter
from .permissions import is_coordinacion_opd


def buscar_ninos(request):
    """
    Vista para buscar niños por nombre, apellido o documento.
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


@login_required
def referencias_home(request):
    context = {
        'juzgados_url': reverse_lazy('oficios:juzgado_list'),
        'instituciones_url': reverse_lazy('oficios:institucion_list'),
        'categorias_url': reverse_lazy('oficios:categoria_list'),
        'profesionales_url': reverse_lazy('oficios:profesional_list'),
        'can_manage_referencias': not is_coordinacion_opd(request.user),
    }
    return render(request, 'oficios/referencias_home.html', context)

# Vista de listado de oficios
class OficioListView(LoginRequiredMixin, ListView):
    model = Oficio
    template_name = 'oficios/oficio_list.html'
    context_object_name = 'oficios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = OficioFilter(self.request.GET, queryset=queryset)
        # Orden por fecha de vencimiento ascendente (nulos al final), luego por emisiÃƒÂ³n desc
        return (
            self.filterset.qs
            .select_related('institucion', 'juzgado', 'usuario')
            .order_by(F('fecha_vencimiento').asc(nulls_last=True), '-fecha_emision')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['now'] = now
        context['filter'] = getattr(self, 'filterset', OficioFilter(queryset=self.get_queryset()))
        try:
            qs = self.filterset.qs if hasattr(self, 'filterset') else self.get_queryset()
            context['total_vencidos'] = qs.filter(fecha_vencimiento__lt=now).exclude(estado='enviado').count()
            context['total_asignados'] = qs.filter(estado='asignado').count()
            context['total_respondidos'] = qs.filter(estado='respondido').count()
            context['total_enviados'] = qs.filter(estado='enviado').count()
        except Exception:
            context['total_vencidos'] = 0
            context['total_asignados'] = 0
            context['total_respondidos'] = 0
            context['total_enviados'] = 0
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
        now = timezone.now()
        context['now'] = now
        # Reusar el mismo formulario de filtros, mostrando el filterset aplicado
        estado = self.kwargs.get('estado')
        context['filter'] = getattr(self, 'filterset', OficioFilter(self.request.GET, queryset=self.get_queryset()))
        context['estado_actual'] = estado
        try:
            qs = self.filterset.qs if hasattr(self, 'filterset') else self.get_queryset()
            context['total_vencidos'] = qs.filter(fecha_vencimiento__lt=now).exclude(estado='enviado').count()
            context['total_asignados'] = qs.filter(estado='asignado').count()
            context['total_respondidos'] = qs.filter(estado='respondido').count()
            context['total_enviados'] = qs.filter(estado='enviado').count()
        except Exception:
            context['total_vencidos'] = 0
            context['total_asignados'] = 0
            context['total_respondidos'] = 0
            context['total_enviados'] = 0
        return context

class DocumentoTipoSelectView(LoginRequiredMixin, View):
    template_name = 'oficios/documento_tipo_select.html'

    def dispatch(self, request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)
        raw_nombre = getattr(getattr(perfil, 'id_sector', None), 'nombre', '') or ''
        norm = unicodedata.normalize('NFKD', raw_nombre)
        sector_nombre = ''.join(c for c in norm if not unicodedata.combining(c)).lower()
        if 'coordinacion opd' in sector_nombre:
            messages.error(request, 'No tiene permisos para crear documentos.')
            return redirect('oficios:list')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        caso_id = request.GET.get('caso')
        tipos = [
            {
                'key': 'mpa',
                'label': 'Oficio MPA',
                'icon': 'fas fa-scale-balanced',
                'enabled': True,
                'url': self._tipo_url('mpa', caso_id),
            },
            {
                'key': 'judicial',
                'label': 'Oficio Judicial',
                'icon': 'fas fa-gavel',
                'enabled': True,
                'url': self._tipo_url('judicial', caso_id),
            },
            {
                'key': 'nacional',
                'label': 'Oficio Nacional',
                'icon': 'fas fa-landmark',
                'enabled': False,
                'url': '#',
            },
            {
                'key': 'nota',
                'label': 'Nota',
                'icon': 'fas fa-file-lines',
                'enabled': True,
                'url': self._tipo_url('nota', caso_id),
            },
        ]
        return render(request, self.template_name, {'tipos': tipos, 'caso_id': caso_id})

    def _tipo_url(self, tipo, caso_id=None):
        url = reverse('oficios:create_tipo', kwargs={'tipo': tipo})
        if caso_id:
            url = f'{url}?caso={caso_id}'
        return url


class OficioCreateView(LoginRequiredMixin, CreateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'
    tipo_config = {
        'mpa': {
            'model': OficioMPA,
            'form': OficioMPAForm,
            'titulo': 'Nuevo Oficio MPA',
            'detalle': 'OFICIO MPA CREADO',
            'success': 'El oficio MPA se ha creado correctamente.',
        },
        'judicial': {
            'model': OficioJudicial,
            'form': OficioJudicialForm,
            'titulo': 'Nuevo Oficio Judicial',
            'detalle': 'OFICIO JUDICIAL CREADO',
            'success': 'El oficio judicial se ha creado correctamente.',
        },
        'nota': {
            'model': Nota,
            'form': NotaForm,
            'titulo': 'Nueva Nota',
            'detalle': 'NOTA CREADA',
            'success': 'La nota se ha creado correctamente.',
        },
    }
    
    def dispatch(self, request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)
        raw_nombre = getattr(getattr(perfil, 'id_sector', None), 'nombre', '') or ''
        norm = unicodedata.normalize('NFKD', raw_nombre)
        sector_nombre = ''.join(c for c in norm if not unicodedata.combining(c)).lower()
        if 'coordinacion opd' in sector_nombre:
            messages.error(request, 'No tiene permisos para crear oficios.')
            return redirect('oficios:list')
        if self.get_tipo_documento() not in self.tipo_config:
            return redirect(self.get_tipo_selector_url())
        return super().dispatch(request, *args, **kwargs)

    def get_tipo_documento(self):
        return self.kwargs.get('tipo')

    def get_tipo_selector_url(self):
        url = reverse('oficios:create')
        caso_id = self.request.GET.get('caso')
        if caso_id:
            url = f'{url}?caso={caso_id}'
        return url

    def get_model_config(self):
        return self.tipo_config[self.get_tipo_documento()]

    def get_form_class(self):
        return self.get_model_config()['form']
    
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
        context['titulo'] = self.get_model_config()['titulo']
        context['tipo_documento'] = self.get_tipo_documento()
        context['selector_url'] = self.get_tipo_selector_url()
        return context
    @transaction.atomic
    def form_valid(self, form):
        instituciones = list(form.cleaned_data.get("instituciones") or [])
        creados = []
        archivo = form.cleaned_data.get("archivo_pdf")
        plantilla = form.save(commit=False)
        # Each destination needs a fresh parent and child row, not a reused
        # multi-table inheritance instance with only its child PK cleared.
        datos = {
            field.attname: getattr(plantilla, field.attname)
            for field in plantilla._meta.concrete_fields
            if not field.primary_key and not field.auto_created
            and field.name not in ('codigo', 'creado', 'actualizado', 'archivo_pdf')
        }
        for institucion in instituciones or [None]:
            obj = type(plantilla)(**datos)
            obj.usuario = self.request.user
            obj.institucion = institucion
            obj._plazo_unidad = plantilla._plazo_unidad
            obj._fecha_vencimiento_manual = plantilla._fecha_vencimiento_manual
            if archivo:
                archivo.seek(0)
                obj.archivo_pdf = archivo
            obj.save()
            MovimientoOficio.objects.create(
                oficio=obj,
                usuario=self.request.user,
                estado_anterior=None,
                estado_nuevo='cargado',
                validado_coord=obj.validado_coord,
                validado_director=obj.validado_director,
                detalle=self.get_model_config()['detalle'],
                institucion=institucion,
            )
            creados.append(obj)

        if plantilla.caso and plantilla.caso.estado == 'ABIERTO':
            plantilla.caso.estado = 'EN_PROCESO'
            plantilla.caso.save()

        if len(creados) == 1:
            self.object = creados[0]
            messages.success(self.request, self.get_model_config()['success'])
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
            # Casos para asignar desde modal (últimos 50)
            'casos_opciones': Caso.objects.all().order_by('-creado')[:50],
        })
        context['puede_enviar_revision'] = _puede_enviar_revision(self.request.user, self.object)
        context['es_coordinacion_opd'] = is_coordinacion_opd(self.request.user)
        context['correccion_en_curso'] = self.object.revision_pendiente or self.object.estado == 'en_revision'
        context['ultima_revision'] = self.object.movimientos.filter(estado_nuevo='en_revision').first()
        return context


class OficioAsignarCasoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio, pk=kwargs['pk'])
        caso_id = request.POST.get('caso_id')
        try:
            caso = get_object_or_404(Caso, pk=caso_id)
            oficio.caso = caso
            oficio.save(update_fields=['caso'])
            messages.success(request, 'El caso fue asignado al oficio correctamente.')
        except Exception:
            messages.error(request, 'No se pudo asignar el caso seleccionado.')
        return redirect('oficios:detail', pk=oficio.pk)


class OficioDesvincularCasoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio, pk=kwargs['pk'])
        try:
            if oficio.caso_id:
                oficio.caso = None
                oficio.save(update_fields=['caso'])
                messages.success(request, 'El oficio fue desvinculado del caso correctamente.')
            else:
                messages.info(request, 'El oficio no tiene un caso asignado actualmente.')
        except Exception:
            messages.error(request, 'No se pudo desvincular el caso del oficio.')
        return redirect('oficios:detail', pk=oficio.pk)


class OficioUpdateView(LoginRequiredMixin, UpdateView):
    model = Oficio
    form_class = OficioForm
    template_name = 'oficios/oficio_form.html'

    def get_success_url(self):
        return reverse_lazy('oficios:detail', kwargs={'pk': self.object.pk})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Oficio'
        return context
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'El oficio se ha actualizado correctamente.')
        return super().form_valid(form)


class OficioEnviarView(LoginRequiredMixin, View):
    """
    Vista para manejar el movimiento de un oficio a un nuevo estado.
    """
    def enviar_asignacion_email(self, oficio, destinatario, asunto, cuerpo):
        try:
            if oficio.numero_interno:
                cuerpo = f'{cuerpo}\n\nNúmero interno: {oficio.numero_interno}'
            correo = EmailMessage(
                subject=asunto,
                body=cuerpo,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                to=[destinatario],
            )
            with oficio.archivo_pdf.open('rb') as adjunto:
                correo.attach(oficio.archivo_pdf.name.rsplit('/', 1)[-1], adjunto.read())
            if correo.send(fail_silently=False) != 1:
                raise RuntimeError('El servidor no aceptó el correo.')
        except Exception:
            messages.warning(self.request, 'El oficio quedó asignado, pero no se pudo enviar el correo a la institución.')
        else:
            messages.success(self.request, f'Copia del oficio enviada a {destinatario}.')

    @method_decorator(login_required)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio.objects.select_for_update(), pk=kwargs['pk'])
        nuevo_estado = request.POST.get('nuevo_estado')
        institucion_id = request.POST.get('institucion')
        detalle = request.POST.get('detalle', '').strip()
        archivo_pdf = request.FILES.get('archivo_pdf')
        incompetencia = request.POST.get('incompetencia')
        enviar_email = request.POST.get('enviar_email') == 'on'
        asunto_email = (request.POST.get('asunto_email') or '').strip()
        cuerpo_email = request.POST.get('cuerpo_email', f'Se adjunta una copia del oficio {oficio.codigo}.').strip()

        if nuevo_estado == 'en_revision':
            messages.error(request, 'Utilice Enviar a revisión e indique las correcciones.')
            return redirect('oficios:detail', pk=oficio.pk)
        if oficio.revision_pendiente or oficio.estado == 'en_revision':
            if (not is_coordinacion_opd(request.user) or nuevo_estado != 'asignado'
                    or oficio.estado not in ('en_revision', 'devuelto', 'derivado')
                    or str(incompetencia).lower() in ('1', 'true', 'on', 'yes', 'si')):
                messages.error(request, 'Solo Coordinación OPD puede reasignar el oficio para su corrección.')
                return redirect('oficios:detail', pk=oficio.pk)
            if not detalle:
                revision = oficio.movimientos.filter(estado_nuevo='en_revision').first()
                detalle = revision.detalle if revision else 'Corregir informe'
        if nuevo_estado == 'enviado' and not (oficio.estado == 'respondido' and oficio.validado_coord and oficio.validado_director):
            messages.error(request, 'El oficio debe contar con ambos vistos buenos antes de enviarse.')
            return redirect('oficios:detail', pk=oficio.pk)
        
        # Validar que el nuevo estado sea vÃƒÂ¡lido
        if nuevo_estado not in dict(oficio.ESTADO_CHOICES):
            messages.error(request, 'El estado seleccionado no es valido.')
            return redirect('oficios:detail', pk=oficio.pk)
            
        # Validar que el estado sea diferente al actual
        if nuevo_estado == oficio.estado:
            messages.warning(request, 'El oficio ya se encuentra en el estado seleccionado.')
            return redirect('oficios:detail', pk=oficio.pk)

        try:
            # Resolver institucion por incompetencia (si aplica)
            es_incompetencia = incompetencia is not None and str(incompetencia).lower() in ('1', 'true', 'on', 'yes', 'si')
            if es_incompetencia:
                nuevo_estado = 'incompetencia'
                detalle = 'EL OFICIO SE MARCO COMO INCOMPETENCIA'
                try:
                    institucion = Institucion.objects.get(nombre__iexact='O.P.D.N.N.A. SEDE')
                except Institucion.DoesNotExist:
                    messages.error(request, 'No se encontro la institucion O.P.D.N.N.A. SEDE.')
                    return redirect('oficios:detail', pk=oficio.pk)
            else:
                # Obtener la institucion (si no viene, usar la del oficio)
                if institucion_id:
                    institucion = Institucion.objects.get(pk=institucion_id)
                else:
                    institucion = oficio.institucion

            if not institucion and nuevo_estado in ('asignado', 'enviado', 'incompetencia'):
                messages.error(request, 'Debe seleccionar una institucion.')
                return redirect('oficios:detail', pk=oficio.pk)

            if enviar_email:
                error = None
                destinatario = ((institucion.email or '').strip() if institucion else '')
                if not destinatario:
                    destinatario = (request.POST.get('email_institucion') or '').strip()
                if nuevo_estado not in ('asignado', 'incompetencia'):
                    error = 'El envío por correo está disponible al asignar el oficio.'
                elif not asunto_email or len(asunto_email) > 200 or '\n' in asunto_email or '\r' in asunto_email:
                    error = 'Ingrese un asunto de hasta 200 caracteres, en una sola línea.'
                elif not cuerpo_email or len(cuerpo_email) > 10000:
                    error = 'Ingrese el mensaje del correo (hasta 10000 caracteres).'
                elif not oficio.archivo_pdf:
                    error = 'Adjunte el archivo del oficio antes de solicitar su envío por correo.'
                else:
                    try:
                        validate_email(destinatario)
                    except ValidationError:
                        error = 'Complete un correo válido para la institución seleccionada.'
                if error:
                    messages.error(request, error)
                    return redirect('oficios:detail', pk=oficio.pk)
            
            # Definir detalle por defecto si viene vacÃ­o
            if not detalle:
                if nuevo_estado == 'asignado':
                    detalle_final = 'Se asignó a institucion'
                elif nuevo_estado == 'incompetencia':
                    detalle_final = 'El oficio se marco como incompetencia'
                elif nuevo_estado == 'enviado':
                    detalle_final = 'Oficio enviado a agente'
                else:
                    detalle_final = (
                        f"Cambio de estado de {oficio.get_estado_display()} a "
                        f"{dict(oficio.ESTADO_CHOICES).get(nuevo_estado, nuevo_estado)} "
                        f"por {request.user.get_full_name() or request.user.username}"
                    )
            else:
                detalle_final = detalle
            detalle_final = (detalle_final or '').upper()

            # Crear registro del movimiento (guardar PDF si se adjunta)
            MovimientoOficio.objects.create(
                oficio=oficio,
                usuario=request.user,
                estado_anterior=oficio.estado,
                estado_nuevo=nuevo_estado,
                validado_coord=oficio.validado_coord,
                validado_director=oficio.validado_director,
                institucion=institucion,
                detalle=detalle_final,
                archivo_pdf=archivo_pdf if archivo_pdf else None,
            )
            
            # Actualizar estado del oficio (sin tocar el PDF del oficio)
            # Actualizar estado del oficio (y fecha de envío si corresponde)
            oficio.estado = nuevo_estado
            oficio.institucion = institucion
            update_fields = ['estado', 'institucion']
            if incompetencia is not None:
                oficio.incompetencia = str(incompetencia).lower() in ('1', 'true', 'on', 'yes', 'si')
                update_fields.append('incompetencia')
            if nuevo_estado == 'enviado' and not getattr(oficio, 'fecha_envio', None):
                oficio.fecha_envio = timezone.now()
                update_fields.append('fecha_envio')
            oficio.save(update_fields=update_fields)

            if nuevo_estado == 'enviado':
                messages.success(request, 'Se envió correctamente.')

            if enviar_email:
                transaction.on_commit(lambda: self.enviar_asignacion_email(
                    oficio, destinatario, asunto_email, cuerpo_email,
                ))
            if nuevo_estado in ('asignado', 'incompetencia'):
                messages.success(request, 'El oficio fue asignado correctamente.')

        except Institucion.DoesNotExist:
            messages.error(request, 'La institucion seleccionada no es valida.')
        except Exception as e:
            transaction.set_rollback(True)
            messages.error(request, f'Ocurrio Â³ un error al procesar el movimiento: {str(e)}')
        
        return redirect('oficios:detail', pk=oficio.pk)


class OficioEnviarRevisionView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio.objects.select_for_update(), pk=kwargs['pk'])
        if not _puede_enviar_revision(request.user, oficio):
            messages.error(request, 'No tiene permisos para enviar este oficio a revisión en su estado actual.')
            return redirect('oficios:detail', pk=oficio.pk)
        detalle = (request.POST.get('detalle') or '').strip()
        if not detalle:
            messages.error(request, 'Indique las correcciones solicitadas.')
            return redirect('oficios:detail', pk=oficio.pk)
        oficio.estado = 'en_revision'
        oficio.revision_pendiente = True
        oficio.validado_coord = False
        oficio.validado_director = False
        oficio.save(update_fields=['estado', 'revision_pendiente', 'validado_coord', 'validado_director'])
        MovimientoOficio.objects.create(
            oficio=oficio, usuario=request.user, institucion=oficio.institucion,
            estado_anterior='respondido', estado_nuevo='en_revision',
            detalle=detalle, validado_coord=False, validado_director=False,
        )
        messages.success(request, 'Oficio enviado a revisión. Coordinación OPD podrá reasignarlo.')
        return redirect('oficios:detail', pk=oficio.pk)


class OficioValidarCoordView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio.objects.select_for_update(), pk=kwargs.get('pk'))
        if not _is_coordinador(request.user):
            messages.error(request, 'No tiene permisos para validar este oficio.')
            return redirect('oficios:detail', pk=oficio.pk)
        if oficio.estado != 'respondido':
            messages.error(request, 'Solo se puede validar un oficio en estado Respondido.')
            return redirect('oficios:detail', pk=oficio.pk)
        oficio.validado_coord = not oficio.validado_coord
        if not oficio.validado_coord:
            oficio.validado_director = False
        oficio.save(update_fields=['validado_coord', 'validado_director'])
        try:
            detalle_input = (request.POST.get('detalle') or '').strip()
            if oficio.validado_coord:
                default_detalle = 'VALIDACION COORDINACION: OK'
                prefix = '✓'
            else:
                default_detalle = 'VALIDACION COORDINACION: REVOCADA'
                prefix = ''
            detalle_body = detalle_input if detalle_input else default_detalle
            detalle = (f'{prefix} {detalle_body}'.strip() if prefix else detalle_body)
            detalle = (detalle or '').upper()
            MovimientoOficio.objects.create(
                oficio=oficio,
                usuario=request.user,
                estado_anterior=oficio.estado,
                estado_nuevo=oficio.estado,
                institucion=oficio.institucion,
                validado_coord=oficio.validado_coord,
                validado_director=oficio.validado_director,
                detalle=detalle,
            )
        except Exception:
            pass
        messages.success(request, 'Validación de coordinación actualizada.')
        return redirect('oficios:detail', pk=oficio.pk)


class OficioValidarDirectorView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        oficio = get_object_or_404(Oficio.objects.select_for_update(), pk=kwargs.get('pk'))
        if not _is_director(request.user):
            messages.error(request, 'No tiene permisos para validar este oficio.')
            return redirect('oficios:detail', pk=oficio.pk)
        if oficio.estado != 'respondido':
            messages.error(request, 'Solo se puede validar un oficio en estado Respondido.')
            return redirect('oficios:detail', pk=oficio.pk)
        if not oficio.validado_coord:
            messages.error(request, 'Primero debe validar coordinación.')
            return redirect('oficios:detail', pk=oficio.pk)
        oficio.validado_director = not oficio.validado_director
        oficio.save(update_fields=['validado_director'])
        try:
            detalle_input = (request.POST.get('detalle') or '').strip()
            if oficio.validado_director:
                default_detalle = 'VALIDACION DIRECCION: OK'
                prefix = '✓✓'
            else:
                default_detalle = 'VALIDACION DIRECCION: REVOCADA'
                prefix = ''
            detalle_body = detalle_input if detalle_input else default_detalle
            detalle = (f'{prefix} {detalle_body}'.strip() if prefix else detalle_body)
            detalle = (detalle or '').upper()
            MovimientoOficio.objects.create(
                oficio=oficio,
                usuario=request.user,
                estado_anterior=oficio.estado,
                estado_nuevo=oficio.estado,
                institucion=oficio.institucion,
                validado_coord=oficio.validado_coord,
                validado_director=oficio.validado_director,
                detalle=detalle,
            )
        except Exception:
            pass
        messages.success(request, 'Validación de dirección actualizada.')
        return redirect('oficios:detail', pk=oficio.pk)


class OficioDeleteView(LoginRequiredMixin, DeleteView):
    model = Oficio
    template_name = 'oficios/oficio_confirm_delete.html'
    success_url = reverse_lazy('oficios:list')

    def dispatch(self, request, *args, **kwargs):
        if not _is_admin_like(request.user):
            messages.error(request, 'No tiene permisos para eliminar oficios.')
            return redirect('oficios:detail', pk=kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'El oficio ha sido eliminado correctamente.')
        return super().delete(request, *args, **kwargs)


class RespuestaCreateView(LoginRequiredMixin, CreateView):
    model = Respuesta
    form_class = RespuestaForm
    template_name = 'oficios/respuesta_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['oficio'] = self.oficio
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if _is_despacho(request.user):
            messages.error(request, 'No tiene permisos para responder oficios.')
            return redirect('oficios:detail', pk=kwargs.get('pk'))
        # Validar que el oficio exista
        self.oficio = get_object_or_404(Oficio, pk=kwargs['pk'])
        if self.oficio.revision_pendiente or self.oficio.estado == 'en_revision':
            if not is_coordinacion_opd(request.user) or self.oficio.estado != 'asignado':
                messages.error(request, 'Coordinación OPD debe reasignar el oficio antes de cargar la respuesta corregida.')
                return redirect('oficios:detail', pk=self.oficio.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        # Preseleccionar instituciÃƒÂ³n del oficio si estÃƒÂ¡ disponible
        if self.oficio and self.oficio.institucion_id:
            initial['id_institucion'] = self.oficio.institucion_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['oficio'] = self.oficio
        return context
    @transaction.atomic
    def form_valid(self, form):
        self.oficio = get_object_or_404(Oficio.objects.select_for_update(), pk=self.oficio.pk)
        if self.oficio.revision_pendiente or self.oficio.estado == 'en_revision':
            if not is_coordinacion_opd(self.request.user) or self.oficio.estado != 'asignado':
                return redirect('oficios:detail', pk=self.oficio.pk)
        obj = form.save(commit=False)
        obj.id_oficio = self.oficio
        obj.id_usuario = self.request.user
        obj.id_institucion = obj.id_institucion or self.oficio.institucion
        obj.save()
        nuevo_estado = ('derivado' if form.cleaned_data.get('derivar') else
                        'devuelto' if form.cleaned_data.get('devolver') else 'respondido')
        anterior = self.oficio.estado
        self.oficio.estado = nuevo_estado
        self.oficio.validado_coord = False
        self.oficio.validado_director = False
        if nuevo_estado == 'respondido':
            self.oficio.revision_pendiente = False
        if obj.id_institucion:
            self.oficio.institucion = obj.id_institucion
        self.oficio.save(update_fields=[
            'estado', 'institucion', 'validado_coord', 'validado_director', 'revision_pendiente',
        ])
        MovimientoOficio.objects.create(
            oficio=self.oficio, usuario=self.request.user,
            estado_anterior=anterior, estado_nuevo=nuevo_estado,
            validado_coord=False, validado_director=False,
            institucion=self.oficio.institucion,
            detalle=(obj.respuesta or 'Se respondio el oficio').strip()[:200],
        )
        messages.success(self.request, 'Respuesta registrada. Estado: ' + self.oficio.get_estado_display())
        return HttpResponseRedirect(reverse('oficios:detail', kwargs={'pk': self.oficio.pk}))


def _puede_enviar_revision(user, oficio):
    return oficio.estado == 'respondido' and (
        (_is_coordinador(user) and not oficio.validado_coord)
        or (_is_director(user) and oficio.validado_coord and not oficio.validado_director)
    )


def _is_admin_like(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        nombre = getattr(sector, 'nombre', '') or ''
        nombre = nombre.strip().lower()
        folded = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
        if folded in ('informatica', 'coordinador'):
            return True
        return ('director' in folded) and ('ninez' in folded)
    except Exception:
        return False


def _is_coordinador(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        nombre = getattr(sector, 'nombre', '') or ''
        nombre = nombre.strip().lower()
        folded = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
        return folded == 'coordinador'
    except Exception:
        return False


def _is_director(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        nombre = getattr(sector, 'nombre', '') or ''
        nombre = nombre.strip().lower()
        folded = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
        return ('director' in folded) and ('ninez' in folded)
    except Exception:
        return False


def _is_despacho(user):
    try:
        sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
        nombre = (getattr(sector, 'nombre', '') or '').strip()
        name_lower = nombre.lower()
        folded = ''.join(c for c in unicodedata.normalize('NFD', name_lower) if unicodedata.category(c) != 'Mn')
        return ('despacho' in name_lower) and ('ninez' in folded)
    except Exception:
        return False
