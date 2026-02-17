# API de Biblioteca - Django REST Framework

## Instalación

```bash
# 1. Crear y activar entorno virtual en directorio de l proyecto con UV
uv init . 
source .venv/bin/activate  # Linux/Mac

# 2. Instalar dependencias
uv sync

# 3. Configurar base de datos
uv run python manage.py makemigrations
uv run python manage.py migrate

# 4. Crear superusuario
uv run python manage.py createsuperuser

# 6. Ejecutar servidor
uv run python manage.py runserver
```

# Endpoints
```bash
### Autenticación

- `POST /api/v1/auth/login/` - Iniciar sesión
- `POST /api/v1/auth/refresh/` - Refrescar token
- `POST /api/v1/auth/registro/` - Registrar nuevo usuario

### Libros

- `GET /api/v1/libros/` - Listar libros
- `GET /api/v1/libros/{id}/` - Detalle de libro
- `GET /api/v1/libros/populares/` - Libros populares
- `GET /api/v1/libros/nuevos/` - Nuevas adquisiciones
- `GET /api/v1/libros/buscar/?q=query` - Buscar libros
- `POST /api/v1/libros/{id}/prestar/` - Prestar libro
- `POST /api/v1/libros/{id}/reservar/` - Reservar libro

### Préstamos

- `GET /api/v1/prestamos/` - Listar préstamos
- `GET /api/v1/prestamos/activos/` - Préstamos activos
- `GET /api/v1/prestamos/historial/` - Historial de préstamos
- `POST /api/v1/prestamos/{id}/renovar/` - Renovar préstamo
- `POST /api/v1/prestamos/{id}/devolver/` - Devolver libro

### Reservas

- `GET /api/v1/reservas/` - Listar reservas
- `GET /api/v1/reservas/activas/` - Reservas activas
- `POST /api/v1/reservas/{id}/cancelar/` - Cancelar reserva

### Reseñas

- `GET /api/v1/resenas/?libro={id}` - Reseñas de un libro
- `POST /api/v1/resenas/` - Crear reseña
- `PUT /api/v1/resenas/{id}/` - Actualizar reseña
- `DELETE /api/v1/resenas/{id}/` - Eliminar reseña

### Notificaciones

- `GET /api/v1/notificaciones/` - Listar notificaciones
- `GET /api/v1/notificaciones/no_leidas/` - Notificaciones no leídas
- `POST /api/v1/notificaciones/{id}/marcar_leida/` - Marcar como leída
- `POST /api/v1/notificaciones/marcar_todas_leidas/` - Marcar todas como leídas

### Perfil

- `GET /api/v1/perfil/` - Ver perfil
- `PUT /api/v1/perfil/actualizar/` - Actualizar perfil
- `GET /api/v1/perfil/estadisticas/` - Estadísticas del usuario

### Otros

- `GET /api/v1/inicio/` - Datos para pantalla de inicio
- `GET /api/v1/autores/` - Listar autores
- `GET /api/v1/categorias/` - Listar categorías
- `GET /api/v1/editoriales/` - Listar editoriales
```
## 

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/login/` | Iniciar sesión | No |
| POST | `/api/v1/auth/registro/` | Registrar usuario | No |
| GET | `/api/v1/inicio/` | Datos inicio | No |
| GET | `/api/v1/libros/` | Listar libros | Opcional |
| GET | `/api/v1/libros/{id}/` | Detalle libro | Opcional |
| POST | `/api/v1/libros/{id}/prestar/` | Prestar libro | Sí |
| GET | `/api/v1/prestamos/activos/` | Mis préstamos | Sí |
| POST | `/api/v1/prestamos/{id}/renovar/` | Renovar préstamo | Sí |
| GET | `/api/v1/perfil/` | Ver perfil | Sí |
| GET | `/api/v1/notificaciones/no_leidas/` | Notificaciones | Sí |
