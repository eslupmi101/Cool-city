# Generated by Django 2.2.16 on 2023-03-30 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20230329_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Загрузить изображение', upload_to='posts/', verbose_name='Изображение'),
        ),
    ]
