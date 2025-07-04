# Generated by Django 5.2.1 on 2025-05-29 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0004_personimage_image_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cam_id', models.CharField(max_length=100, unique=True)),
                ('cam_name', models.CharField(max_length=255)),
                ('cam_password', models.CharField(max_length=255)),
                ('cam_ip', models.GenericIPAddressField()),
                ('cam_position', models.CharField(max_length=255)),
            ],
        ),
    ]
