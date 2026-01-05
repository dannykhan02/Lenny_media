release: flask db upgrade
web: gunicorn --bind :$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - run:app