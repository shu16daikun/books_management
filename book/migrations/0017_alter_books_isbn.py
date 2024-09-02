# Generated by Django 5.0.7 on 2024-08-28 02:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0016_storage_unique_floor_area'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='isbn',
            field=models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(message='ISBNは13桁の数字である必要があります。', regex='^\\d{13}$')], verbose_name='ISBN'),
        ),
    ]
