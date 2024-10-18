from django.contrib.auth.models import User
from django.db import models
from country.models import Country


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    countries_interest = models.ManyToManyField(Country, blank=True, verbose_name="Интересующие страны")
    post_count = models.IntegerField(default=0, verbose_name='Количество постов')
    followers = models.ManyToManyField(User, related_name='following', blank=True, verbose_name='Подписчики')
    followers_count = models.IntegerField(default=0, verbose_name='Количество подписчиков')
    is_create = models.BooleanField(default=True, verbose_name='Создавать посты')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')

    def __str__(self):
        return f'{self.user}'


class Post(models.Model):
    pass