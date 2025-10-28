from django.shortcuts import render
from django.contrib.auth.decorators import login_required
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
