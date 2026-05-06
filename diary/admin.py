from django.contrib import admin
from diary.models import UserProfile, Medicine, HealthRecord
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(Medicine)
admin.site.register(HealthRecord)


