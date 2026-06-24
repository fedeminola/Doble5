# Proyecto: Sistema de Gestión "Doble5"

Este es un sistema de gestión administrativa y operativa para canchas de fútbol, desarrollado con Django y Docker.

## Entornos

Este proyecto está configurado para dos entornos:

1.  **Desarrollo:** Utiliza `docker-compose.yml`. Está pensado para un entorno local, con la base de datos y los servicios corriendo en Docker.
2.  **Producción:** Utiliza `docker-compose.prod.yml`. Este archivo está optimizado para producción, con volúmenes persistentes y una configuración más segura.

---

## Instalación y Ejecución (Entorno de Desarrollo)

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd Doble5
    ```

2.  **Configurar el entorno local:**
    - Copia el archivo de ejemplo `.env.example` a un nuevo archivo llamado `.env`.
    ```bash
    cp .env.example .env
    ```
    - Abre el archivo `.env` y asigna una contraseña a `POSTGRES_PASSWORD`. Para desarrollo, cualquier valor funcionará.

3.  **Construir y levantar los contenedores:**
    ```bash
    docker-compose up --build
    ```

4.  **Ejecutar comandos de Django (en otra terminal):**
    ```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python setup_groups.py
    docker-compose exec web python manage.py createsuperuser
    ```

5.  **Acceder a la aplicación:**
    - Panel de Administración: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## Despliegue en Producción con Nginx

Para desplegar esta aplicación en un servidor de producción (ej. un VPS con Ubuntu) usando Nginx como proxy inverso, sigue estos pasos:

1.  **Preparación del Servidor:**
    - Conéctate a tu servidor vía SSH.
    - Instala Nginx:
      ```bash
      sudo apt update && sudo apt upgrade -y
      sudo apt install nginx -y
      ```

2.  **Instalar Docker y Docker Compose:**
    - **Docker:** Sigue la guía oficial: [Get Docker](https://docs.docker.com/engine/install/ubuntu/)
    - **Docker Compose:**
      ```bash
      sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      sudo chmod +x /usr/local/bin/docker-compose
      ```

3.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd Doble5
    ```

4.  **Crear Directorios Compartidos para Archivos Estáticos:**
    - Crea directorios en `/srv` para los archivos estáticos y multimedia, y asigna los permisos adecuados.
      ```bash
      sudo mkdir -p /srv/doble5/static
      sudo mkdir -p /srv/doble5/media
      sudo chown -R $USER:www-data /srv/doble5
      sudo chmod -R 775 /srv/doble5
      ```

5.  **Configuración del Entorno de Producción:**
    - Copia el archivo de ejemplo `.env.example` a `.env` (si no lo hiciste para desarrollo):
      ```bash
      cp .env.example .env
      ```
    - Abre el archivo `.env` y edita las variables para tu entorno de producción. Asegúrate de:
      - Generar una `SECRET_KEY` nueva y segura.
      - Establecer `DEBUG=0`.
      - Configurar `ALLOWED_HOSTS` con tu dominio y la IP del servidor.
      - Configurar `CSRF_TRUSTED_ORIGINS` con tu dominio (ej. `https://tu_dominio.com`).
      - Establecer una contraseña segura para `POSTGRES_PASSWORD`.

6.  **Construir y Ejecutar Contenedores de Producción:**
    - Usa el archivo `docker-compose.prod.yml` para construir y correr los contenedores en segundo plano (`-d`):
      ```bash
      docker-compose -f docker-compose.prod.yml up --build -d
      ```

7.  **Comandos Iniciales de Django (Producción):**
    - Ejecuta las migraciones, la configuración de grupos y la recolección de archivos estáticos.
      ```bash
      docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
      docker-compose -f docker-compose.prod.yml exec web python setup_groups.py
      docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
      ```
    - Crea un superusuario para el entorno de producción:
      ```bash
      docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
      ```

8.  **Configurar Nginx como Proxy Inverso:**
    - El archivo `doble5.conf` en este repositorio contiene la configuración recomendada. Cópialo a `/etc/nginx/sites-available/doble5` en tu servidor.
    - Asegúrate de que el contenido del archivo de Nginx apunte a los directorios compartidos:
      ```nginx
      # Contenido del archivo doble5.conf
      server {
          listen 80;
          server_name tu_dominio.com www.tu_dominio.com;

          access_log /var/log/nginx/doble5_access.log;
          error_log /var/log/nginx/doble5_error.log;

          location / {
              proxy_pass http://127.0.0.1:8000;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;
          }

          location /static/ {
              alias /srv/doble5/static/;
          }

          location /media/ {
              alias /srv/doble5/media/;
          }
      }
      ```
    - Activa la configuración:
      ```bash
      sudo ln -s /etc/nginx/sites-available/doble5 /etc/nginx/sites-enabled/
      ```
    - Verifica y reinicia Nginx:
      ```bash
      sudo nginx -t
      sudo systemctl restart nginx
      ```

9.  **(Recomendado) Configurar SSL con Let's Encrypt:**
    - Instala Certbot: `sudo apt install certbot python3-certbot-nginx`
    - Obtén el certificado: `sudo certbot --nginx -d tu_dominio.com -d www.tu_dominio.com`

10. **Acceder a la Aplicación:**
    - Tu aplicación estará disponible en `https://tu_dominio.com`.

11. **Mantenimiento (Producción):**
    - Logs: `docker-compose -f docker-compose.prod.yml logs -f`
    - Detener: `docker-compose -f docker-compose.prod.yml down`
