web: python manage.py migrate ; python manage.py ensure_superuser ; python manage.py collectstatic --noinput ; gunicorn amfit.wsgi:application --log-file -
