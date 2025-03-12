import os
import sys

# Add your project directory to the sys.path
path = '/home/sherimandyshop/sherimandyshop'
if path not in sys.path:
    sys.path.append(path)

# Set environment variable to tell Django where your settings.py is
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Set the 'PYTHONANYWHEREHOST' environment variable
os.environ['PYTHONANYWHEREHOST'] = 'true'

# Import Django and start the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
