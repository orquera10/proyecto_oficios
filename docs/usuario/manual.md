# Manual de usuario - Sistema de gestion de oficios

## 1. Objetivo

Este manual describe en detalle las funciones del sistema para registrar oficios, administrar casos y personas vinculadas, y consultar reportes de gestion. Esta pensado para usuarios operativos y administradores.

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

## 4. Navegacion general

El menu principal incluye:

- Casos: listado, alta y detalle.
- Oficios: listado general y por estado.
- Personas: ninos y partes.
- Referencias: catalogos (instituciones, juzgados, categorias, profesionales).
- Reportes: solo visible para Informatica.
- Usuario: perfil y manual.

## 5. Casos

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

Paso a paso: crear un caso

1. Ingrese a Casos -> Nuevo Caso.
2. Complete los datos generales del caso.
3. Agregue uno o mas ninos y partes desde los bloques correspondientes.
4. Guarde el caso. El sistema lo redirige al detalle.

Paso a paso: editar un caso

1. Ingrese al detalle del caso.
2. Seleccione Editar.
3. Actualice datos generales y relaciones.
4. Guarde los cambios.

## 6. Personas

El modulo Personas permite administrar Ninos y Partes.

Funciones:

- Listar y filtrar ninos y partes.
- Crear, editar y eliminar registros.
- Ver detalle con los casos asociados.

Estos registros se utilizan como referencia en Casos y filtros de busqueda.

Paso a paso: crear un nino o parte

1. Ingrese a Personas -> Ninos o Personas -> Partes.
2. Seleccione Nuevo.
3. Complete el formulario y guarde.

## 7. Oficios

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

Paso a paso: crear un oficio

1. Ingrese a Oficios -> Nuevo Oficio.
2. Complete los datos principales (nro, denuncia, legajo, caratula).
3. Seleccione institucion o instituciones.
4. Adjunte el PDF si corresponde.
5. Guarde. Si se eligieron varias instituciones, se crea un oficio por cada una.

Paso a paso: asignar un oficio

1. Abra el detalle del oficio.
2. Seleccione Asignar.
3. Elija la institucion y confirme. El detalle se completa por defecto.
4. Guarde. El oficio pasa a estado asignado.

Paso a paso: responder un oficio

1. Abra el detalle del oficio asignado.
2. Seleccione Responder.
3. Complete el texto de respuesta (se precarga por defecto).
4. Opcional: marque Devolver si corresponde.
5. Guarde. El oficio pasa a respondido o devuelto.

Paso a paso: enviar un oficio

1. Abra el detalle del oficio respondido.
2. Seleccione Enviar.
3. Complete el detalle (se precarga por defecto) y adjunte PDF si corresponde.
4. Confirme. El oficio pasa a enviado y se registra fecha de envio.

Paso a paso: vincular/desvincular caso

1. Desde el detalle del oficio, use Vincular a caso existente.
2. Seleccione el caso y confirme.
3. Para desvincular, use la accion Desvincular en el panel del caso.

## 8. Catalogos (Oficios)

Desde el modulo de Oficios se administran catalogos:

- Instituciones
- Juzgados
- Categorias de juzgados
- Profesionales

En cada uno puede listar, crear, editar y eliminar registros.

Recomendaciones:

- Mantenga catalogos actualizados para facilitar el filtrado.
- Revise instituciones y juzgados antes de crear oficios.

## 9. Reportes

El panel de reportes muestra indicadores y resumenes:

- Totales por estado de oficio.
- Oficios vencidos y proximos a vencer.
- Totales por institucion y juzgado.
- Movimientos y respuestas recientes.

Puede filtrar por rango de fechas para acotar la informacion.

## 10. Archivos PDF

- Se aceptan solo archivos PDF.
- Tamano maximo: 10 MB.
- Los archivos pueden adjuntarse en oficios, movimientos y respuestas.

## 11. Errores frecuentes y soluciones

- Permisos insuficientes: verifique su sector o contacte al administrador.
- No se puede eliminar un caso: el caso tiene oficios asociados.
- No se puede responder o enviar un oficio: el sector Despacho Ninez no tiene permiso.
- Error por tamanos o tipo de archivo: confirme que el PDF sea menor a 10 MB.

## 12. Buenas practicas

- Mantenga actualizados los datos de casos y personas antes de crear oficios.
- Registre movimientos con detalle claro para trazabilidad.
- Use los filtros para priorizar oficios proximos a vencer.
 - Revise el estado del oficio antes de avanzar al siguiente paso.
