# RECOVERY_HTTPS_CERTIFICATE.md

## Symptom

The website is no longer reachable in HTTPS.

Browser error:

```text
ERR_CONNECTION_REFUSED
```

or

```text
SSL_ERROR
```

Nginx status:

```bash
systemctl status nginx
```

Typical error:

```text
cannot load certificate
/etc/letsencrypt/live/molonari.io/fullchain.pem
```

## Step 1 - Verify certificate status

```bash
certbot certificates
```

Verify:

```bash
ls -l /etc/letsencrypt/live/
```

## Step 2 - Disable HTTPS temporarily

Edit:

```bash
nano /etc/nginx/sites-available/molonari.io
```

Remove or comment the HTTPS server block.

Keep only HTTP access:

```nginx
server {
    listen 80;
    listen [::]:80;

    server_name molonari.io www.molonari.io;

    root /var/www/html/molonari.io/wordpress;
    index index.php index.html index.htm;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
    }
}
```

Disable additional SSL virtual hosts if necessary.

Verify:

```bash
grep -R "ssl_certificate" /etc/nginx/sites-enabled/
```

## Step 3 - Restart nginx

```bash
nginx -t
systemctl restart nginx
```

Verify:

```bash
curl -I http://localhost
```

## Step 4 - Recreate certificate

```bash
certbot certonly --webroot \
  -w /var/www/html/molonari.io/wordpress \
  -d molonari.io \
  -d www.molonari.io
```

Verify:

```bash
ls -l /etc/letsencrypt/live/molonari.io/
```

Expected files:

```text
fullchain.pem
privkey.pem
```

## Step 5 - Restore HTTPS configuration

Restore nginx HTTPS block:

```nginx
ssl_certificate     /etc/letsencrypt/live/molonari.io/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/molonari.io/privkey.pem;

include /etc/letsencrypt/options-ssl-nginx.conf;
ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
```

Restore HTTP → HTTPS redirection.

## Step 6 - Reload nginx

```bash
nginx -t
systemctl reload nginx
```

## Step 7 - Validate

```bash
curl -Ik https://molonari.io
```

Expected:

```text
HTTP/1.1 200 OK
```

Verify renewal:

```bash
certbot renew --dry-run
```

Expected:

```text
Congratulations, all simulated renewals succeeded
```

## Backup

Create backup:

```bash
tar czf /root/molonari_https_backup_$(date +%Y%m%d).tar.gz \
    /etc/nginx \
    /etc/letsencrypt
```
