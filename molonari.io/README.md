# Deploying molonari.io with Django

This directory contains the Django-based website for [molonari.io](https://molonari.io), replacing the previous WordPress setup. Using Django keeps the entire MOLONARI1D stack in Python, and the repository now uses **pixi** rather than pip for Python environments.

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
cd /path/to/MOLONARI1D
pixi install
# installs the local molonari.io website package from molonari.io/website
pixi run website-migrate
pixi run website-dev
```

Open http://127.0.0.1:8000/ in your browser.

### Live Sensor Data

To enable the sensor data page, point `MOLONAVIZ_DB_PATH` at a Molonaviz SQLite database:

```bash
export MOLONAVIZ_DB_PATH=/path/to/Molonari.sqlite
pixi run website-dev
```

## Running Tests

```bash
cd /path/to/MOLONARI1D
pixi run website-test
```

## Production Deployment

### 1. Configure the DNS

The domain name must redirect requests to the VPS. On Namecheap:

1. Find the fixed IPv4 address of the VPS (`Panel` > `Serveurs` > `IPv4` on LWS).
2. On Namecheap, go to `Domain List` > `Advanced DNS` and add:
   - **A record**: host `@`, value = VPS IPv4, TTL automatic
   - **CNAME record**: host `www`, value `molonari.io`, TTL automatic

Verify propagation at [dnschecker.org](https://dnschecker.org/).

### 2. Prepare the VPS

On the VPS (see `server/vps_config.md` for SSH access details):

```bash
apt update && apt install python3 python3-venv nginx certbot python3-certbot-nginx

# Clone the repository
git clone https://github.com/flipoyo/MOLONARI1D.git /var/www/molonari.io
cd /var/www/molonari.io

# Install pixi
curl -fsSL https://pixi.sh/install.sh | bash
export PATH="$HOME/.pixi/bin:$PATH"

# Resolve dependencies and package the local Django site from the repo checkout
pixi install
```

### 3. Configure Django for Production

```bash
export DJANGO_SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="molonari.io,www.molonari.io"
export MOLONAVIZ_DB_PATH="/path/to/Molonari.sqlite"   # optional

pixi run website-migrate
pixi run website-collectstatic
```

### 4. Run with Gunicorn

```bash
cd /var/www/molonari.io
pixi run website-serve
```

Or create a systemd service for automatic startup — see the deployment directory for a sample Nginx config (`deployment/nginx_molonari.conf`).

### 5. Set up HTTPS

```bash
certbot --nginx -d molonari.io -d www.molonari.io
```
