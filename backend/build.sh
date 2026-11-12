#!/usr/bin/env bash
# Build script used by Render (see ../render.yaml). Exit on the first error.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input

# Safety net: if you forgot to commit the migration files, create them now.
# (Best practice is to run "makemigrations" locally and commit the files.)
if ! ls accounts/migrations/0001_*.py >/dev/null 2>&1; then
  echo "No migration files found - generating them now. Commit them to Git later!"
  python manage.py makemigrations
fi

python manage.py migrate --no-input

# Optional demo data (only runs when SEED_DEMO_DATA=true and the database is empty).
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python manage.py seed_data
fi
