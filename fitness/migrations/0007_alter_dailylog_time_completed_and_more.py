# Generated by Django 5.1.6 on 2025-03-02 02:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0006_alter_dailylog_time_completed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailylog',
            name='time_completed',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 1, 21, 27, 48, 91109)),
        ),
        migrations.AlterField(
            model_name='tasklog',
            name='time_completed',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 1, 21, 27, 48, 91109)),
        ),
    ]
