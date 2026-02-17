from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Library System"

    def ready(self):
        """Importar signals cuando la app esté lista"""
        import core.signals
