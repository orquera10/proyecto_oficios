from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class ProfesionalBlockAuthenticationForm(AuthenticationForm):
    """Bloquea el login de usuarios marcados como profesionales.

    Usa el hook confirm_login_allowed para validar tras la autenticación.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        'profesional_not_allowed': 'Los profesionales no pueden iniciar sesión por ahora.',
    }

    def confirm_login_allowed(self, user):
        # Mantener validaciones por defecto (is_active, etc.)
        super().confirm_login_allowed(user)
        perfil = getattr(user, 'perfil', None)
        if getattr(perfil, 'es_profesional', False):
            raise ValidationError(
                self.error_messages['profesional_not_allowed'],
                code='profesional_not_allowed',
            )

