# No-op migration - kept for migration history consistency
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trip_planner', '0001_initial'),
    ]

    operations = [
        # No operations - destination stays as FK, form handles text input
    ]
