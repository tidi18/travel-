from django.contrib import admin
from .models import Profile, Post, Photo, Tag, Comment


admin.site.register(Profile)
admin.site.register(Photo)
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Comment)
