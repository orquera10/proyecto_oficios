from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify

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


@login_required
def home(request):
    return render(request, 'core/home.html')


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
