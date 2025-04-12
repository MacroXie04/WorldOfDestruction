# WorldOfDestruction



### Deploy via Gunicorn and Nginx

```bash
gunicorn WorldOfDestruction.wsgi:application --bind unix:/tmp/wod.sock --chdir /var/www/WorldOfDestruction --workers 3 --timeout 120 --daemon
```