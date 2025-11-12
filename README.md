# SelecLoop

SelecLoop es una plataforma web colaborativa que recopila y organiza reseñas sobre procesos de selección laboral. Ayuda a los candidatos a prepararse mejor para sus entrevistas y a las empresas a mejorar sus prácticas de reclutamiento mediante feedback estructurado y anónimo.

## Integrantes

- Matías Martínez
- Tomás Giraldo
- Luis Alfonso Agudelo

## Setup

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/matias-martinez-moreno/SelecLoop.git
   cd SelecLoop
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv env
   
   # Windows
   env\Scripts\activate
   
   # macOS/Linux
   source env/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar migraciones**
   ```bash
   python manage.py migrate
   ```

5. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

6. **Ejecutar servidor**
   ```bash
   python manage.py runserver
   ```
   La aplicación estará disponible en `http://127.0.0.1:8000/`

## Workflow

**Flujo:** `development` → `feature-branch` → `merge` → `development`

1. **Sincronizar con `development`**
   ```bash
   git checkout development
   git pull origin development
   ```

2. **Crear rama de feature**
   ```bash
   git checkout -b feature/nombre-del-feature
   ```

3. **Hacer commit de cambios**
   ```bash
   git add .
   git commit -m "feat: Descripción breve del feature"
   ```

4. **Sincronizar rama antes de mergear**
   ```bash
   git checkout development
   git pull origin development
   git checkout feature/nombre-del-feature
   git merge development
   ```
   *(Resolver conflictos si aparecen)*

5. **Mergear a `development`**
   ```bash
   git checkout development
   git merge feature/nombre-del-feature
   ```

6. **Subir a remoto**
   ```bash
   git push origin development
   ```

7. **Eliminar rama local (opcional)**
   ```bash
   git branch -d feature/nombre-del-feature
   ```
