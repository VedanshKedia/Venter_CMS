# Generated by Django 2.1.2 on 2019-02-21 06:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Venter', '0013_auto_20190218_1212'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'permissions': (('view_organisation_files', 'Can view organisation files'), ('view_self_files', 'Can view files uploaded by self'), ('delete_organisation_files', 'Can delete organisation files')), 'verbose_name_plural': 'CSV File'},
        ),
    ]
