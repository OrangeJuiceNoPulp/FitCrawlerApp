# Generated by Django 5.1.6 on 2025-03-02 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dungeon', '0002_armor_boots_staff_sword_gamestats_action_points_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dungeonexploration',
            name='exploration_start',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='milestonelog',
            name='time_completed',
            field=models.DateTimeField(null=True),
        ),
    ]
