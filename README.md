# Proyecto: Sistema de Gestión "Doble5"

Este es un sistema de gestión administrativa y operativa para canchas de fútbol, desarrollado con Django y Docker.

## Requisitos Previos

- Docker
- Docker Compose

## Instalación y Ejecución (Entorno de Desarrollo)

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Doble5
   ```

2. **Construir y levantar los contenedores:**
   El siguiente comando construirá la imagen de Docker para la aplicación de Django, levantará el servicio de la aplicación y la base de datos PostgreSQL.
   ```bash
   docker-compose up --build
   ```
   La primera vez que se ejecute, puede tardar unos minutos en construir la imagen y descargar la de PostgreSQL.

3. **Crear las migraciones y migrar la base de datos:**
   En una nueva terminal, con los contenedores corriendo, ejecuta los siguientes comandos para preparar la base de datos.
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

4. **Crear un superusuario:**
   Para poder acceder al panel de administración de Django, necesitas crear un superusuario.
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
   Sigue las instrucciones en la terminal para crear tu usuario.

5. **Acceder a la aplicación:**
   Una vez que los contenedores estén en funcionamiento y la base de datos esté migrada, puedes acceder al panel de administración en tu navegador:
   [http://localhost:8000/admin](http://localhost:8000/admin)

   Usa las credenciales del superusuario que creaste en el paso anterior.

---

## Despliegue en Producción

Para desplegar esta aplicación en un servidor de producción (por ejemplo, un VPS con Ubuntu), sigue estos pasos:

1. **Preparación del Servidor:**
   - Conéctate a tu servidor a través de SSH.
   - Asegúrate de que tu sistema esté actualizado:
     ```bash
     sudo apt update && sudo apt upgrade -y
     ```

2. **Instalar Docker y Docker Compose:**
   - Sigue las instrucciones oficiales para instalar Docker Engine en tu distribución de Linux: [Get Docker](https://docs.docker.com/engine/install/ubuntu/)
   - Instala Docker Compose:
     ```bash
     sudo apt install docker-compose-plugin
     ```

3. **Clonar el Repositorio:**
   - Clona el proyecto en tu servidor:
     ```bash
     git clone <URL_DEL_REPOSITORIO>
     cd Doble5
     ```

4. **Configuración del Entorno de Producción:**
   - **IMPORTANTE:** Crea un archivo `.env` en la raíz del proyecto para gestionar las variables de entorno de forma segura. **No subas este archivo a tu repositorio de Git.**
     ```bash
     nano .env
     ```
   - Añade las siguientes variables, reemplazando los valores de ejemplo:
     ```env
     SECRET_KEY=tu_super_secreto_aqui_muy_largo_y_dificil
     DEBUG=0
     ALLOWED_HOSTS=tu_dominio.com,www.tu_dominio.com,la_ip_de_tu_servidor
     POSTGRES_DB=doble5_prod
     POSTGRES_USER=doble5_user
     POSTGRES_PASSWORD=una_contraseña_muy_segura_para_postgres
     ```
   - Asegúrate de que `Doble5/settings.py` esté configurado para leer estas variables (usando `os.environ.get()`).

5. **Ajustes en `docker-compose.yml` para Producción:**
   - **Volúmenes Persistentes:** Asegúrate de que el volumen de la base de datos (`doble5_db`) esté correctamente configurado para que los datos no se pierdan al reiniciar los contenedores.
   - **Puertos:** El `docker-compose.yml` actual expone el puerto `8000`. En producción, es recomendable usar un servidor proxy inverso como Nginx o Traefik para gestionar el tráfico en los puertos 80/443 y apuntarlo al contenedor de Django.

6. **Construir y Ejecutar en Modo Detached:**
   - Levanta los servicios en segundo plano (`-d`):
     ```bash
     docker-compose up --build -d
     ```

7. **Comandos Iniciales de Django:**
   - Ejecuta las migraciones de la base de datos:
     ```bash
     docker-compose exec web python manage.py migrate
     ```
   - Recolecta los archivos estáticos:
     ```bash
     docker-compose exec web python manage.py collectstatic --noinput
     ```
   - Crea un superusuario para producción:
     ```bash
     docker-compose exec web python manage.py createsuperuser
     ```

8. **Acceder a la Aplicación:**
   - Si no estás usando un proxy inverso, la aplicación debería estar disponible en `http://<la_ip_de_tu_servidor>:8000`.
   - Si configuraste un dominio y un proxy inverso, deberías poder acceder a través de tu dominio.

9. **Mantenimiento:**
   - Para ver los logs de los contenedores:
     ```bash
     docker-compose logs -f
     ```
   - Para detener los servicios:
     ```bash
     docker-compose down
     ```
