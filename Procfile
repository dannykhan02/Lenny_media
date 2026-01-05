cat > Procfile << 'EOF'
web: flask db upgrade && gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 300 --access-logfile - --error-logfile - run:app
EOF