# Generated by Django 5.1 on 2024-10-16 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='cover_photo',
            field=models.ImageField(blank=True, null=True, upload_to='company_covers/findoutpwa/'),
        ),
        migrations.AlterField(
            model_name='company',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='company_profiles/findoutpwa/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/findoutpwa/'),
        ),
    ]
