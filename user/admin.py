from django.contrib import admin
from .models import Profile, Post, Photo, Tag


admin.site.register(Profile)
admin.site.register(Photo)
admin.site.register(Post)
admin.site.register(Tag)
