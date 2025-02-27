# Generated by Django 5.1 on 2024-10-18 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0007_category_category_type_alter_company_cover_photo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Categoría de empresa',
                'verbose_name_plural': 'Categorías de empresas',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=3, unique=True)),
            ],
            options={
                'verbose_name': 'País',
                'verbose_name_plural': 'Países',
            },
        ),
        migrations.AddField(
            model_name='company',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='companies', to='marketplace.companycategory', verbose_name='Categoría'),
        ),
        migrations.AddField(
            model_name='company',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='companies', to='marketplace.country', verbose_name='País'),
        ),
    ]
