from django.db import models


class Medicine(models.Model):
    name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    purpose = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} {self.dosage} - {self.purpose}"


   