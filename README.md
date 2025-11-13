# Sistema de Gestión de Oficios

Aplicación web para la gestión de oficios, diseñada para facilitar el seguimiento y administración de documentos oficiales, con énfasis en oficios relacionados con protección de derechos de niños, niñas y adolescentes.

## Características Principales

- Gestión completa de oficios con seguimiento de estado
- Gestión de instituciones y juzgados
- Registro y seguimiento de niños, niñas y partes involucradas
- Sistema de búsqueda avanzada con filtros
- Interfaz intuitiva y responsiva
- Autenticación de usuarios

## Tecnologías Utilizadas

- **Backend:** Django 5.2
- **Frontend:** Bootstrap 5, jQuery, Select2
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Despliegue:** Configuración para producción lista

## Requisitos del Sistema

- Python 3.8+
- Django 5.2
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/orquera10/proyecto_oficios.git
   cd proyecto_oficios
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Aplicar migraciones:
   ```bash
   python manage.py migrate
   ```

5. Crear un superusuario:
   ```bash
   python manage.py createsuperuser
   ```

6. Iniciar el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```

7. Acceder a la aplicación en [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Estructura del Proyecto

```
proyecto_oficios/
├── config/               # Configuración principal del proyecto
├── oficios/             # Aplicación de gestión de oficios
├── personas/            # Gestión de personas (niños, partes)
├── static/              # Archivos estáticos (CSS, JS, imágenes)
├── templates/           # Plantillas HTML base
└── manage.py            # Script de gestión de Django
```

## Características Técnicas

- **Búsqueda Avanzada:** Filtros combinados para búsqueda rápida de oficios
- **Interfaz Responsive:** Diseño adaptativo para diferentes dispositivos
- **Seguridad:** Sistema de autenticación y control de acceso
- **Exportación:** Funcionalidad para exportar datos

## Contribución

Las contribuciones son bienvenidas. Por favor, lee nuestras pautas de contribución para más detalles.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto

Dario Orquera
Para más información, por favor contacta con el equipo de desarrollo.