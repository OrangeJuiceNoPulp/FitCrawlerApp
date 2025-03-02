from django.contrib import admin

from fitness.models import *

# Register your models here.

admin.site.register(Task)
admin.site.register(TaskLog)
admin.site.register(DailyLog)
