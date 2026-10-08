import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthproject.settings')
django.setup()

from django.core.management import call_command
from io import StringIO

# Захоплюємо вивід dumpdata в пам'ять
buf = StringIO()
call_command(
    'dumpdata',
    '--natural-foreign',
    '--natural-primary',
    '-e', 'contenttypes',
    '-e', 'auth.Permission',
    '-e', 'admin',
    '-e', 'sessions',
    '--indent', '2',
    stdout=buf,
)

data = json.loads(buf.getvalue())

# Пріоритет моделей
priority = {
    'auth.user': 1,
    'auth.group': 2,
    'diary.userprofile': 10,
    'diary.doctorprofile': 11,
    'diary.icd10code': 12,
    'diary.healthrecord': 20,
    'diary.schedule': 21,
    'diary.appointment': 22,
    'diary.question': 23,
    'diary.questionmessage': 24,
    'diary.medicalconclusion': 25,
}

# Сортуємо з безпечним доступом до 'pk'
data.sort(key=lambda x: (priority.get(x['model'], 99), x.get('pk', 0)))

# Записуємо у файл з UTF-8 без BOM
with open('db.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ db.json перегенеровано з правильним порядком")
print(f"   Всього об'єктів: {len(data)}")