# Manual de usuario - Sistema de gestion de oficios

## 1. Objetivo

Este manual describe las funciones principales del sistema para registrar oficios, administrar casos y personas vinculadas, y consultar reportes de gestion.

## 2. Acceso e inicio de sesion

- Ingrese con su usuario y clave en la pantalla de login.
- Si el acceso es correcto, el sistema lo redirige a la pantalla principal.
- Para cerrar sesion, use la opcion "Cerrar sesion" del menu de usuario.

## 3. Roles y permisos

Los permisos se aplican segun el sector del usuario y su perfil:

- Coordinacion OPD: no puede crear casos ni oficios.
- Despacho Ninez: no puede responder oficios ni cambiar estados (enviar/actualizar).
- Informatica: unico sector habilitado para eliminar oficios.
- Profesionales: usuarios marcados como profesionales se gestionan desde el modulo de catalogos.

Si una accion no esta permitida, el sistema muestra un mensaje de error y evita el cambio.

## 4. Casos

Los casos agrupan informacion de ninos y partes, y pueden tener oficios asociados.

Funciones disponibles:

- Listar casos: muestra filtros por texto y estado (ABIERTO, EN_PROCESO, CERRADO).
- Crear caso: complete los datos del caso y agregue ninos y partes desde el formulario.
- Editar caso: actualice datos generales, ninos y partes relacionados.
- Ver detalle: muestra informacion completa y relaciones.
- Eliminar caso: solo si no tiene oficios asociados.

Notas:

- El estado del caso se ajusta automaticamente segun el estado de sus oficios.
- Los casos se ordenan por fecha de creacion.

## 5. Personas

El modulo Personas permite administrar Ninos y Partes.

Funciones:

- Listar y filtrar ninos y partes.
- Crear, editar y eliminar registros.
- Ver detalle con los casos asociados.

Estos registros se utilizan como referencia en Casos y filtros de busqueda.

## 6. Oficios

El modulo Oficios centraliza el ciclo de vida del oficio.

Funciones principales:

- Crear oficio: se registra en estado "cargado". Puede seleccionar varias instituciones; se genera un oficio por cada institucion.
- Listar y filtrar: por texto, estado, fechas, institucion, juzgado y nino asociado.
- Ver detalle: muestra datos generales, movimientos, respuestas y vinculaciones.
- Cambiar estado / Enviar: genera un movimiento con detalle y PDF opcional.
- Responder oficio: registra respuesta y define si queda "respondido" o "devuelto".
- Asignar caso: vincula un oficio a un caso existente.
- Desvincular caso: remueve la relacion con el caso.
- Eliminar oficio: solo sector Informatica, elimina el registro y el PDF asociado.

Estados habituales del oficio:

- cargado, asignado, respondido, enviado, devuelto.

## 7. Catalogos (Oficios)

Desde el modulo de Oficios se administran catalogos:

- Instituciones
- Juzgados
- Categorias de juzgados
- Profesionales

En cada uno puede listar, crear, editar y eliminar registros.

## 8. Reportes

El panel de reportes muestra indicadores y resumenes:

- Totales por estado de oficio.
- Oficios vencidos y proximos a vencer.
- Totales por institucion y juzgado.
- Movimientos y respuestas recientes.

Puede filtrar por rango de fechas para acotar la informacion.

## 9. Archivos PDF

- Se aceptan solo archivos PDF.
- Tamano maximo: 10 MB.
- Los archivos pueden adjuntarse en oficios, movimientos y respuestas.

## 10. Errores frecuentes y soluciones

- Permisos insuficientes: verifique su sector o contacte al administrador.
- No se puede eliminar un caso: el caso tiene oficios asociados.
- No se puede responder o enviar un oficio: el sector Despacho Ninez no tiene permiso.
- Error por tamanos o tipo de archivo: confirme que el PDF sea menor a 10 MB.

## 11. Buenas practicas

- Mantenga actualizados los datos de casos y personas antes de crear oficios.
- Registre movimientos con detalle claro para trazabilidad.
- Use los filtros para priorizar oficios proximos a vencer.
