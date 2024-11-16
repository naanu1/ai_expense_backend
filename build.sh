#!/usr/bin/env bash
echo "Building the project..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Make migrations..."
python manage.py makemigrations

echo "Migrate..."
python manage.py migrate

echo "Collect static..."
python manage.py collectstatic --no-input

# 7. Procfile (create in backend root folder)
web: gunicorn your_project_name.wsgi:application