# Generated by Django 5.1.7 on 2025-04-01 02:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dungeon', '0015_alter_dungeonbattle_enemy_health_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dungeonenemy',
            name='defense',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='dungeonenemy',
            name='strength',
            field=models.FloatField(),
        ),
    ]
