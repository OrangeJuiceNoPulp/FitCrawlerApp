# Generated by Django 5.1.7 on 2025-04-01 03:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0008_alter_exercise_video_link'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ExerciseVideo',
        ),
    ]
