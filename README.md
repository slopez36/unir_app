# UNIR App 🎓

Aplicación web para gestión académica de estudiantes de la UNIR. Permite gestionar asignaturas, notas, recursos (Drive) y eventos (Calendar), con una interfaz moderna y profesional.

## Características ✨

*   **Gestión de Asignaturas**: Crea y organiza tus asignaturas.
*   **Integración con Google Drive**: Sube apuntes, ejercicios y exámenes directamente a tu Drive.
*   **Integración con Google Calendar**: Sincroniza eventos y fechas de entrega.
*   **Dashboard Interactivo**: Vista general de tu actividad académica.
*   **Diseño Premium**: Interfaz limpia y responsive construida con Tailwind CSS y Google Fonts (Inter).
*   **Arquitectura Robusta**: Backend en Python (Flask) y base de datos SQLite.

## Requisitos 📋

*   Python 3.9+
*   Cuenta de Google (para integración con Drive/Calendar)
*   Docker (opcional, para despliegue)

## Instalación Local 🛠️

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/slopez36/unir_app.git
    cd unir_app
    ```

2.  **Crear entorno virtual**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\Activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración**:
    *   Necesitas los archivos `credentials.json` y `token.json` de Google Cloud en la raíz del proyecto para que funcione la integración con Google.
    
5.  **Ejecutar**:
    ```bash
    python run.py
    ```
    Visita `http://localhost:5000`.

## Despliegue con Docker 🐳

La aplicación está lista para desplegarse con Docker Compose.

1.  Asegúrate de tener la red externa creada (o ajusta el `docker-compose.yml`):
    ```bash
    docker network create nginx-network
    ```

2.  Levanta el servicio:
    ```bash
    docker-compose up -d
    ```

## Estructura del Proyecto ue

*   `app/`: Código fuente de la aplicación Flask.
    *   `routes/`: Controladores de las diferentes secciones.
    *   `services/`: Lógica de integración con Google.
    *   `templates/`: Plantillas HTML/Jinja2 con Tailwind.
    *   `models.py`: Modelos de base de datos SQLAlchemy.
*   `instance/`: Base de datos SQLite (persistente).
*   `run.py`: Punto de entrada.

## Autor ✒️

Desarrollado por [slopez36](https://github.com/slopez36).
