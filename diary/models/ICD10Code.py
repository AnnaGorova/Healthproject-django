from django.db import models

class ICD10Code(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.TextField()
    level = models.PositiveSmallIntegerField(default=4)
    category_code = models.CharField(max_length=10, blank=True)
    category_name = models.TextField(blank=True)
    parent_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Код МКХ-10'
        verbose_name_plural = 'Коди МКХ-10'

    def __str__(self):
        return f"{self.code} — {self.name}"