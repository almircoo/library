from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Autor,
    Categoria,
    Editorial,
    Libro,
    Notificacion,
    PerfilUsuario,
    Prestamo,
    Resena,
    Reserva,
)
from .serializers import (
    AutorSerializer,
    CategoriaSerializer,
    EditorialSerializer,
    EstadisticasUsuarioSerializer,
    LibroDetailSerializer,
    LibroListSerializer,
    NotificacionSerializer,
    PerfilUsuarioSerializer,
    PrestamoSerializer,
    ResenaSerializer,
    ReservaSerializer,
    UserRegistrationSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AutorViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar autores"""

    queryset = Autor.objects.all()
    serializer_class = AutorSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "biografia", "nacionalidad"]
    ordering_fields = ["nombre", "fecha_nacimiento"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["get"])
    def libros(self, request, pk=None):
        """Obtiene todos los libros de un autor"""
        autor = self.get_object()
        libros = autor.libros.all()
        serializer = LibroListSerializer(libros, many=True)
        return Response(serializer.data)


class CategoriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar categorías"""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "descripcion"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["get"])
    def libros(self, request, pk=None):
        """Obtiene todos los libros de una categoría"""
        categoria = self.get_object()
        libros = categoria.libros.all()

        # Aplicar filtros adicionales
        disponible = request.query_params.get("disponible", None)
        if disponible is not None:
            if disponible.lower() == "true":
                libros = libros.filter(cantidad_disponible__gt=0)

        serializer = LibroListSerializer(libros, many=True)
        return Response(serializer.data)


class EditorialViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar editoriales"""

    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "pais"]
    ordering = ["nombre"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class LibroViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar libros"""

    queryset = (
        Libro.objects.all()
        .select_related("autor", "editorial")
        .prefetch_related("categorias")
    )
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["titulo", "autor__nombre", "descripcion", "isbn"]
    ordering_fields = ["titulo", "anio_publicacion", "fecha_agregado"]
    ordering = ["-fecha_agregado"]

    def get_serializer_class(self):
        if self.action == "list":
            return LibroListSerializer
        return LibroDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "buscar", "populares", "nuevos"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros personalizados
        categoria = self.request.query_params.get("categoria", None)
        autor = self.request.query_params.get("autor", None)
        disponible = self.request.query_params.get("disponible", None)
        es_popular = self.request.query_params.get("es_popular", None)
        es_nuevo = self.request.query_params.get("es_nuevo", None)
        anio_desde = self.request.query_params.get("anio_desde", None)
        anio_hasta = self.request.query_params.get("anio_hasta", None)

        if categoria:
            queryset = queryset.filter(categorias__id=categoria)

        if autor:
            queryset = queryset.filter(autor__id=autor)

        if disponible is not None:
            if disponible.lower() == "true":
                queryset = queryset.filter(cantidad_disponible__gt=0)

        if es_popular is not None:
            if es_popular.lower() == "true":
                queryset = queryset.filter(es_popular=True)

        if es_nuevo is not None:
            if es_nuevo.lower() == "true":
                queryset = queryset.filter(es_nuevo=True)

        if anio_desde:
            queryset = queryset.filter(anio_publicacion__gte=anio_desde)

        if anio_hasta:
            queryset = queryset.filter(anio_publicacion__lte=anio_hasta)

        return queryset.distinct()

    @action(detail=False, methods=["get"])
    def populares(self, request):
        """Obtiene libros populares"""
        libros = self.get_queryset().filter(es_popular=True)[:10]
        serializer = self.get_serializer(libros, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def nuevos(self, request):
        """Obtiene nuevas adquisiciones"""
        libros = (
            self.get_queryset().filter(es_nuevo=True).order_by("-fecha_agregado")[:10]
        )
        serializer = self.get_serializer(libros, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def buscar(self, request):
        """Búsqueda avanzada de libros"""
        query = request.query_params.get("q", "")

        if query:
            queryset = self.get_queryset().filter(
                Q(titulo__icontains=query)
                | Q(autor__nombre__icontains=query)
                | Q(descripcion__icontains=query)
                | Q(isbn__icontains=query)
            )
        else:
            queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LibroListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LibroListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def prestar(self, request, pk=None):
        """Crear un préstamo para un libro"""
        libro = self.get_object()

        serializer = PrestamoSerializer(
            data={"libro": libro.id}, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reservar(self, request, pk=None):
        """Crear una reserva para un libro"""
        libro = self.get_object()

        serializer = ReservaSerializer(
            data={"libro": libro.id}, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrestamoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar préstamos"""

    queryset = Prestamo.objects.all().select_related("usuario", "libro", "libro__autor")
    serializer_class = PrestamoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["fecha_prestamo", "fecha_devolucion_esperada"]
    ordering = ["-fecha_prestamo"]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Los usuarios normales solo ven sus préstamos
        if not user.is_staff:
            queryset = queryset.filter(usuario=user)

        # Filtro por estado
        estado = self.request.query_params.get("estado", None)
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Obtiene préstamos activos del usuario"""
        prestamos = self.get_queryset().filter(
            usuario=request.user, estado__in=["activo", "renovado"]
        )
        serializer = self.get_serializer(prestamos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def historial(self, request):
        """Obtiene historial de préstamos del usuario"""
        prestamos = self.get_queryset().filter(usuario=request.user)

        page = self.paginate_queryset(prestamos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(prestamos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def renovar(self, request, pk=None):
        """Renovar un préstamo"""
        prestamo = self.get_object()

        if prestamo.usuario != request.user and not request.user.is_staff:
            return Response(
                {"error": "No tienes permiso para renovar este préstamo"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if prestamo.renovar():
            # Crear notificación
            Notificacion.objects.create(
                usuario=prestamo.usuario,
                tipo="prestamo",
                titulo="Préstamo renovado",
                mensaje=f'Has renovado el préstamo del libro "{prestamo.libro.titulo}". Nueva fecha de devolución: {prestamo.fecha_devolucion_esperada.strftime("%d/%m/%Y")}',
            )

            serializer = self.get_serializer(prestamo)
            return Response(serializer.data)

        return Response(
            {"error": "No se puede renovar este préstamo"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        """Devolver un libro"""
        prestamo = self.get_object()

        if not request.user.is_staff:
            return Response(
                {"error": "Solo el personal puede marcar libros como devueltos"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if prestamo.devolver():
            # Crear notificación
            Notificacion.objects.create(
                usuario=prestamo.usuario,
                tipo="devolucion",
                titulo="Libro devuelto",
                mensaje=f'Has devuelto el libro "{prestamo.libro.titulo}". ¡Gracias!',
            )

            # Verificar si hay reservas pendientes
            reserva = (
                Reserva.objects.filter(libro=prestamo.libro, estado="pendiente")
                .order_by("fecha_reserva")
                .first()
            )

            if reserva:
                reserva.estado = "notificado"
                reserva.fecha_notificacion = timezone.now()
                reserva.fecha_expiracion = timezone.now() + timedelta(days=3)
                reserva.save()

                Notificacion.objects.create(
                    usuario=reserva.usuario,
                    tipo="reserva",
                    titulo="Libro disponible",
                    mensaje=f'El libro "{prestamo.libro.titulo}" que reservaste ya está disponible. Tienes 3 días para recogerlo.',
                )

            serializer = self.get_serializer(prestamo)
            return Response(serializer.data)

        return Response(
            {"error": "No se puede devolver este préstamo"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResenaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar reseñas"""

    queryset = Resena.objects.all().select_related("usuario", "libro")
    serializer_class = ResenaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por libro
        libro_id = self.request.query_params.get("libro", None)
        if libro_id:
            queryset = queryset.filter(libro__id=libro_id)

        # Filtrar por usuario
        if not self.request.user.is_staff:
            usuario_id = self.request.query_params.get("usuario", None)
            if usuario_id:
                queryset = queryset.filter(usuario__id=usuario_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        if (
            serializer.instance.usuario != self.request.user
            and not self.request.user.is_staff
        ):
            raise PermissionError("No tienes permiso para editar esta reseña")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.usuario != self.request.user and not self.request.user.is_staff:
            raise PermissionError("No tienes permiso para eliminar esta reseña")
        instance.delete()


class ReservaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar reservas"""

    queryset = Reserva.objects.all().select_related("usuario", "libro", "libro__autor")
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if not user.is_staff:
            queryset = queryset.filter(usuario=user)

        estado = self.request.query_params.get("estado", None)
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    @action(detail=False, methods=["get"])
    def activas(self, request):
        """Obtiene reservas activas del usuario"""
        reservas = self.get_queryset().filter(
            usuario=request.user, estado__in=["pendiente", "notificado"]
        )
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Cancelar una reserva"""
        reserva = self.get_object()

        if reserva.usuario != request.user and not request.user.is_staff:
            return Response(
                {"error": "No tienes permiso para cancelar esta reserva"},
                status=status.HTTP_403_FORBIDDEN,
            )

        reserva.estado = "cancelado"
        reserva.save()

        serializer = self.get_serializer(reserva)
        return Response(serializer.data)


class NotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar notificaciones"""

    queryset = Notificacion.objects.all().select_related("usuario")
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    @action(detail=False, methods=["get"])
    def no_leidas(self, request):
        """Obtiene notificaciones no leídas"""
        notificaciones = self.get_queryset().filter(leido=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def marcar_leida(self, request, pk=None):
        """Marcar notificación como leída"""
        notificacion = self.get_object()
        notificacion.leido = True
        notificacion.save()

        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def marcar_todas_leidas(self, request):
        """Marcar todas las notificaciones como leídas"""
        self.get_queryset().update(leido=True)
        return Response({"message": "Todas las notificaciones marcadas como leídas"})


@api_view(["POST"])
@permission_classes([AllowAny])
def registro_usuario(request):
    """Endpoint para registrar nuevos usuarios"""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Usuario registrado exitosamente",
                "user": {"id": user.id, "username": user.username, "email": user.email},
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    """Obtiene el perfil del usuario autenticado"""
    perfil = request.user.perfil
    serializer = PerfilUsuarioSerializer(perfil)
    return Response(serializer.data)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def actualizar_perfil(request):
    """Actualiza el perfil del usuario"""
    perfil = request.user.perfil
    serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estadisticas_usuario(request):
    """Obtiene estadísticas del usuario"""
    user = request.user

    prestamos_activos = Prestamo.objects.filter(
        usuario=user, estado__in=["activo", "renovado"]
    ).count()

    prestamos_totales = Prestamo.objects.filter(usuario=user).count()

    libros_leidos = Prestamo.objects.filter(usuario=user, estado="devuelto").count()

    reservas_activas = Reserva.objects.filter(
        usuario=user, estado__in=["pendiente", "notificado"]
    ).count()

    calificacion_promedio = (
        Resena.objects.filter(usuario=user).aggregate(Avg("calificacion"))[
            "calificacion__avg"
        ]
        or 0
    )

    libros_vencidos = Prestamo.objects.filter(
        usuario=user, estado="activo", fecha_devolucion_esperada__lt=timezone.now()
    ).count()

    data = {
        "prestamos_activos": prestamos_activos,
        "prestamos_totales": prestamos_totales,
        "libros_leidos": libros_leidos,
        "reservas_activas": reservas_activas,
        "calificacion_promedio_dada": round(calificacion_promedio, 2),
        "libros_vencidos": libros_vencidos,
    }

    serializer = EstadisticasUsuarioSerializer(data)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def inicio(request):
    """Endpoint para la pantalla de inicio con libros populares y nuevos"""
    libros_populares = Libro.objects.filter(es_popular=True)[:6]
    nuevas_adquisiciones = Libro.objects.filter(es_nuevo=True).order_by(
        "-fecha_agregado"
    )[:6]

    return Response(
        {
            "libros_populares": LibroListSerializer(libros_populares, many=True).data,
            "nuevas_adquisiciones": LibroListSerializer(
                nuevas_adquisiciones, many=True
            ).data,
        }
    )
