from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Profile, Post, Comment


@receiver(pre_save, sender=Post)
def clear_cache_on_rating_change(sender, instance, **kwargs):
    if instance.pk:
        old_post = Post.objects.filter(pk=instance.pk).first()
        if old_post and old_post.rating != instance.rating:
            cache_key = f"user_feed_{old_post.author.id}"
            cache.delete(cache_key)


@receiver(post_save, sender=Post)
def clear_cache_on_post_create(sender, instance, created, **kwargs):
    if created:
        for profile in Profile.objects.all():
            cache_key = f"user_feed_{profile.user.id}"
            cache.delete(cache_key)

        cache.delete('public_feed')
        cache.delete('countries_with_posts')


@receiver(m2m_changed, sender=Profile.countries_interest.through)
def clear_cache_on_country_change(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        cache_key = f"user_feed_{instance.user.id}"
        cache.delete(cache_key)


@receiver(m2m_changed, sender=Profile.followers.through)
def clear_cache_on_followers_change(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        cache_key = f"user_feed_{instance.user.id}"
        cache.delete(cache_key)


@receiver(post_save, sender=Comment)
def clear_cache_on_comment_create(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        for profile in Profile.objects.all():
            cache_key = f"user_feed_{profile.user.id}"
            cache.delete(cache_key)
        cache.delete('public_feed')


@receiver(post_save, sender=User)
def clear_cache_on_user_registration(sender, instance, created, **kwargs):
    if created:
        for profile in Profile.objects.all():
            cache_key = f"user_feed_{profile.user.id}"
            cache.delete(cache_key)

