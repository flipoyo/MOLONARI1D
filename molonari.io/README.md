# Deploying the MOLONARI website

This file aims to explain the process of deploying the Molonari website.

## Overall architecture

The `molonari.io` website aims to provide an entry point for MOLONARI users. It features a landing page and a quickstart for understanding the project and starting to build a device.

Anticipating further customization (dataloggers API, remote MCMC, chatbot and code-hosting), we opted for a `Virtual Private Server` (VPS), which is basically a remotely-accessible computer that never turns off. The VPS is hosted by **LWS** and runs on Debian 12.

The website (html pages) is hosted by the VPS and built with WordPress. It should be accessible with the domain name (DNS) `molonari.io`, which was bought on **Namecheap**.

The documented production setup remains the WordPress deployment described in `website/wordpress_config.md` and the related WordPress guides in `website/`. In parallel, the repository now also contains an **exploratory Django option** for quick deployments and experiments from the repo checkout.

## Configuration

For now, we split the configuration process into three parts:
- configuring the DNS (molonari.io) with Namecheap: *see below*
- configuring the VPS with LWS: *see `server/vps_config.md`*
- configuring WordPress on the VPS: *see `website/wordpress_config.md`*

## Exploratory Django quick deployment

The `molonari.io/website/` directory now also contains an exploratory Django site that can be packaged directly from the repository with **pixi**. This is intended for quick deployments, previews, and experimentation; it does **not** replace the WordPress deployment documentation above.

### Local run

```bash
cd /path/to/MOLONARI1D
pixi install
pixi run website-migrate
pixi run website-dev
```

Open http://127.0.0.1:8000/ in your browser.

### Optional live sensor data

```bash
export MOLONAVIZ_DB_PATH=/path/to/Molonari.sqlite
pixi run website-dev
```

### Exploratory VPS deployment

```bash
cd /var/www/molonari.io
pixi install
export DJANGO_SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="molonari.io,www.molonari.io"
pixi run website-migrate
pixi run website-collectstatic
pixi run website-serve
```

Sample Nginx and Gunicorn files for this exploratory Django option are available in `molonari.io/website/deployment/`.

## Configuring the DNS

The domain name has to redirect requests to the VPS. To do so, we configure the domain list directly on Namecheap. IPv4 redirections are achieved with `A records`.
- Find the fixed IPv4 address of the VPS on the VPS provider website (`Panel` > `Serveurs` > `IPv4` on LWS)
- On the DNS provider's control panel, find the subdomains list (`Domain List` > `Advanced DNS` on Namecheap)
- Add a record:
    - type: `A record`
    - host: `@`
    - value: the VPS's IPv4
    - TTL: automatic

This process will redirect all requests to `http(s)://molonari.io/` to the VPS.

The `@` host can be changed to any value, for example `www` or `mysubdomain`. In that case, the DNS will forward requests addressed to `http(s)://www.molonari.io/` or `http(s)://mysubdomain.molonari.io/`.

- Important, to avoid certificate renewal failure, add a record:
    - type: `CNAME Record`
    - host: `www`
    - value: `molonari.io`
    - TTL: automatic
This maps: www.molonari.io → molonari.io 

**Checking:** We can verify that the DNS has been updated worldwide with the website [dnschecker.org](https://dnschecker.org/).
