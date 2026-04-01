
# Configuring the VPS

## Accessing the VPS

We access the VPS with an SSH connection. To initiate a connection, simply run `ssh root@vpsXXXXXX.serveur-vps.net` where `vpsXXXXXX.serveur-vps.net` is your VPS host name. You can find the VPS host name on the VPS provider control panel (`Panel` > `Serveurs` > `VPS-XXXXXX` on LWS). Then, enter the SSH password provided by the VPS provider.

The SSH password can be changed in the control panel.

Once connected, you should see the following line, meaning you're connected as root: `root@vps115892:~#`

## Link the VPS with the DNS

The WordPress website will be served by either `nginx` or `apache`. In our case, we chose `nginx`.

We start by disabling and removing `apache` from the VPS:
- `systemctl stop apache2`
- `systemctl disable apache2`
- do the same for all services linked with apache (apache-html-cache...)
- `apt purge apache2 apache2-utils apache2-bin apache2-data`

Then, we install `nginx`:
- `apt install nginx`
- `systemctl enable nginx`
- `systemctl start nginx`

We create a simple and temporary html page for testing.
- `mkdir /var/www/html/molonari.io`
- `nano /var/www/html/molonari.io` and copy `<html><body><h1>Coming Soon: WordPress Site!</h1></body></html>`. save (Ctrl+S) and exit (Ctrl+X)

Then, we configure `nginx` to accept requests from `http://molonari.io`.
- `nano /etc/nginx/sites-available/molonari.io` and copy 
    ```
    server {
        server_name molonari.io www.molonari.io;
        root /var/www/html/molonari.io;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }
    }
    ```
- enable this configuration with a symlink: `ln -s /etc/nginx/sites-available/molonari.io /etc/nginx/sites-enabled/`
- test the configuration: `nginx -t`
- reload nginx: `systemctl restart nginx`

Now, you should be able to open `http://(www.)molonari.io` on any browser and succesfully fetch `index.html`.

**Troubleshooting:** If, for some reason, `nginx` does not work, you can verify which ports are used with `ss -tulnp` and kill the programs accordingly.

## Securing the connection

The website should run in `https`. To do so, we will use `certbot`. On the VPS, run:
- `apt install certbot python3-certbot-nginx`
- `certbot --nginx -d molonari.io -d www.molonari.io`

Now, you should be able to access `https://molonari.io/`

## Full NGINX configuration (post-certbot)

After certbot has generated the certificate, replace the entire content of `/etc/nginx/sites-available/molonari.io` with the following:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name molonari.io www.molonari.io;

    return 301 https://molonari.io$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name molonari.io www.molonari.io;

    root /var/www/html/molonari.io/wordpress;
    index index.php index.html index.htm;

    ssl_certificate /etc/letsencrypt/live/molonari.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/molonari.io/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    ssl_stapling off;
    ssl_stapling_verify off;
    # NOTE: OCSP stapling is disabled while the revoked certificate is being replaced.
    # Once certbot renew --force-renewal has been run and the new certificate is verified
    # (see section below), re-enable stapling by replacing the two lines above with:
    #   ssl_stapling on;
    #   ssl_stapling_verify on;
    #   ssl_trusted_certificate /etc/letsencrypt/live/molonari.io/chain.pem;
    #   resolver 8.8.8.8 8.8.4.4 valid=300s;
    #   resolver_timeout 5s;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;  # Adjust PHP version as needed
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|webp)$ {
        expires max;
        log_not_found off;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

**Notes on this configuration:**
- The HTTP block redirects all traffic (both `molonari.io` and `www.molonari.io`) with a 301 to the canonical HTTPS URL without `www`.
- Both server names are covered by the certificate, so `www.molonari.io` does not fall back to a default vhost.
- `ssl_stapling` is intentionally disabled here. It should remain `off` until a fresh, non-revoked certificate has been obtained (see section below). Once the certificate is renewed, it can be re-enabled.
- `include snippets/fastcgi-php.conf;` already sets `SCRIPT_FILENAME` on Debian, so the directive is not duplicated.

After editing, ensure the symlink in `sites-enabled` exists:
```
ls -l /etc/nginx/sites-enabled/
```
If the symlink is missing, create it:
```
ln -s /etc/nginx/sites-available/molonari.io /etc/nginx/sites-enabled/molonari.io
```

Remove the default site if it exists to avoid conflicts:
```
rm -f /etc/nginx/sites-enabled/default
```

Then validate and reload:
```
nginx -t
systemctl start nginx
systemctl reload nginx
```

## Renewing a revoked certificate (fixing Firefox SEC_ERROR_REVOKED_CERTIFICATE)

Firefox performs strict OCSP (Online Certificate Status Protocol) checks and will show `SEC_ERROR_REVOKED_CERTIFICATE` if the Let's Encrypt **intermediate** certificate used to sign your certificate has been revoked (e.g. the E8 intermediate revocation in February 2026). Chrome and Edge use a soft-fail policy and are unaffected.

To fix this, force-renew the certificate to obtain a new one signed by a non-revoked intermediate:
```
certbot renew --force-renewal
systemctl reload nginx
```

Verify that the new certificate is no longer using the revoked intermediate:
```
openssl s_client -connect molonari.io:443 -servername molonari.io | openssl x509 -noout -serial -fingerprint -issuer
```

The serial number must differ from the revoked certificate's serial (the one reported in the Firefox error — e.g. `058D237F541B0DEA66A95818E05434477D5D` in the February 2026 incident). If the serial is unchanged, nginx is still serving the old certificate and the renewal did not succeed — check `/etc/letsencrypt/live/molonari.io/`.

You can also verify the HTTP redirect and HTTPS response with:
```
curl -I http://molonari.io/
curl -I http://www.molonari.io/
curl -I https://molonari.io/
```
- HTTP requests should return `301 Moved Permanently`.
- The HTTPS request should return `200 OK`.
