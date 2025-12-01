# Modulo de Oficios

Resumen operativo y tecnico del flujo de oficios dentro de la aplicacion.

## Objetivo

- Registrar oficios entrantes y sus estados.
- Relacionar cada oficio con un caso, instituciones y agentes (juzgados).
- Seguir el historial mediante movimientos y respuestas con adjuntos PDF.

## Modelos clave

- `Oficio` (`oficios/models.py`): entidad principal, con numero, denuncia/legajo, estado, plazos y archivo PDF opcional. Puede vincularse a un `Caso` y a una `Institucion` o `Juzgado`.
- `MovimientoOficio`: bitacora de cambios de estado (cargado, asignado, respondido, enviado, devuelto), guarda quien lo realizo, detalle y PDF opcional.
- `Respuesta`: registro de respuesta a un oficio, permite adjuntar PDF y elegir si el oficio queda `respondido` o vuelve a `devuelto`.
- `Institucion`, `Juzgado`, `CategoriaJuzgado`, `Caratula`, `CaratulaOficio`: tablas auxiliares para clasificar oficios y agentes.

## Flujo operativo

1. **Alta de oficio** (`OficioCreateView`): se crea en estado `cargado`. El formulario permite seleccionar varias instituciones; se clona un oficio por cada institucion elegida. Se registra un movimiento inicial y, si el caso estaba `ABIERTO`, pasa a `EN_PROCESO`.
2. **Listado y filtros** (`OficioListView`, `OficioEstadoListView`): filtros combinados por texto, estado, fechas, institucion, juzgado y nino/a asociado al caso (`OficioFilter`). Ordena por fecha de vencimiento y muestra contadores basicos.
3. **Cambio de estado / movimientos** (`OficioEnviarView`): crea un `MovimientoOficio` con detalle y PDF opcional, actualiza el estado y la institucion seleccionada. Al marcar `enviado`, completa `fecha_envio`.
4. **Respuestas** (`RespuestaCreateView`): guarda la respuesta y, segun el checkbox `devolver`, deja el oficio en `respondido` o `devuelto`. Genera movimiento con el texto ingresado (primeros 200 caracteres).
5. **Asignar o desvincular caso** (`OficioAsignarCasoView`, `OficioDesvincularCasoView`): permite ligar/desligar un oficio a un caso existente desde el detalle.
6. **Eliminacion** (`OficioDeleteView`): restringida a usuarios del sector Informatica, elimina el registro y el PDF asociado.

## Reglas y permisos

- Usuarios del sector **Coordinacion OPD** no pueden crear oficios.
- Usuarios del sector **Despacho Ninez** no pueden responder ni cambiar estados (bloqueo en update, enviar y responder).
- El tamano maximo de PDF es 10 MB (validado en formularios); solo se aceptan `.pdf`.
- Archivos se almacenan en:
  - Oficios: `MEDIA_ROOT/oficios/oficio_<id>/<archivo>`
  - Respuestas: `MEDIA_ROOT/respuestas/oficio_<id_oficio>/<archivo>`
  - Movimientos: `MEDIA_ROOT/movimientos/oficio_<id_oficio>/<archivo>`

## URLs principales (namespace `oficios`)

- `""` → listado general.
- `"nuevo/"` → alta de oficio.
- `"<pk>/"` → detalle con movimientos y respuestas.
- `"<pk>/editar/"`, `"<pk>/eliminar/"`, `"<pk>/responder/"`, `"<pk>/enviar/"`.
- `"<pk>/asignar-caso/"`, `"<pk>/desvincular-caso/"`.
- Catalogos: `juzgados/`, `instituciones/`, `categorias/`, `profesionales/` con sus rutas `nuevo`, `editar`, `eliminar`.

## Notas para desarrollo

- Cada `save` de `Oficio` recalcula `fecha_vencimiento` si cambia `plazo_horas` y ajusta el estado del `Caso`: si todos los oficios del caso estan `enviado`, el caso pasa a `CERRADO`; si se modifica desde un cerrado, vuelve a `EN_PROCESO`.
- Los movimientos no bloquean el flujo ante errores (try/except deliberado para no impedir el guardado).
- `OficioForm` espera el campo `caso` como hidden; puede recibirse por querystring `?caso=<id>` para precargarlo.
