# Generated by Django 5.1.7 on 2025-03-25 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dungeon', '0012_alter_dungeon_boss_monster_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dungeon',
            name='difficulty_quantifer',
            field=models.FloatField(default=5),
        ),
    ]
