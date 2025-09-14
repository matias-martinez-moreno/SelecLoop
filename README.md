# SelecLoop

SelecLoop is a collaborative web platform that collects and organizes anonymous reviews about job selection processes, helping candidates to better prepare themselves and companies to improve their recruitment practices.

## Team Members
- Matías Martínez
- Tomás Giraldo
- Luis Alfonso agudelo

## 🏗️ **Arquitectura del Sistema**

### **Estilos Arquitectónicos Usados**

#### **Tipo de Aplicación**
- **Web**: Plataforma web responsive que funciona en navegadores modernos

#### **Estilo Arquitectónico**
- **Cliente/Servidor (Implementación)**: La aplicación sigue un modelo Cliente-Servidor. El navegador web (cliente) realiza peticiones HTTP al servidor Django, el cual procesa la lógica de negocio, accede a la base de datos y devuelve una respuesta HTML.
- **Layered (Estructura)/3-Tiers**: Django implementa de forma nativa una arquitectura en capas, conocida como Modelo-Vista-Template (MVT), una variante del patrón MVC. Esto separa la lógica en:
  - **Capa de Presentación (Template)**: Gestiona la interfaz de usuario (.html)
  - **Capa de Lógica de Negocio (Vista)**: Procesa las peticiones y coordina la interacción entre el modelo y la plantilla (views.py)
  - **Capa de Acceso a Datos (Modelo)**: Define la estructura de los datos y se comunica con la base de datos a través del ORM de Django (models.py)
- **Object-Oriented (Estructura)**: El desarrollo se basa en el paradigma orientado a objetos, utilizando clases de Python para definir los modelos de datos, las vistas y otras lógicas del sistema.

#### **Lenguaje de Programación**
- **Python (versión 3.13)**

#### **Aspectos Técnicos**
- **Base de Datos Relacional**: SQLite para desarrollo, con planes de migrar a PostgreSQL para producción
- **Frameworks**: Django (versión 5.2) para el backend, Bootstrap (versión 5.3) para el diseño frontend

### **Funcionalidades Implementadas**

#### **Sistema de Geo-localización**
- Campos de ubicación estructurados (ciudad, región, país) en el modelo Company
- Búsqueda y filtrado de empresas por ubicación geográfica
- Información geo en reseñas y perfiles de empresa

#### **Optimización SEO Avanzada**
- Meta tags dinámicos personalizados por página
- Open Graph y Twitter Cards para compartir en redes sociales
- Sitemap.xml generado automáticamente con todas las empresas
- Robots.txt configurado para motores de búsqueda
- Structured Data (JSON-LD) para empresas y reseñas
- URLs optimizadas para SEO

#### **Sistema de Estadísticas y Analytics**
- Dashboards personalizados según rol de usuario
- Gráficos dinámicos generados con Matplotlib
- Métricas específicas:
  - **Candidatos**: Calificación general, tiempo de respuesta, reseñas recientes
  - **Empresas**: Ratio de aprobación, SLA, estado de reseñas
- Exportación de datos en formato CSV

#### **Sistema de Roles y Seguridad**
- Tres tipos de usuarios: Candidatos, Representantes de Empresa, Staff
- Control de acceso granular basado en roles
- Autenticación segura con Django
- Moderación de reseñas por staff

### **Estructura del Proyecto**

```
SelecLoop/
├── core/                          # Aplicación principal Django
│   ├── models.py                  # Modelos: Company, Review, UserProfile
│   ├── views.py                   # Lógica de negocio y controladores
│   ├── forms.py                   # Formularios para creación/edición
│   ├── urls.py                    # Configuración de rutas URL
│   ├── admin.py                   # Panel de administración
│   ├── templates/core/            # Templates HTML
│   └── static/core/               # Archivos estáticos
├── selecloop_project/             # Configuración del proyecto
│   ├── settings.py                # Configuración global
│   ├── urls.py                    # Rutas principales
│   ├── wsgi.py                    # Configuración WSGI
│   └── asgi.py                    # Configuración ASGI
├── staticfiles/                   # Archivos estáticos (generado)
├── db.sqlite3                     # Base de datos
├── manage.py                      # Script de gestión Django
├── requirements.txt               # Dependencias Python
└── README.md                      # Esta documentación
```

### **Patrones de Diseño Utilizados**

1. **MVC (Model-View-Controller)**: Implementado a través del patrón MVT de Django
2. **Repository Pattern**: ORM de Django abstrae el acceso a datos
3. **Template Method**: Vistas basadas en clases y herencia
4. **Decorator Pattern**: Decoradores para autenticación y permisos
5. **Observer Pattern**: Señales de Django para eventos del sistema
6. **Factory Pattern**: Creación de objetos a través de managers de Django

## Use of Artificial Intelligence in Development
During the development of this project, **Gemini** (Google) was used as a support tool for:
- Suggesting view structures and logic.  
- Assisting in error resolution and debugging.  
- Providing styling recommendations with Bootstrap.  

All AI-assisted contributions were reviewed, refined, and integrated by the author,  
who retains full responsibility for the final implementation.


##  Initial Setup

1.  **Clone Repository**
    ```bash
    git clone https://github.com/matias-martinez-moreno/SelecLoop.git
    cd SphereLink
    ```

2.  **Create & Activate Virtual Environment**
    ```bash
    python -m venv env
    
    # On Windows
    env\Scripts\activate
    
    # On macOS/Linux
    source env/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Database Migrations**
    ```bash
    python manage.py migrate
    ```

5.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run Server**
    ```bash
    python manage.py runserver
    ```
    The application will run at `http://127.0.0.1:8000/`.

##  Git Workflow

**Flow:** `development` → `feature-branch` → `merge` → `development`

1.  **Sync with `development`**
    ```bash
    git checkout development
    git pull origin development
    ```

2.  **Create Feature Branch**
    ```bash
    git checkout -b feature/your-feature-name
    ```

3.  **Commit Changes**
    ```bash
    # After making changes
    git add .
    git commit -m "feat: Short description of the feature"
    ```

4.  **Sync Branch Before Merging**
    ```bash
    git checkout development
    git pull origin development
    git checkout feature/your-feature-name
    git merge development
    ```
    *(Resolve any conflicts if they appear)*

5.  **Merge into `development`**
    ```bash
    git checkout development
    git merge feature/your-feature-name
    ```

6.  **Push to Remote**
    ```bash
    git push origin development
    ```

7.  **Delete Local Branch (Optional)**
    ```bash
    git branch -d feature/your-feature-name
    ```

## Managing Dependencies

To ensure all team members use the same package versions, follow this process when adding a new dependency.

1.  **Install the New Package**
    ```bash
    pip install new-package-name
    ```

2.  **Update the `requirements.txt` File**
    This command saves all current packages and their exact versions to the file.
    ```bash
    pip freeze > requirements.txt
    ```

3.  **Commit the `requirements.txt` File**
    Add the updated `requirements.txt` file to your commit. This ensures everyone on the team will install the new dependency when they set up the project or pull the latest changes.
