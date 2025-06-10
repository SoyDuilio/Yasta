# rucfacil
DeclaracionesMensuales
# RUCFACIL - Servicios de Declaraciones Juradas de Impuestos en Perú (MVP)

Este proyecto tiene como objetivo desarrollar una plataforma de servicios para simplificar la presentación de declaraciones juradas mensuales de impuestos (IGV-Renta) para microempresarios en Perú, específicamente aquellos obligados solo a llevar registros de ventas y compras electrónicos.

Debido a la facturación electrónica normada por SUNAT, la Administración Tributaria ya conoce todas las operaciones de estos contribuyentes. RUCFACIL busca ofrecer un servicio confiable y eficiente para realizar estas declaraciones, evitando los riesgos asociados a contadores poco responsables y simplificando el proceso para el empresario.

## Características Principales (MVP)

*   **Gestión de Clientes:** Registro y administración de microempresarios.
*   **Almacenamiento Seguro de Credenciales SOL:** Gestión segura de usuario y clave SOL del cliente para realizar los trámites.
*   **Procesamiento de Declaraciones Mensuales (IGV-Renta):** Un equipo interno utilizará la plataforma para gestionar y registrar la presentación manual de las declaraciones en el portal SUNAT SOL.
*   **Notificaciones y Comunicación:** Información al cliente sobre el estado de su declaración, impuestos a pagar y confirmaciones.
*   **Gestión de Pagos del Servicio:** Cobro de una tarifa por el servicio (ej. S/. 10), potencialmente a través de Yape/Plin.
*   **Dashboard para Clientes:** Acceso a constancias de declaración/pago y un consolidado de operaciones mensuales con estadísticas básicas.
*   **Panel de Administración Interno:** Para que el personal de RUCFACIL gestione los servicios, clientes y tareas.

## Servicios Adicionales Planeados (Post-MVP)

*   Presentación de solicitudes de devolución de percepciones/retenciones.
*   Presentación de solicitudes de fraccionamiento de deuda.
*   Emisión de Recibos por Honorarios Electrónicos (RxH).

## Stack Tecnológico

*   **Backend:** Python, FastAPI
*   **Base de Datos/ORM:** PostgreSQL (preferido) o MySQL, SQLAlchemy, Alembic (para migraciones)
*   **Frontend Dinámico (Cliente y Admin):** HTMX, JavaScript (con Hyperscript)
*   **Estilos:** CSS, SASS
*   **Autenticación:** JWT (JSON Web Tokens)
*   **Despliegue Local (Dev):** Uvicorn
*   **Procesamiento de Imágenes (Yape/Plin):** OCR + LLM (planificado)
*   **Notificaciones:** Email (inicial), SMS/WhatsApp (futuro)

## Estructura del Proyecto
peru_tax_services_project/ # Nombre raíz (ej: RUCFACIL)
├── alembic/ # Migraciones de base de datos
├── app/ # Código fuente de la aplicación FastAPI
│ ├── apis/ # Endpoints y routers de la API
│ ├── chatbot/ # Lógica del chatbot (futuro)
│ ├── core/ # Configuración central, seguridad
│ ├── crud/ # Operaciones CRUD de base deatos
│ ├── db/ # Configuración de DB, clase base, scripts de inicialización
│ ├── models/ # Modelos SQLAlchemy (tablas)
│ ├── schemas/ # Esquemas Pydantic (validación y serialización)
│ ├── services_logic/ # Lógica de negocio específica
│ ├── static/ # Archivos estáticos (CSS, JS, imágenes)
│ ├── templates/ # Plantillas HTML (para HTMX)
│ ├── init.py
│ └── main.py # Punto de entrada de la aplicación FastAPI
├── tests/ # Pruebas unitarias y de integración
├── .env # Variables de entorno (NO versionar)
├── .gitignore
├── alembic.ini
├── pyproject.toml # O requirements.txt
└── README.md
## Configuración e Instalación (Desarrollo)

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/rucfacil.git # Reemplaza con tu URL
    cd rucfacil
    ```
2.  **Crear y activar un entorno virtual:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt 
    # O si usas Poetry/PDM: poetry install / pdm install
    ```
4.  **Configurar variables de entorno:**
    *   Copiar `.env.example` (si existe) a `.env`.
    *   Editar `.env` con la configuración de tu base de datos (DATABASE_URL), SECRET_KEY para JWT, etc.
    ```
    DATABASE_URL="postgresql+asyncpg://user:password@host:port/database_name" # Ejemplo para PostgreSQL asíncrono
    SECRET_KEY="tu_super_secreto_aqui"
    # ... otras variables ...
    ```
5.  **Configurar Alembic:**
    *   Asegúrate de que `sqlalchemy.url` en `alembic.ini` coincida con tu `DATABASE_URL`.
    *   Revisa `alembic/env.py` para que importe correctamente tus modelos de `app.models` y `Base` de `app.db.base_class`.
6.  **Aplicar migraciones de base de datos:**
    ```bash
    alembic upgrade head
    ```
7.  **Ejecutar la aplicación (desarrollo):**
    ```bash
    uvicorn app.main:app --reload
    ```
    La aplicación estará disponible en `http://127.0.0.1:8000`.

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, revisa las guías de contribución (si existen) o abre un issue para discutir cambios mayores.

## Licencia

[Especifica tu licencia aquí, ej: MIT]
