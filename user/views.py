from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import RegistrationForm, PostForm
from .models import Profile, Photo, Post
from .forms import UserLoginForm
from django.db.models import Q
from django.http import JsonResponse


class RegistrationView(SuccessMessageMixin, CreateView):
    form_class = RegistrationForm
    template_name = 'user/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        profile = Profile.objects.create(user=user)
        profile.countries_interest.set(form.cleaned_data['countries_interest'])
        profile.save()

        return super().form_valid(form)


class UserLoginView(SuccessMessageMixin, LoginView):
    form_class = UserLoginForm
    template_name = 'user/login.html'
    next_page = 'index'


def index(request):
    active_link = 'index'
    if request.user.is_authenticated:

        posts = Post.objects.filter(
            Q(countries__in=request.user.profile.countries_interest.all()) |
            Q(author__in=request.user.profile.followers.all())
        ).distinct().order_by('-create_date')

        for post in posts:
            post.is_following = post.author.profile.followers.filter(id=request.user.id).exists()
    else:
        posts = Post.objects.all().order_by('-create_date')[:10]

    return render(request, "user/index.html", {'posts': posts, 'active_link': active_link})


def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            countries = form.cleaned_data.get('countries')
            if countries:
                post.countries.set(countries)

            tags = form.cleaned_data.get('tags')
            if tags:
                post.tags.set(tags)

            uploaded_images = request.FILES.getlist('photos')
            for image in uploaded_images:
                photo = Photo(image=image)
                photo.save()
                post.photos.add(photo)

            profile = Profile.objects.get(user=request.user)
            profile.post_count += 1
            profile.save()

            return redirect('index')
    else:
        form = PostForm()

    return render(request, 'user/create_post.html', {'form': form})


def increase_rating(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        post.rating += 1
        post.save()
        return JsonResponse({'status': 'ok', 'new_rating': post.rating})


def downgrade_rating(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        if post.rating > 0:
            post.rating -= 1
            post.save()
        return JsonResponse({'status': 'ok', 'new_rating': post.rating})


def toggle_subscription(request, author_id):
    author_profile = get_object_or_404(Profile, user_id=author_id)
    user_profile = get_object_or_404(Profile, user=request.user)

    if author_profile.followers.filter(id=request.user.id).exists():
        author_profile.followers.remove(request.user)  # Удаляем подписку
    else:
        author_profile.followers.add(request.user)  # Добавляем подписку

    author_profile.followers_count = author_profile.followers.count()
    author_profile.save()

    return redirect(request.META.get('HTTP_REFERER'))


def post_detail_view(request, pk):
    post = get_object_or_404(Post, id=pk)

    is_following = False
    if request.user.is_authenticated:
        is_following = post.author.followers.filter(id=request.user.id).exists()

    context = {
        'post': post,
        'is_following': is_following,
        'active_link': 'post_detail',
    }
    return render(request, 'user/post_detail.html', context)


def profiles_list_view(request):
    active_link = 'profiles'
    profiles = Profile.objects.exclude(user__is_superuser=True).select_related('user')

    for profile in profiles:
        profile.unique_country_count = profile.user.posts.values('countries').distinct().count()

    return render(request, 'user/index.html', {'profiles': profiles, 'active_link': active_link})