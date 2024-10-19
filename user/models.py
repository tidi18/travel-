from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from country.models import Country


def validate_image_size(image):
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Размер изображения не может превышать {max_size_mb} МБ.')


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


class Photo(models.Model):
    image = models.ImageField(upload_to='post_photos/', validators=[validate_image_size], verbose_name='Фото')


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Тег')

    def __str__(self):
        return self.name


class Post(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,  verbose_name='Автор', blank=False, null=True)
    countries = models.ManyToManyField(Country, blank=False, null=True, verbose_name="Страны")
    subject = models.CharField(max_length=255, blank=False, null=True, verbose_name='Тема')
    body = models.TextField(validators=[MinLengthValidator(3)], blank=False, null=True, verbose_name='Тело поста')
    photos = models.ManyToManyField(Photo, blank=True, verbose_name='Фотографии')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')

    def __str__(self):
        return f'{self.author} | {self.subject}'

