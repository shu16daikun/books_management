# Generated by Django 5.0.7 on 2024-07-25 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0002_alter_storage_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='author',
            field=models.CharField(default='Unknown', max_length=100, verbose_name='著者'),
        ),
    ]
