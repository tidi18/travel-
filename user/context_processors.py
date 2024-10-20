from .models import Post, Tag, Profile
from django.db.models import Count, Sum


def global_context(request):
    latest_posts = Post.objects.order_by('-create_date')[:3]

    tag_cloud = Tag.objects.all()

    top_users = Profile.objects.annotate(
        posts_count=Count('user__posts'),
        total_rating=Sum('user__posts__rating')
    ).filter(total_rating__gt=0).order_by('-total_rating')[:5]

    return {
        'latest_posts': latest_posts,
        'tag_cloud': tag_cloud,
        'top_users': top_users,
    }
