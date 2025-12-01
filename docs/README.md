# Documentacion del proyecto

Resumen completo de la aplicacion de gestion de oficios, casos y reportes.

## 1. Descripcion general

- Aplicacion Django 5.2 para gestionar oficios, casos y actores relacionados.
- Frontend basado en Bootstrap 5 con django-bootstrap5, crispy-forms y select2 (via widget_tweaks).
- Pensado para operadores internos con roles diferenciados por sector.

## 2. Arquitectura y apps

- `core`: configuracion base, autenticacion y helpers.
- `casos`: gestion de casos, estados y relacion con ninos/partes (estado ABIERTO/EN_PROCESO/CERRADO).
- `personas`: modelos de personas (ninos, partes), usados por casos y filtros.
- `oficios`: ciclo completo de oficios, movimientos, respuestas y catalogos (instituciones, juzgados, categorias, profesionales).
- `reportes`: vistas/reportes agregados.
- `config/settings.py`: configuracion global, carga de .env, static/media, middleware, apps instaladas.

## 3. Dependencias clave

- Django 5.2, psycopg2 (PostgreSQL), django-filter, crispy-bootstrap5, django-bootstrap5, widget-tweaks.
- WhiteNoise para servir estaticos en produccion.

## 4. Configuracion y variables de entorno (.env)

Revisa `.env.example` como base. Principales variables:
- `SECRET_KEY`: clave Django.
- `DEBUG`: True/False.
- `ALLOWED_HOSTS`: lista separada por comas.
- DB: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (por defecto PostgreSQL).
- Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- Seguridad: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`.

## 5. Ejecucion local

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Accede en http://127.0.0.1:8000/

## 6. Datos y modelos principales

- `Casos`: agrupan ninos/partes y se vinculan a oficios. Estado del caso cambia segun estados de sus oficios (todos enviados -> CERRADO).
- `Oficios`: numero, denuncia/legajo, caratula, institucion, juzgado, estado (`cargado`, `asignado`, `respondido`, `enviado`, `devuelto`), plazos y archivos PDF.
- `MovimientoOficio`: bitacora de cambios de estado con usuario, detalle y PDF opcional.
- `Respuesta`: respuestas a oficios con PDF opcional; puede marcar el oficio como respondido o devuelto.
- Catalogos: `Institucion`, `Juzgado`, `CategoriaJuzgado`, `Caratula`, `CaratulaOficio`, `Profesionales`.

## 7. Roles y permisos (logica de negocio)

- Sector Coordinacion OPD: no puede crear oficios.
- Sector Despacho Ninez: no puede responder ni cambiar estados (enviar/actualizar).
- Sector Informatica: unico autorizado a eliminar oficios.
- Usuarios se resuelven via `perfil.id_sector` y flags como `perfil.es_profesional`.

## 8. Flujos principales

- **Autenticacion**: LOGIN_URL `login`, redireccion a `casos:list`.
- **Casos**: crear/editar; asignar oficios desde el detalle de oficio (modal de casos recientes).
- **Oficios**:
  - Crear: estado inicial `cargado`. El formulario permite elegir varias instituciones; se clona un oficio por institucion. Si el caso estaba ABIERTO pasa a EN_PROCESO.
  - Listar/filtrar: filtros combinados (texto, estado, fechas, institucion, juzgado, nino) via `OficioFilter`. Orden por vencimiento y fecha de emision.
  - Movimientos: cambio de estado/enviar crea `MovimientoOficio` con detalle y PDF opcional; al marcar `enviado` se completa `fecha_envio`.
  - Responder: registra `Respuesta`; si se marca “devolver” el estado pasa a `devuelto`, de lo contrario `respondido`.
  - Asignar/desvincular caso: acciones desde el detalle.
  - Eliminar: requiere permiso de Informatica; borra el PDF fisico.
- **Reportes**: vistas agregadas (ver app `reportes` para detalle).

## 9. Archivos, estaticos y media

- Estaticos en `static/`, recogidos a `staticfiles/` en produccion (WhiteNoise).
- Media en `media/`.
- Rutas de carga:
  - Oficios: `oficios/oficio_<id>/<archivo.pdf>`
  - Respuestas: `respuestas/oficio_<id_oficio>/<archivo.pdf>`
  - Movimientos: `movimientos/oficio_<id_oficio>/<archivo.pdf>`
- Limite de carga: 10 MB, solo PDF (validado en formularios).

## 10. Pruebas y calidad

- Ejecutar pruebas: `python manage.py test`.
- No hay suite extensa en repo; agregar pruebas por app segun nuevos features.

## 11. Despliegue

- Dockerfile incluido. Usar `collectstatic` antes de servir.
- WhiteNoise configurado para servir estaticos.
- Configurar variables de entorno de seguridad (SECRET_KEY, DEBUG=False, cookies seguras).

## 12. Documentacion por modulo

- Oficios: `oficios/README.md` (flujo detallado, estados y permisos).

## 13. Manual de usuario (sugerido)

Mantener en `docs/usuario/manual.md` (crear). Secciones sugeridas:
- Roles y accesos (quien puede crear, responder, eliminar).
- Paso a paso: crear oficio (uno o varios), enviar/cambiar estado, responder/devolver, asignar/desvincular caso, usar filtros y reportes.
- Gestion de archivos (PDF, limites, reemplazos).
- Errores frecuentes y soluciones (permisos, tamanos, estados invalidos).
