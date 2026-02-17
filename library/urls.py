from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Configuración de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Biblioteca API",
        default_version="v1",
        description="API para gestión de biblioteca - Préstamos, Reservas, Catálogo de Libros",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="almirco@mail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API
    path("api/v1/", include("core.urls")),
    # Documentación Swagger/OpenAPI
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
