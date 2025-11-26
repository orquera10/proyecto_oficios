from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from oficios.models import MovimientoOficio, Oficio, Respuesta


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/dashboard.html'

    def _parse_date(self, value):
        """Convert a YYYY-MM-DD string into a date object or return None."""
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    def get_filters(self):
        """Return start/end dates from the query params, forcing a coherent range."""
        start = self._parse_date(self.request.GET.get('desde'))
        end = self._parse_date(self.request.GET.get('hasta'))
        if start and end and end < start:
            end = start
        return start, end

    def get_base_oficios(self):
        """Base queryset for all report calculations."""
        qs = Oficio.objects.select_related('institucion', 'juzgado', 'caso')
        start, end = self.get_filters()
        if start:
            qs = qs.filter(fecha_emision__date__gte=start)
        if end:
            qs = qs.filter(fecha_emision__date__lte=end)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end = self.get_filters()
        oficios_qs = self.get_base_oficios()

        today = timezone.localdate()
        upcoming_limit = today + timedelta(days=7)

        estado_labels = dict(Oficio.ESTADO_CHOICES)
        estado_counts = {key: 0 for key in estado_labels.keys()}
        for row in oficios_qs.values('estado').annotate(total=Count('id')):
            estado_counts[row['estado']] = row['total']
        estado_resumen = [
            {'clave': key, 'nombre': label, 'total': estado_counts.get(key, 0)}
            for key, label in estado_labels.items()
        ]

        serie_mensual = (
            oficios_qs
            .annotate(mes=TruncMonth('fecha_emision'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )

        top_instituciones = (
            oficios_qs
            .filter(institucion__isnull=False)
            .values('institucion__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )

        top_juzgados = (
            oficios_qs
            .filter(juzgado__isnull=False)
            .values('juzgado__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )

        movimientos_recientes = (
            MovimientoOficio.objects
            .select_related('oficio', 'institucion', 'usuario')
            .filter(oficio__in=oficios_qs)
            .order_by('-fecha_creacion')[:8]
        )

        respuestas_recientes = (
            Respuesta.objects
            .select_related('id_oficio', 'id_institucion', 'id_usuario')
            .filter(id_oficio__in=oficios_qs)
            .order_by('-fecha_hora')[:8]
        )

        context.update({
            'fecha_desde': start,
            'fecha_hasta': end,
            'kpis': {
                'total_oficios': oficios_qs.count(),
                'respondidos': oficios_qs.filter(estado='respondido').count(),
                'enviados': oficios_qs.filter(estado='enviado').count(),
                'pendientes': oficios_qs.filter(estado__in=['cargado', 'asignado']).count(),
                'vencidos': oficios_qs.filter(fecha_vencimiento__lt=today).count(),
                'proximos': oficios_qs.filter(
                    fecha_vencimiento__gte=today,
                    fecha_vencimiento__lte=upcoming_limit
                ).count(),
                'casos_vinculados': oficios_qs.exclude(caso__isnull=True).values('caso_id').distinct().count(),
            },
            'estado_labels': estado_labels,
            'estado_counts': estado_counts,
            'estado_resumen': estado_resumen,
            'serie_mensual': serie_mensual,
            'top_instituciones': top_instituciones,
            'top_juzgados': top_juzgados,
            'movimientos_recientes': movimientos_recientes,
            'respuestas_recientes': respuestas_recientes,
            'oficios_proximos_vencer': (
                oficios_qs
                .filter(fecha_vencimiento__gte=today)
                .order_by('fecha_vencimiento')[:5]
            ),
        })

        return context
