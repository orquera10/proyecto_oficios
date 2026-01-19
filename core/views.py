from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import UsuarioPerfil


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


def _render_manual_md(text):
    lines = (text or '').splitlines()
    html_parts = []
    in_list = False

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
            html_parts.append(f'<h3>{escape(stripped[4:])}</h3>')
            continue
        if stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{escape(stripped[3:])}</h2>')
            continue
        if stripped.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h1>{escape(stripped[2:])}</h1>')
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

    return mark_safe('\n'.join(html_parts))


@login_required
def manual_usuario(request):
    manual_path = Path(settings.BASE_DIR) / 'docs' / 'usuario' / 'manual.md'
    manual_text = ''
    try:
        manual_text = manual_path.read_text(encoding='utf-8')
    except Exception:
        manual_text = 'No se pudo cargar el manual de usuario.'
    manual_html = _render_manual_md(manual_text)
    return render(request, 'core/manual_usuario.html', {
        'manual_html': manual_html,
    })
