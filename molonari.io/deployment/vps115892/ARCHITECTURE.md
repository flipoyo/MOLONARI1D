# ARCHITECTURE.md

## Host

* Hostname: vps115892.serveur-vps.net
* Provider: LWS
* Type: Virtual Private Server (VPS)

## Operating System

* Debian GNU/Linux 12 (Bookworm)
* Kernel: Linux 6.12.38+deb13-amd64

Verification:

```bash
lsb_release -a
uname -a
```

## Core Services

### Web

* nginx
* PHP-FPM
* WordPress

Website:

* molonari.io
* [www.molonari.io](http://www.molonari.io)

Document root:

```text
/var/www/html/molonari.io/wordpress
```

### HTTPS

Certificate management:

* Certbot
* Let's Encrypt

Certificate location:

```text
/etc/letsencrypt/live/molonari.io/
```

Validation:

```bash
certbot renew --dry-run
```

### Mail

* Postfix

### DNS

* BIND (named)

### Hosting Control Panel

* ISPConfig

Main tasks executed every minute:

```bash
/usr/local/ispconfig/server/server.sh
/usr/local/ispconfig/server/cron.sh
```

Root crontab:

```bash
crontab -l
```

## Backup

Manual backup:

```bash
tar czf /root/molonari_https_backup_$(date +%Y%m%d).tar.gz \
    /etc/nginx \
    /etc/letsencrypt
```

Recommended backup directory:

```text
/root/backups
```

## Important Configuration Files

nginx:

```text
/etc/nginx/sites-available/molonari.io
```

Let's Encrypt:

```text
/etc/letsencrypt/live/molonari.io/
```

ISPConfig:

```text
/usr/local/ispconfig/
```

## Related Documentation

* INCIDENT_20260612.md
* RECOVERY_HTTPS_CERTIFICATE.md
