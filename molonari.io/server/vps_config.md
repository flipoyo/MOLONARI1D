
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
