# Sherimandyshop E-Commerce Platform

A complete online store solution built with Django, offering secure payments and easy product management.

## Setup Guide

### System Requirements
Python 3.9 or higher and MySQL database

### Basic Setup
Set up your workspace:
```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate

# Install packages
pip install -r requirements.txt
```

Add your database settings in `core/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
    }
}
```

Start the application:
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

Your store will be available at `http://127.0.0.1:8000`

## Admin Guide

### First-Time Setup
Create your admin account:
```bash
python manage.py createsuperuser
```
Enter your preferred username, email, and password when prompted.

### Managing Your Store
Access the admin panel at `/admin` using your login details.

The admin panel lets you control:
Your product catalog
Customer orders
User accounts
Payment tracking
Store content

### Important Security Steps
Set a strong admin password
Keep your secret key private
Use HTTPS in production
Check access logs regularly

## PythonAnywhere Setup

Update your database configuration:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sherimandyshop$default',
        'USER': 'sherimandyshop',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'sherimandyshop.mysql.pythonanywhere-services.com',
    }
}
```

Complete your setup:
1. Configure your MySQL database
2. Add your site to ALLOWED_HOSTS
3. Set up your static files
4. Reload your application

Need help? Contact us at lmtsoftwares@gmail.com
