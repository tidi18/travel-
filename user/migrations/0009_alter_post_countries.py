# Generated by Django 5.1.2 on 2024-10-22 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0002_alter_country_options'),
        ('user', '0008_post_last_lifted_at_autopostlift_postliftlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='countries',
            field=models.ManyToManyField(to='country.country', verbose_name='Страны'),
        ),
    ]