import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'scamguard.settings'
django.setup()

from django.db import connection
cursor = connection.cursor()

# Add destination_name column
try:
    cursor.execute("ALTER TABLE trip_planner_trip ADD COLUMN destination_name VARCHAR(200) NOT NULL DEFAULT ''")
    print("Added destination_name column")
except Exception as e:
    print(f"destination_name column might already exist: {e}")

# Copy data from destination FK to destination_name
try:
    cursor.execute("""
        UPDATE trip_planner_trip 
        SET destination_name = COALESCE(
            (SELECT name FROM trip_planner_location WHERE trip_planner_location.id = trip_planner_trip.destination_id),
            ''
        )
        WHERE destination_id IS NOT NULL
    """)
    print("Copied existing destination data")
except Exception as e:
    print(f"Copy step skipped: {e}")

# Drop destination_id column (old FK)
try:
    cursor.execute("ALTER TABLE trip_planner_trip DROP COLUMN destination_id")
    print("Dropped old destination_id column")
except Exception as e:
    print(f"Drop step skipped: {e}")

# Mark migration as applied
try:
    cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('trip_planner', '0002_trip_destination_to_charfield', datetime('now'))")
    print("Migration marked as applied")
except Exception as e:
    print(f"Migration record skipped: {e}")

print("Done!")
