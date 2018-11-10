# Generated by Django 2.1.2 on 2018-10-22 01:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('redirects', '0001_initial_patched'),
    ]

    operations = [
        migrations.AlterField(
            model_name='redirect',
            name='old_path',
            field=models.CharField(db_index=True, help_text="This should be an absolute path, excluding the domain name. Example: '/events/search/'.", max_length=200, verbose_name='redirect from'),
        ),
        migrations.AlterField(
            model_name='redirect',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.Site', verbose_name='site'),
        ),
    ]
