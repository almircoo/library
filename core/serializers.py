from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

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


class AutorSerializer(serializers.ModelSerializer):
    numero_libros = serializers.SerializerMethodField()

    class Meta:
        model = Autor
        fields = [
            "id",
            "nombre",
            "biografia",
            "fecha_nacimiento",
            "nacionalidad",
            "foto",
            "numero_libros",
        ]

    def get_numero_libros(self, obj):
        return obj.libros.count()


class CategoriaSerializer(serializers.ModelSerializer):
    numero_libros = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion", "numero_libros"]

    def get_numero_libros(self, obj):
        return obj.libros.count()


class EditorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = ["id", "nombre", "pais", "sitio_web"]


class ResenaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    usuario_foto = serializers.ImageField(source="usuario.perfil.foto", read_only=True)

    class Meta:
        model = Resena
        fields = [
            "id",
            "libro",
            "usuario",
            "usuario_nombre",
            "usuario_foto",
            "calificacion",
            "comentario",
            "fecha_creacion",
            "fecha_actualizado",
        ]
        read_only_fields = ["usuario", "fecha_creacion", "fecha_actualizado"]

    def create(self, validated_data):
        validated_data["usuario"] = self.context["request"].user
        return super().create(validated_data)


class LibroListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""

    autor_nombre = serializers.CharField(source="autor.nombre", read_only=True)
    calificacion_promedio = serializers.FloatField(read_only=True)
    numero_resenas = serializers.IntegerField(read_only=True)
    categorias = CategoriaSerializer(many=True, read_only=True)
    disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Libro
        fields = [
            "id",
            "titulo",
            "autor_nombre",
            "anio_publicacion",
            "portada",
            "calificacion_promedio",
            "numero_resenas",
            "categorias",
            "disponible",
            "cantidad_disponible",
            "es_popular",
            "es_nuevo",
        ]


class LibroDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para vista individual"""

    autor = AutorSerializer(read_only=True)
    autor_id = serializers.PrimaryKeyRelatedField(
        queryset=Autor.objects.all(), source="autor", write_only=True
    )
    editorial = EditorialSerializer(read_only=True)
    editorial_id = serializers.PrimaryKeyRelatedField(
        queryset=Editorial.objects.all(),
        source="editorial",
        write_only=True,
        required=False,
    )
    categorias = CategoriaSerializer(many=True, read_only=True)
    categoria_ids = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        many=True,
        source="categorias",
        write_only=True,
    )
    calificacion_promedio = serializers.FloatField(read_only=True)
    numero_resenas = serializers.IntegerField(read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    resenas = ResenaSerializer(many=True, read_only=True)

    class Meta:
        model = Libro
        fields = [
            "id",
            "titulo",
            "autor",
            "autor_id",
            "isbn",
            "editorial",
            "editorial_id",
            "anio_publicacion",
            "numero_paginas",
            "idioma",
            "descripcion",
            "portada",
            "categorias",
            "categoria_ids",
            "tipo",
            "cantidad_total",
            "cantidad_disponible",
            "disponible",
            "calificacion_promedio",
            "numero_resenas",
            "resenas",
            "fecha_agregado",
            "es_popular",
            "es_nuevo",
        ]
        read_only_fields = ["fecha_agregado", "calificacion_promedio", "numero_resenas"]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    prestamos_activos = serializers.IntegerField(read_only=True)
    puede_prestar = serializers.BooleanField(read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefono",
            "direccion",
            "fecha_nacimiento",
            "foto",
            "numero_tarjeta",
            "activo",
            "max_prestamos",
            "dias_prestamo_default",
            "prestamos_activos",
            "puede_prestar",
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    telefono = serializers.CharField(required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "telefono",
            "direccion",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        telefono = validated_data.pop("telefono", None)
        direccion = validated_data.pop("direccion", None)

        user = User.objects.create_user(**validated_data)

        # Crear perfil de usuario
        PerfilUsuario.objects.create(user=user, telefono=telefono, direccion=direccion)

        return user


class PrestamoSerializer(serializers.ModelSerializer):
    libro_info = LibroListSerializer(source="libro", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    dias_restantes = serializers.IntegerField(read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    puede_renovar = serializers.SerializerMethodField()

    class Meta:
        model = Prestamo
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "libro",
            "libro_info",
            "fecha_prestamo",
            "fecha_devolucion_esperada",
            "fecha_devolucion_real",
            "estado",
            "renovaciones",
            "max_renovaciones",
            "notas",
            "dias_restantes",
            "esta_vencido",
            "puede_renovar",
        ]
        read_only_fields = [
            "usuario",
            "fecha_prestamo",
            "fecha_devolucion_real",
            "estado",
            "renovaciones",
        ]

    def get_puede_renovar(self, obj):
        return obj.puede_renovar()

    def validate_libro(self, value):
        """Valida que el libro esté disponible"""
        if not value.disponible:
            raise serializers.ValidationError("El libro no está disponible")
        return value

    def create(self, validated_data):
        usuario = self.context["request"].user
        libro = validated_data["libro"]

        # Verificar que el usuario pueda realizar préstamos
        if not usuario.perfil.puede_prestar:
            raise serializers.ValidationError(
                "Has alcanzado el límite de préstamos activos o tu cuenta está inactiva"
            )

        # Verificar que el libro esté disponible
        if not libro.disponible:
            raise serializers.ValidationError("El libro no está disponible")

        # Calcular fecha de devolución
        dias_prestamo = usuario.perfil.dias_prestamo_default
        fecha_devolucion = timezone.now() + timedelta(days=dias_prestamo)

        # Crear préstamo
        prestamo = Prestamo.objects.create(
            usuario=usuario,
            libro=libro,
            fecha_devolucion_esperada=fecha_devolucion,
            **validated_data,
        )

        # Actualizar disponibilidad del libro
        libro.cantidad_disponible -= 1
        libro.save()

        # Crear notificación
        Notificacion.objects.create(
            usuario=usuario,
            tipo="prestamo",
            titulo="Préstamo realizado",
            mensaje=f'Has prestado el libro "{libro.titulo}". Fecha de devolución: {fecha_devolucion.strftime("%d/%m/%Y")}',
        )

        return prestamo


class ReservaSerializer(serializers.ModelSerializer):
    libro_info = LibroListSerializer(source="libro", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "libro",
            "libro_info",
            "fecha_reserva",
            "estado",
            "fecha_notificacion",
            "fecha_expiracion",
        ]
        read_only_fields = [
            "usuario",
            "fecha_reserva",
            "estado",
            "fecha_notificacion",
            "fecha_expiracion",
        ]

    def create(self, validated_data):
        usuario = self.context["request"].user
        libro = validated_data["libro"]

        # Verificar que el libro no esté disponible
        if libro.disponible:
            raise serializers.ValidationError(
                "El libro está disponible, puedes realizar un préstamo directamente"
            )

        # Verificar que no tenga una reserva activa del mismo libro
        reserva_existente = Reserva.objects.filter(
            usuario=usuario, libro=libro, estado="pendiente"
        ).exists()

        if reserva_existente:
            raise serializers.ValidationError(
                "Ya tienes una reserva activa para este libro"
            )

        reserva = Reserva.objects.create(usuario=usuario, libro=libro)

        # Crear notificación
        Notificacion.objects.create(
            usuario=usuario,
            tipo="reserva",
            titulo="Reserva creada",
            mensaje=f'Has reservado el libro "{libro.titulo}". Te notificaremos cuando esté disponible.',
        )

        return reserva


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            "id",
            "usuario",
            "tipo",
            "titulo",
            "mensaje",
            "leido",
            "fecha_creacion",
        ]
        read_only_fields = ["usuario", "fecha_creacion"]


class EstadisticasUsuarioSerializer(serializers.Serializer):
    """Serializer para estadísticas del usuario"""

    prestamos_activos = serializers.IntegerField()
    prestamos_totales = serializers.IntegerField()
    libros_leidos = serializers.IntegerField()
    reservas_activas = serializers.IntegerField()
    calificacion_promedio_dada = serializers.FloatField()
    libros_vencidos = serializers.IntegerField()


class BusquedaLibroSerializer(serializers.Serializer):
    """Serializer para búsqueda de libros"""

    query = serializers.CharField(required=False, allow_blank=True)
    categoria = serializers.IntegerField(required=False)
    autor = serializers.IntegerField(required=False)
    disponible = serializers.BooleanField(required=False)
    es_popular = serializers.BooleanField(required=False)
    es_nuevo = serializers.BooleanField(required=False)
    anio_desde = serializers.IntegerField(required=False)
    anio_hasta = serializers.IntegerField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            "titulo",
            "-titulo",
            "autor__nombre",
            "-autor__nombre",
            "anio_publicacion",
            "-anio_publicacion",
            "-fecha_agregado",
            "fecha_agregado",
            "-calificacion_promedio",
            "calificacion_promedio",
        ],
        required=False,
    )
