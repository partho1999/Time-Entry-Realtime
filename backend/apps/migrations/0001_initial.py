# Generated by Django 5.2.1 on 2025-05-27 11:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('mobile_no', models.CharField(max_length=50)),
                ('gender', models.CharField(max_length=50)),
                ('company', models.CharField(max_length=100)),
                ('id_no', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='PersonImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='person_image/')),
                ('person', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='image', to='apps.person')),
            ],
        ),
    ]
