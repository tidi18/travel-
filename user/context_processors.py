from .models import Post, Tag, Profile
from django.db.models import Count, Sum


def global_context(request):
    # Получаем последние 3 поста, отсортированные по дате создания
    latest_posts = Post.objects.order_by('-create_date')[:3]

    # Получаем все теги для облака тегов
    tag_cloud = Tag.objects.all()

    # Получаем топ 5 пользователей с количеством постов и их общим рейтингом
    top_users = Profile.objects.annotate(
        posts_count=Count('user__posts'),
        total_rating=Sum('user__posts__rating')  # Суммируем рейтинг постов пользователя
    ).filter(total_rating__gt=0).order_by('-total_rating')[:5]  # Фильтруем пользователей с рейтингом больше 0

    return {
        'latest_posts': latest_posts,
        'tag_cloud': tag_cloud,
        'top_users': top_users,
    }
