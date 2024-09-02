# Generated by Django 5.0.7 on 2024-08-19 05:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0014_lending_cancel_date_lending_return_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='storage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='book.storage', verbose_name='保管場所'),
        ),
    ]
