# Configuring WordPress on the VPS

## Installing WordPress

We first have to install WordPress. From a root SSH terminal:
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

## WordPress configuration

We now have to configure WordPress.
- Choose a language and click `Continue`
- Fill in the MySQL details created earlier
- Click `Submit` and then `Run the installation`
- Choose a title for the website and admin credentials
- Click `Install WordPress`

Now, when opening `https://molonari.io`, we should see the default WordPress page: "Blog, Hello world!". We can now build our website.

## Building pages

We can add a page with `New` > `Page`