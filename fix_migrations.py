import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scamguard.settings')
django.setup()

print("Making migrations...")
call_command('makemigrations', 'trip_planner', interactive=False)
print("Migrating...")
call_command('migrate', 'trip_planner', interactive=False)
print("Done!")
