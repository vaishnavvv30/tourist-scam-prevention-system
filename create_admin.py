import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'scamguard.settings'
django.setup()
from django.contrib.auth.models import User
try:
    u = User.objects.create_superuser('admin', 'admin@scamguard.ai', 'admin12345')
    u.first_name = 'Admin'
    u.save()
    print('Superuser created: admin / admin12345')
except Exception as e:
    print(f'Note: {e}')
