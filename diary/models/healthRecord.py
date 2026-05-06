from django.db import models
from .user_profile import UserProfile


class HealthRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='records')
    date = models.DateTimeField(auto_now_add=True)
    well_being = models.CharField(max_length=50, blank=True)
    temperature = models.FloatField(default=36.6)
    pressure = models.CharField(max_length=20, blank=True)
    complaints = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    medicines = models.ManyToManyField('Medicine', blank=True, related_name='records')


    def __str__(self):
        medicines_str = ", ".join(str(m) for m in self.medicines.all())

        date_str = self.date.strftime("%d-%m-%Y %H:%M:%S")

        return (f"{date_str}: {self.user.username}  \n"
                f"    Cамопочуття: {self.well_being};\n"
                f"    Температура: {self.temperature}°C;\n"
                f"    Артеріальний тиск: {self.pressure}мм.рт.ст; \n"
                f"    Симптоми: {self.complaints};\n"
                f"    Коментар: {self.comment};\n"
                f"    \nЛіки: {medicines_str}")





