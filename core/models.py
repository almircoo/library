from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Autor(models.Model):
    nombre = models.CharField(max_length=200)
    biografia = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    nacionalidad = models.CharField(max_length=100, blank=True, null=True)
    foto = models.ImageField(upload_to="autores/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Autores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    """Modelo para categorías de libros"""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Editorial(models.Model):
    """Modelo para editoriales"""

    nombre = models.CharField(max_length=200)
    pais = models.CharField(max_length=100, blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Editoriales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    """Modelo principal para libros"""

    TIPO_CHOICES = [
        ("novela", "Novela"),
        ("cuento", "Cuento"),
        ("ensayo", "Ensayo"),
        ("poesia", "Poesía"),
        ("biografia", "Biografía"),
        ("historia", "Historia"),
        ("ciencia", "Ciencia"),
        ("otro", "Otro"),
    ]

    titulo = models.CharField(max_length=300)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="libros")
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    editorial = models.ForeignKey(
        Editorial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="libros",
    )
    anio_publicacion = models.IntegerField()
    numero_paginas = models.IntegerField(blank=True, null=True)
    idioma = models.CharField(max_length=50, default="Español")
    descripcion = models.TextField()
    portada = models.ImageField(upload_to="libros/", blank=True, null=True)
    categorias = models.ManyToManyField(Categoria, related_name="libros")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="novela")

    # Campos para gestión de inventario
    cantidad_total = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    cantidad_disponible = models.IntegerField(
        default=1, validators=[MinValueValidator(0)]
    )

    # Campos de control
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)
    es_popular = models.BooleanField(default=False)
    es_nuevo = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha_agregado"]
        indexes = [
            models.Index(fields=["titulo"]),
            models.Index(fields=["autor"]),
            models.Index(fields=["-fecha_agregado"]),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.autor.nombre}"

    @property
    def disponible(self):
        return self.cantidad_disponible > 0

    @property
    def calificacion_promedio(self):
        """Calcula el promedio de calificaciones"""
        resenas = self.resenas.all()
        if resenas.exists():
            return resenas.aggregate(models.Avg("calificacion"))["calificacion__avg"]
        return 0

    @property
    def numero_resenas(self):
        return self.resenas.count()


class PerfilUsuario(models.Model):
    """Extensión del modelo User para información adicional"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    foto = models.ImageField(upload_to="usuarios/", blank=True, null=True)
    numero_tarjeta = models.CharField(max_length=20, unique=True, blank=True, null=True)
    activo = models.BooleanField(default=True)

    # Límites de préstamo
    max_prestamos = models.IntegerField(default=3)
    dias_prestamo_default = models.IntegerField(default=14)

    class Meta:
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def prestamos_activos(self):
        """Retorna el número de préstamos activos"""
        return self.user.prestamos.filter(estado="activo").count()

    @property
    def puede_prestar(self):
        """Verifica si el usuario puede realizar más préstamos"""
        return self.prestamos_activos < self.max_prestamos and self.activo


class Prestamo(models.Model):
    """Modelo para gestionar préstamos de libros"""

    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("devuelto", "Devuelto"),
        ("vencido", "Vencido"),
        ("renovado", "Renovado"),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="prestamos"
    )
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="prestamos")
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_devolucion_esperada = models.DateTimeField()
    fecha_devolucion_real = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="activo")
    renovaciones = models.IntegerField(default=0)
    max_renovaciones = models.IntegerField(default=2)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha_prestamo"]
        indexes = [
            models.Index(fields=["usuario", "estado"]),
            models.Index(fields=["libro", "estado"]),
            models.Index(fields=["-fecha_prestamo"]),
        ]

    def __str__(self):
        return f"{self.libro.titulo} - {self.usuario.username}"

    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta la devolución"""
        if self.estado == "devuelto":
            return 0
        delta = self.fecha_devolucion_esperada - timezone.now()
        return delta.days

    @property
    def esta_vencido(self):
        """Verifica si el préstamo está vencido"""
        return self.dias_restantes < 0 and self.estado == "activo"

    def puede_renovar(self):
        """Verifica si el préstamo puede ser renovado"""
        return (
            self.estado == "activo"
            and self.renovaciones < self.max_renovaciones
            and not self.esta_vencido
        )

    def renovar(self, dias=14):
        """Renueva el préstamo extendiendo la fecha de devolución"""
        if self.puede_renovar():
            self.fecha_devolucion_esperada = timezone.now() + timezone.timedelta(
                days=dias
            )
            self.renovaciones += 1
            self.estado = "renovado"
            self.save()
            return True
        return False

    def devolver(self):
        """Marca el libro como devuelto"""
        if self.estado in ["activo", "vencido", "renovado"]:
            self.fecha_devolucion_real = timezone.now()
            self.estado = "devuelto"
            self.libro.cantidad_disponible += 1
            self.libro.save()
            self.save()
            return True
        return False


class Resena(models.Model):
    """Modelo para reseñas de libros"""

    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resenas")
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Reseñas"
        unique_together = ["libro", "usuario"]
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo} ({self.calificacion}★)"


class Reserva(models.Model):
    """Modelo para reservas de libros no disponibles"""

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("notificado", "Notificado"),
        ("completado", "Completado"),
        ("cancelado", "Cancelado"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservas")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name="reservas")
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente"
    )
    fecha_notificacion = models.DateTimeField(blank=True, null=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["fecha_reserva"]
        indexes = [
            models.Index(fields=["libro", "estado"]),
            models.Index(fields=["usuario", "estado"]),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.libro.titulo}"


class Notificacion(models.Model):
    """Modelo para notificaciones a usuarios"""

    TIPO_CHOICES = [
        ("prestamo", "Préstamo"),
        ("devolucion", "Devolución"),
        ("vencimiento", "Vencimiento"),
        ("reserva", "Reserva disponible"),
        ("sistema", "Sistema"),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
