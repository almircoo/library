from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

# Crear router para los ViewSets
router = DefaultRouter()
router.register(r"autores", views.AutorViewSet)
router.register(r"categorias", views.CategoriaViewSet)
router.register(r"editoriales", views.EditorialViewSet)
router.register(r"libros", views.LibroViewSet)
router.register(r"prestamos", views.PrestamoViewSet)
router.register(r"resenas", views.ResenaViewSet)
router.register(r"reservas", views.ReservaViewSet)
router.register(r"notificaciones", views.NotificacionViewSet)

urlpatterns = [
    # Autenticación JWT
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/registro/", views.registro_usuario, name="registro"),
    # Perfil de usuario
    path("perfil/", views.perfil_usuario, name="perfil"),
    path("perfil/actualizar/", views.actualizar_perfil, name="actualizar_perfil"),
    path("perfil/estadisticas/", views.estadisticas_usuario, name="estadisticas"),
    # Pantalla de inicio
    path("inicio/", views.inicio, name="inicio"),
    # Incluir rutas del router
    path("", include(router.urls)),
]
