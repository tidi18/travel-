from django.contrib import admin
from .models import Profile, Post, Photo, Tag, Comment, PostRatingAction, AutoPostLift, PostLiftLog


admin.site.register(Profile)
admin.site.register(Photo)
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(PostRatingAction)
admin.site.register(AutoPostLift)
admin.site.register(PostLiftLog)

