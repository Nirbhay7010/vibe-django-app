from django.apps import AppConfig

class VibeappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vibeapp'

    def ready(self):
        import vibeapp.signals
