# Generated by Django 5.1.6 on 2025-02-20 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0007_alter_exercise_video_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='video_link',
            field=models.URLField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
