from django.contrib.auth.backends import ModelBackend


class NoProfesionalesBackend(ModelBackend):
    """Bloquea la autenticación de usuarios marcados como profesionales.

    Se aplica tanto al admin como al login normal, porque usa user_can_authenticate.
    """

    def user_can_authenticate(self, user):
        can = super().user_can_authenticate(user)
        if not can:
            return False
        try:
            perfil = getattr(user, 'perfil', None)
            if getattr(perfil, 'es_profesional', False):
                return False
        except Exception:
            # No bloquear por errores inesperados
            pass
        return True

