# Generated by Django 5.1.6 on 2025-02-07 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gym', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fitcrawleruser',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]
