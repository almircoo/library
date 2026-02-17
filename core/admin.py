from django.contrib import admin
from django.utils.html import format_html

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


# =========================
# AUTOR
# =========================
@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nacionalidad", "fecha_nacimiento")
    search_fields = ("nombre", "nacionalidad")
    list_filter = ("nacionalidad",)
    ordering = ("nombre",)


# =========================
# CATEGORIA
# =========================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    ordering = ("nombre",)


# =========================
# EDITORIAL
# =========================
@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pais", "sitio_web")
    search_fields = ("nombre", "pais")
    list_filter = ("pais",)
    ordering = ("nombre",)


# =========================
# RESEÑA INLINE
# =========================
class ResenaInline(admin.TabularInline):
    model = Resena
    extra = 0
    readonly_fields = ("fecha_creacion", "fecha_actualizado")


# =========================
# LIBRO
# =========================
@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "editorial",
        "anio_publicacion",
        "tipo",
        "cantidad_disponible",
        "es_popular",
        "es_nuevo",
        "disponible",
    )
    list_filter = (
        "tipo",
        "es_popular",
        "es_nuevo",
        "idioma",
        "editorial",
        "categorias",
    )
    search_fields = ("titulo", "autor__nombre", "isbn")
    filter_horizontal = ("categorias",)
    readonly_fields = ("fecha_agregado", "fecha_actualizado")
    inlines = [ResenaInline]

    fieldsets = (
        (
            "Información básica",
            {
                "fields": (
                    "titulo",
                    "autor",
                    "isbn",
                    "editorial",
                    "anio_publicacion",
                    "numero_paginas",
                    "idioma",
                    "tipo",
                    "descripcion",
                    "portada",
                    "categorias",
                )
            },
        ),
        (
            "Inventario",
            {
                "fields": (
                    "cantidad_total",
                    "cantidad_disponible",
                )
            },
        ),
        (
            "Estado",
            {
                "fields": (
                    "es_popular",
                    "es_nuevo",
                )
            },
        ),
        (
            "Control",
            {
                "fields": (
                    "fecha_agregado",
                    "fecha_actualizado",
                )
            },
        ),
    )

    @admin.display(boolean=True)
    def disponible(self, obj):
        return obj.disponible


# =========================
# PERFIL USUARIO
# =========================
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "telefono",
        "activo",
        "max_prestamos",
        "prestamos_activos",
    )
    search_fields = ("user__username", "telefono", "numero_tarjeta")
    list_filter = ("activo",)
    readonly_fields = ("prestamos_activos",)


# =========================
# PRESTAMO
# =========================
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "libro",
        "usuario",
        "fecha_prestamo",
        "fecha_devolucion_esperada",
        "estado",
        "renovaciones",
        "esta_vencido",
    )
    list_filter = ("estado", "fecha_prestamo", "fecha_devolucion_esperada")
    search_fields = ("usuario__username", "libro__titulo")
    readonly_fields = ("fecha_prestamo", "esta_vencido", "dias_restantes")

    actions = ["marcar_como_devuelto"]

    @admin.action(description="Marcar préstamos seleccionados como devueltos")
    def marcar_como_devuelto(self, request, queryset):
        for prestamo in queryset:
            prestamo.devolver()

    @admin.display(boolean=True)
    def esta_vencido(self, obj):
        return obj.esta_vencido


# =========================
# RESEÑA
# =========================
@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = (
        "libro",
        "usuario",
        "calificacion",
        "fecha_creacion",
    )
    list_filter = ("calificacion", "fecha_creacion")
    search_fields = ("libro__titulo", "usuario__username")
    readonly_fields = ("fecha_creacion", "fecha_actualizado")


# =========================
# RESERVA
# =========================
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "libro",
        "usuario",
        "fecha_reserva",
        "estado",
        "fecha_notificacion",
    )
    list_filter = ("estado", "fecha_reserva")
    search_fields = ("libro__titulo", "usuario__username")
    readonly_fields = ("fecha_reserva",)


# =========================
# NOTIFICACION
# =========================
@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "usuario",
        "tipo",
        "leido",
        "fecha_creacion",
    )
    list_filter = ("tipo", "leido", "fecha_creacion")
    search_fields = ("titulo", "usuario__username")
    readonly_fields = ("fecha_creacion",)
