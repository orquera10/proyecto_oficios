from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Register history tracking for the auth user model.
        try:
            from django.contrib.auth import get_user_model
            from simple_history import register

            register(get_user_model())
        except Exception:
            # Avoid breaking startup if simple_history isn't available yet.
            pass
