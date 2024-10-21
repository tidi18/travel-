# Generated by Django 5.1.2 on 2024-10-21 08:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_comment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='photo',
            options={'verbose_name': 'Фото', 'verbose_name_plural': 'Фотки'},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'verbose_name': 'Профиль', 'verbose_name_plural': 'Профили'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'Тег', 'verbose_name_plural': 'Теги'},
        ),
        migrations.CreateModel(
            name='PostRatingAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('up', 'Upvote'), ('down', 'Downvote')], max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.post', verbose_name='Пост')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Оценка',
                'verbose_name_plural': 'Оценки',
                'unique_together': {('user', 'post')},
            },
        ),
    ]
