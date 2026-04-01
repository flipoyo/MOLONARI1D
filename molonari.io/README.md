# Deploying molonari.io with Django

This directory contains the Django-based website for [molonari.io](https://molonari.io), replacing the previous WordPress setup. Using Django keeps the entire MOLONARI1D stack in Python.

## Overall Architecture

The `molonari.io` website provides an entry point for MOLONARI users with a landing page, project documentation and live sensor data display. It is deployed on a **Virtual Private Server** (VPS) hosted by **LWS** (Debian 12) and accessible via the domain `molonari.io` (DNS managed on **Namecheap**).

```
Client  ──HTTPS──▶  Nginx (reverse proxy)  ──▶  Gunicorn  ──▶  Django
                      └── serves /static/          └── WSGI app
```

## Project Structure

```
molonari.io/
├── README.md                        # This file
├── server/
│   └── vps_config.md                # VPS & Nginx setup guide
└── website/                         # Django project root
    ├── manage.py                    # Django management CLI
    ├── requirements.txt             # Python dependencies
    ├── molonari_site/               # Project settings & URL config
    ├── pages/                       # Static content pages app
    │   ├── views.py
    │   ├── urls.py
    │   ├── templates/pages/         # HTML templates
    │   └── static/pages/css/        # Stylesheet
    ├── data_viewer/                 # Sensor data display app
    │   ├── views.py                 # Reads Molonaviz SQLite DB
    │   ├── urls.py
    │   └── templates/data_viewer/
    └── deployment/
        ├── gunicorn.conf.py         # Gunicorn config
        └── nginx_molonari.conf      # Nginx site config
```

## Local Development

```bash
cd molonari.io/website

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

### Live Sensor Data

To enable the sensor data page, point `MOLONAVIZ_DB_PATH` at a Molonaviz SQLite database:

```bash
export MOLONAVIZ_DB_PATH=/path/to/Molonari.sqlite
python manage.py runserver
```

## Running Tests

```bash
cd molonari.io/website
python manage.py test
```

## Production Deployment

### 1. Configure the DNS

See the **Configuring the DNS** section of the previous `README.md` — the A-record and CNAME setup on Namecheap remains the same.

### 2. Prepare the VPS

On the VPS (see `server/vps_config.md` for SSH access details):

```bash
apt update && apt install python3 python3-venv nginx certbot python3-certbot-nginx

# Clone the repository
git clone https://github.com/flipoyo/MOLONARI1D.git /var/www/molonari.io
cd /var/www/molonari.io/molonari.io/website

# Create a virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Django for Production

```bash
export DJANGO_SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="molonari.io,www.molonari.io"
export MOLONAVIZ_DB_PATH="/path/to/Molonari.sqlite"   # optional

python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Run with Gunicorn

```bash
gunicorn -c deployment/gunicorn.conf.py molonari_site.wsgi
```

Or create a systemd service for automatic startup — see the deployment directory for a sample Nginx config (`deployment/nginx_molonari.conf`).

### 5. Set up HTTPS

```bash
certbot --nginx -d molonari.io -d www.molonari.io
```
