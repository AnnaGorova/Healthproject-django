import json
from django.core.management.base import BaseCommand
from diary.models import ICD10Code


class Command(BaseCommand):
    help = 'Завантаження кодів МКХ-10 з JSON-файлу'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Шлях до JSON-файлу')

    def handle(self, *args, **options):
        json_file = options['json_file']

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f"Знайдено {len(data)} записів. Починаємо завантаження...")

        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = ICD10Code.objects.update_or_create(
                code=item['code'],
                defaults={
                    'name': item.get('name', ''),
                    'level': item.get('level', 4),
                    'category_code': item.get('category_code', ''),
                    'category_name': item.get('category_name', ''),
                    'parent_code': item.get('parent_code'),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово! Створено: {created_count}, Оновлено: {updated_count}"
        ))