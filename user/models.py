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

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class Photo(models.Model):
    image = models.ImageField(upload_to='post_photos/', validators=[validate_image_size], verbose_name='Фото')

    def __str__(self):
        return self.image.name

    def get_absolute_url(self):
        return self.image.url

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фотки'


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Тег')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Post(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,  verbose_name='Автор', blank=False, null=True, related_name='posts')
    countries = models.ManyToManyField(Country, blank=False, null=True, verbose_name="Страны")
    subject = models.CharField(max_length=255, blank=False, null=True, verbose_name='Тема')
    body = models.TextField(validators=[MinLengthValidator(3)], blank=False, null=True, verbose_name='Тело поста')
    photos = models.ManyToManyField(Photo, blank=True, verbose_name='Фотографии')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Теги')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        if self.photos.count() > 10:
            self.delete()
            raise ValidationError("Можно прикрепить не более 10 фотографий.")

    def __str__(self):
        return f'{self.author} | {self.subject}'

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Пост')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    body = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Комментарий от {self.author} на {self.post}'

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']


class PostRatingAction(models.Model):
    """
    модель для отслеживания кто оставил голос
    ( ограничение для того чтобы каждый пользователь мог оценить пост только 1 раз )
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Пост')
    action = models.CharField(max_length=10, choices=[('up', 'Upvote'), ('down', 'Downvote')])
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ('user', 'post', 'action')

