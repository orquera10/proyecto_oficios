import unicodedata
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from .models import UsuarioPerfil
from oficios.models import Oficio


@login_required
def perfil(request):
    user = request.user
    perfil = None
    try:
        perfil = user.perfil
    except Exception:
        perfil = None
    return render(request, 'core/perfil.html', {
        'user_obj': user,
        'perfil': perfil,
    })


@login_required
def home(request):
    def _sector_nombre(user):
        try:
            sector = getattr(getattr(user, 'perfil', None), 'id_sector', None)
            raw_nombre = getattr(sector, 'nombre', '') or ''
            norm = unicodedata.normalize('NFKD', raw_nombre)
            return ''.join(c for c in norm if not unicodedata.combining(c)).lower()
        except Exception:
            return ''

    sector_nombre = _sector_nombre(request.user)
    is_coordinacion_opd = 'coordinacion opd' in sector_nombre
    # Sea flexible con acentos/variantes: basta con que contenga despacho + ninez
    is_despacho_ninez = 'despacho' in sector_nombre and 'ninez' in sector_nombre
    is_director_ninez = 'director' in sector_nombre and 'ninez' in sector_nombre
    is_coordinador = 'coordinador' in sector_nombre
    ultimos_cargados = []
    ultimos_asignados = []
    ultimos_enviados = []
    ultimos_respondidos_un_check = []
    ultimos_respondidos_sin_check = []
    ultimos_respondidos_para_director = []
    if is_coordinacion_opd:
        ultimos_cargados = list(
            Oficio.objects.filter(estado='cargado')
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
        ultimos_asignados = list(
            Oficio.objects.filter(estado='respondido')
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
    elif is_despacho_ninez:
        ultimos_asignados = list(
            Oficio.objects.filter(
                estado='respondido',
                validado_coord=True,
                validado_director=True,
            )
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
        ultimos_enviados = list(
            Oficio.objects.filter(estado='enviado')
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
    elif is_director_ninez:
        ultimos_respondidos_un_check = list(
            Oficio.objects.filter(
                estado='respondido',
                validado_coord=True,
                validado_director=False,
            )
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
        ultimos_enviados = list(
            Oficio.objects.filter(estado='enviado')
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
    elif is_coordinador:
        ultimos_respondidos_sin_check = list(
            Oficio.objects.filter(
                estado='respondido',
                validado_coord=False,
                validado_director=False,
            )
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )
        ultimos_respondidos_para_director = list(
            Oficio.objects.filter(
                estado='respondido',
                validado_coord=True,
                validado_director=False,
            )
            .select_related('institucion', 'juzgado', 'caso')
            .order_by('-creado')[:8]
        )

    return render(request, 'core/home.html', {
        'is_coordinacion_opd': is_coordinacion_opd,
        'is_despacho_ninez': is_despacho_ninez,
        'is_director_ninez': is_director_ninez,
        'is_coordinador': is_coordinador,
        'ultimos_cargados': ultimos_cargados,
        'ultimos_asignados': ultimos_asignados,
        'ultimos_enviados': ultimos_enviados,
        'ultimos_respondidos_un_check': ultimos_respondidos_un_check,
        'ultimos_respondidos_sin_check': ultimos_respondidos_sin_check,
        'ultimos_respondidos_para_director': ultimos_respondidos_para_director,
    })


def _render_manual_md(text):
    lines = (text or '').splitlines()
    html_parts = []
    toc = []
    in_list = False
    used_ids = {}

    def _unique_id(base):
        base = base or 'seccion'
        count = used_ids.get(base, 0) + 1
        used_ids[base] = count
        return base if count == 1 else f"{base}-{count}"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            title = stripped[4:]
            anchor = _unique_id(slugify(title))
            html_parts.append(f'<h3 id="{anchor}">{escape(title)}</h3>')
            toc.append({'level': 3, 'title': title, 'anchor': anchor})
            continue
        if stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            title = stripped[3:]
            anchor = _unique_id(slugify(title))
            html_parts.append(f'<h2 id="{anchor}">{escape(title)}</h2>')
            toc.append({'level': 2, 'title': title, 'anchor': anchor})
            continue
        if stripped.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            title = stripped[2:]
            anchor = _unique_id(slugify(title))
            html_parts.append(f'<h1 id="{anchor}">{escape(title)}</h1>')
            continue

        if stripped.startswith('- '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{escape(stripped[2:])}</li>')
            continue

        if in_list:
            html_parts.append('</ul>')
            in_list = False
        html_parts.append(f'<p>{escape(stripped)}</p>')

    if in_list:
        html_parts.append('</ul>')

    return mark_safe('\n'.join(html_parts)), toc


@login_required
def manual_usuario(request):
    manual_path = Path(settings.BASE_DIR) / 'docs' / 'usuario' / 'manual.md'
    manual_text = ''
    try:
        manual_text = manual_path.read_text(encoding='utf-8')
    except Exception:
        manual_text = 'No se pudo cargar el manual de usuario.'
    manual_html, manual_toc = _render_manual_md(manual_text)
    return render(request, 'core/manual_usuario.html', {
        'manual_html': manual_html,
        'manual_toc': manual_toc,
    })
