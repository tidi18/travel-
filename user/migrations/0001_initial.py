# Generated by Django 5.1.2 on 2024-10-18 10:04

import django.core.validators
import django.db.models.deletion
import user.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('country', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='post_photos/', validators=[user.models.validate_image_size], verbose_name='Фото')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Тег')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_count', models.IntegerField(default=0, verbose_name='Количество постов')),
                ('followers_count', models.IntegerField(default=0, verbose_name='Количество подписчиков')),
                ('is_create', models.BooleanField(default=True, verbose_name='Создавать посты')),
                ('is_blocked', models.BooleanField(default=False, verbose_name='Заблокирован')),
                ('countries_interest', models.ManyToManyField(blank=True, to='country.country', verbose_name='Интересующие страны')),
                ('followers', models.ManyToManyField(blank=True, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Подписчики')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255, null=True, verbose_name='Тема')),
                ('body', models.TextField(null=True, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='Тело поста')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('countries', models.ManyToManyField(null=True, to='country.country', verbose_name='Страны')),
                ('photos', models.ManyToManyField(blank=True, to='user.photo', verbose_name='Фотографии')),
                ('tags', models.ManyToManyField(blank=True, to='user.tag', verbose_name='Теги')),
            ],
        ),
    ]
