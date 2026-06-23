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

2.  **Construir y levantar los contenedores:**
    ```bash
    docker-compose up --build
    ```

3.  **Ejecutar comandos de Django (en otra terminal):**
    ```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser
    ```

4.  **Acceder a la aplicación:**
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

4.  **Configuración del Entorno de Producción:**
    - Crea un archivo `.env` en la raíz del proyecto:
      ```bash
      nano .env
      ```
    - Añade las siguientes variables (reemplaza los valores):
      ```env
      SECRET_KEY=tu_super_secreto_aqui_muy_largo_y_dificil
      DEBUG=0
      ALLOWED_HOSTS=tu_dominio.com,www.tu_dominio.com,la_ip_de_tu_servidor
      CSRF_TRUSTED_ORIGINS=https://tu_dominio.com,https://www.tu_dominio.com
      POSTGRES_DB=doble5_prod
      POSTGRES_USER=doble5_user
      POSTGRES_PASSWORD=una_contraseña_muy_segura_para_postgres
      ```

5.  **Construir y Ejecutar Contenedores de Producción:**
    - Usa el archivo `docker-compose.prod.yml` para construir y correr los contenedores en segundo plano (`-d`):
      ```bash
      docker-compose -f docker-compose.prod.yml up --build -d
      ```

6.  **Comandos Iniciales de Django (Producción):**
    - Ejecuta las migraciones y recolecta los archivos estáticos usando el archivo de producción:
      ```bash
      docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
      docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
      ```
    - Crea un superusuario para el entorno de producción:
      ```bash
      docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
      ```

7.  **Configurar Nginx como Proxy Inverso:**
    - El archivo `doble5.conf` en este repositorio contiene la configuración recomendada. Cópialo a tu servidor.
    - Crea un archivo de configuración en Nginx:
      ```bash
      sudo nano /etc/nginx/sites-available/doble5
      ```
    - Pega el contenido de `doble5.conf`, **reemplazando `tu_dominio.com`**. Las rutas de los alias para `/static/` y `/media/` apuntan a las ubicaciones por defecto de los volúmenes de Docker.
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

          # El nombre del volumen es <nombre_del_directorio>_<nombre_del_volumen>.
          # Para confirmar la ruta, ejecuta: sudo docker volume inspect Doble5_static_volume
          location /static/ {
              alias /var/lib/docker/volumes/Doble5_static_volume/_data/;
          }

          location /media/ {
              alias /var/lib/docker/volumes/Doble5_media_volume/_data/;
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

8.  **(Recomendado) Configurar SSL con Let's Encrypt:**
    - Instala Certbot: `sudo apt install certbot python3-certbot-nginx`
    - Obtén el certificado: `sudo certbot --nginx -d tu_dominio.com -d www.tu_dominio.com`

9.  **Acceder a la Aplicación:**
    - Tu aplicación estará disponible en `https://tu_dominio.com`.

10. **Mantenimiento (Producción):**
    - Logs: `docker-compose -f docker-compose.prod.yml logs -f`
    - Detener: `docker-compose -f docker-compose.prod.yml down`
