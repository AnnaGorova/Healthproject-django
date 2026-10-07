import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthproject.settings')
django.setup()

import ftfy
from django.apps import apps
from django.db import models


def fix_string(s):
    if not isinstance(s, str) or not s:
        return s
    # Якщо в рядку немає нічого, крім ASCII — не чіпаємо
    if not any(ord(c) > 127 for c in s):
        return s
    # ftfy сам визначає, чи потрібне виправлення
    fixed = ftfy.fix_text(s)
    return fixed


def fix_model(model):
    text_fields = []
    for field in model._meta.get_fields():
        if isinstance(field, (models.CharField, models.TextField, models.EmailField)):
            text_fields.append(field.name)
    if not text_fields:
        return 0
    fixed_count = 0
    for obj in model.objects.all():
        changed = False
        for field_name in text_fields:
            value = getattr(obj, field_name, None)
            if isinstance(value, str):
                fixed = fix_string(value)
                if fixed != value:
                    setattr(obj, field_name, fixed)
                    changed = True
        if changed:
            obj.save()
            fixed_count += 1
    return fixed_count


def main():
    total = 0
    for model in apps.get_models():
        if model._meta.app_label in ('admin', 'contenttypes', 'sessions'):
            continue
        count = fix_model(model)
        if count:
            print(f"OK {model._meta.label}: fixed {count} objects")
            total += count
    print(f"\nTotal fixed: {total}")


if __name__ == '__main__':
    main()