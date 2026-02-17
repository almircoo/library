from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Notificacion, PerfilUsuario, Prestamo, Reserva


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil de usuario automáticamente al crear un usuario"""
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guardar perfil cuando se guarde el usuario"""
    if hasattr(instance, "perfil"):
        instance.perfil.save()


@receiver(pre_save, sender=Prestamo)
def actualizar_estado_prestamo(sender, instance, **kwargs):
    """Actualizar estado de préstamo si está vencido"""
    if instance.pk:  # Solo para préstamos existentes
        if instance.estado == "activo" and instance.esta_vencido:
            instance.estado = "vencido"

            # Crear notificación de vencimiento
            Notificacion.objects.get_or_create(
                usuario=instance.usuario,
                tipo="vencimiento",
                titulo="Préstamo vencido",
                mensaje=f'El préstamo del libro "{instance.libro.titulo}" está vencido. Por favor devuélvelo lo antes posible.',
                defaults={"leido": False},
            )


@receiver(post_save, sender=Prestamo)
def notificar_proximo_vencimiento(sender, instance, created, **kwargs):
    """Notificar cuando faltan 2 días para el vencimiento"""
    if not created and instance.estado in ["activo", "renovado"]:
        if instance.dias_restantes == 2:
            Notificacion.objects.get_or_create(
                usuario=instance.usuario,
                tipo="vencimiento",
                titulo="Préstamo próximo a vencer",
                mensaje=f'El préstamo del libro "{instance.libro.titulo}" vence en 2 días. Fecha límite: {instance.fecha_devolucion_esperada.strftime("%d/%m/%Y")}',
                defaults={"leido": False},
            )
