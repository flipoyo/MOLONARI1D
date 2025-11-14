# Deploying the MOLONARI website

This file aims to explain the process of deploying the Molonari website.

## Overall architecture

- the domain name (DNS) `molonari.io` was bought on Namecheap
- the VPS hosting is provided by LWS and runs on Debian 12
    - VPS stands for `Virtual Private Server`. A VPS is basically a remotely-accessible computer that never turns off.
- the website is built and run on the VPS with WordPress

## Configuring the DNS

The domain name has to redirect requests to the VPS. To do so, we configure the domain list directly on Namecheap. IPv4 redirections are achieved with `A records`.
- Find the fixed IPv4 address of the VPS on the VPS provider website (`Panel` > `Serveurs` > `IPv4` on LWS)
- On the DNS provider's control panel, find the subdomains list (`Domain List` > `Advanced DNS` on Namecheap)
- Add a record:
    - type: `A record`
    - host: `wwww`
    - value: the VPS's IPv4
    - TTL: automatic

This process will redirect all requests to `http(s)://www.molonari.io/` to the VPS.

We also add a similar entry with host `@`, which will redirect `http(s)://molonari.io/` requests.

**Checking:** We can verify that the DNS has been updated worldwide with the website [dnschecker.org](https://dnschecker.org/).

## Configuring the VPS

### Accessing the VPS

We access the VPS with an SSH connection. To initiate a connection, simply run `ssh root@vpsXXXXXX.serveur-vps.net` where `vpsXXXXXX.serveur-vps.net` is your VPS host name. You can find the VPS host name on the VPS provider control panel (`Panel` > `Serveurs` > `VPS-XXXXXX` on LWS). Then, enter the SSH password provided by the VPS provider.

The SSH password can be changed in the control panel.

Once connected, you should see the following line, meaning you're connected as root: `root@vps115892:~#`

### Link the VPS with the DNS

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

### Securing the connection

The website should run in `https`. To do so, we will use `certbot`. On the VPS, run:
- `apt install certbot python3-certbot-nginx`
- `certbot --nginx -d molonari.io -d www.molonari.io`

Now, you should be able to access `https://molonari.io/`

### Installing WordPress

We then install WordPress on the VPS.
- install and deploy PHP:
    - `apt install php-fpm php-mysql php-curl php-gd php-intl php-mbstring php-soap php-xml php-xmlrpc php-zip`
    - `systemctl start php8.1-fpm`
    - `systemctl enable php8.1-fpm`
- create a MySQL database for WordPress: log into MySQL with `mysql -u root` and execute the following commands:
    ```
    CREATE DATABASE wordpress_db;
    CREATE USER 'wordpress_user'@'localhost' IDENTIFIED BY 'your_strong_password';
    GRANT ALL PRIVILEGES ON wordpress_db.* TO 'wordpress_user'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```
- download and install WordPress:
    - `cd /tmp`
    - `wget https://wordpress.org/latest.tar.gz`
    - `tar -xzvf latest.tar.gz`
- move WordPress to the website's directory: `mv wordpress /var/www/html/molonari.io`
- and update the permissions:
    - `chown -R www-data:www-data /var/www/html/molonari.io`
    - `chmod -R 755 /var/www/html/molonari.io`
- configure nginx (`nano /etc/nginx/sites-available/molonari.io`) by updating the lines before the lines added by certbot:
    ```
    server {
        listen 80;
        server_name molonari.io www.molonari.io;
        root /var/www/html/molonari.io/wordpress;
        index index.php index.html index.htm;

        location / {
            try_files $uri $uri/ /index.php?$args;
        }

        location ~ \.php$ {
            include snippets/fastcgi-php.conf;
            fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;  # Adjust PHP version
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            include fastcgi_params;
        }

        # certbot lines...
    }
    ```
- restart nginx: `nginx -t` then `systemctl restart nginx`

You should now see the WordPress configuration page when opening `https://molonari.io`.


## Building with WordPress

### WordPress configuration

We now have to configure WordPress.
- Choose a language and click `Continue`
- Fill in the MySQL details created earlier
- Click `Submit` and then `Run the installation`
- Choose a title for the website and admin credentials
- Click `Install WordPress`

Now, when opening `https://molonari.io`, we should see the default WordPress page: "Blog, Hello world!". We can now build our website.

### Building pages

We can add a page with `New` > `Page`