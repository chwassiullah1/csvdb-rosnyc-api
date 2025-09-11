import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edwin_backend.settings')

app = Celery('edwin_backend')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks inside all apps (tasks.py)
app.autodiscover_tasks()
