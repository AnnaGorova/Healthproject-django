import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthproject.settings')
django.setup()

from django.core.management import call_command

# Перенаправляємо stdout у файл з utf-8
with open('db.json', 'w', encoding='utf-8') as f:
    original_stdout = sys.stdout
    sys.stdout = f
    try:
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '-e', 'contenttypes',
            '-e', 'auth.Permission',
            '-e', 'admin',
            '-e', 'sessions',
            '--indent', '2',
        )
    finally:
        sys.stdout = original_stdout

print("✅ Готово! db.json збережено у utf-8")
