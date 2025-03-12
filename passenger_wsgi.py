import os
import sys

from core.wsgi import application

# Add your site directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['PRODUCTION'] = 'True'
