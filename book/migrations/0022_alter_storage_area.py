# Generated by Django 5.0.7 on 2024-09-11 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0021_alter_books_isbn'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storage',
            name='area',
            field=models.CharField(max_length=30, null=True, verbose_name='エリア'),
        ),
    ]
