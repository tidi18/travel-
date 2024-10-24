from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import RegistrationForm, PostForm, CommentForm
from .models import Profile, Photo, Post, Tag, PostRatingAction
from .forms import UserLoginForm
from django.db.models import Q
from django.http import JsonResponse
from user.models import Country
from django.core.paginator import Paginator
from .permissions import check_user_blocked, check_user_can_create


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


def logout_view(request):
    logout(request)
    return redirect('index')


def index(request):
    """
    Представление для ленты. Если пользователь аутентифицирован, показываются посты
    по интересующим его странам и посты пользователей, на которых он подписан.
    Если нет, то будут показаны первые 10 постов.
    """

    active_link = 'index'
    is_authenticated_user = request.user.is_authenticated

    if is_authenticated_user:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return redirect('login')

        cache_key = f"user_feed_{request.user.id}"
        posts = cache.get(cache_key)

        if not posts:
            posts = Post.objects.filter(
                Q(countries__in=profile.countries_interest.all()) |
                Q(author__in=profile.followers.all())
            ).order_by('-last_lifted_at')

            cache.set(cache_key, posts, timeout=60*5)

        for post in posts:
            post.is_following = post.author.profile.followers.filter(id=request.user.id).exists()

        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'posts': page_obj,
            'active_link': active_link,
            'is_authenticated_user': is_authenticated_user
        }

        return render(request, "user/index.html", context)
    else:

        cache_key = 'public_feed'
        posts = cache.get(cache_key)

        if not posts:
            posts = Post.objects.all().order_by('-create_date')[:10]

            cache.set(cache_key, posts, timeout=60*5)

        context = {
            'posts': posts,
            'active_link': active_link,
            'is_authenticated_user': is_authenticated_user
        }
        return render(request, "user/index.html", context)


@login_required
def create_post(request):
    """
    представление создания поста
    посты могут создать только те пользователи у которых is_create = True
    по дефолту значение сохраняется как True
    возможность загрузить сразу до 10 фотографий в пределах 5мб
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    create_permission_response = check_user_can_create(profile)
    if create_permission_response:
        return create_permission_response

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
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

            uploaded_images = form.cleaned_data.get('photos')

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


@login_required
def increase_rating(request, post_id):
    """
    Предназначенно для увеличения рейтинга поста.
    """
    profile = Profile.objects.get(user=request.user)
    post = get_object_or_404(Post, id=post_id)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    rating_action, created = PostRatingAction.objects.get_or_create(user=request.user, post=post)

    if rating_action.action == 'up':
        return JsonResponse({'status': 'ok', 'new_rating': post.rating})

    if request.method == 'POST':
        if rating_action.action == 'down':

            post.rating += 1
        else:
            post.rating += 1

        post.save()

        rating_action.action = 'up'
        rating_action.save()

        cache_keys = [
            f"user_feed_{request.user.id}",
            f"profile_{request.user.id}",
            f"profile_{post.author.id}"
            f"post_{post_id}",
            f"user_posts_{request.user.id}"
        ]

        for country in post.countries.all():
            cache_keys.append(f"posts_by_country_{country.id}")

        for tag in post.tags.all():
            cache_keys.append(f"tag_posts_{tag.id}")

        for cache_key in cache_keys:
            cache.delete(cache_key)
            print(f"Cache cleared for key: {cache_key}")

        return JsonResponse({'status': 'ok', 'new_rating': post.rating})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def downgrade_rating(request, post_id):
    """
    Предназначенно для уменьшения рейтинка поста.
    """
    profile = Profile.objects.get(user=request.user)
    post = get_object_or_404(Post, id=post_id)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    rating_action, created = PostRatingAction.objects.get_or_create(user=request.user, post=post)

    if rating_action.action == 'down':
        return JsonResponse({'status': 'ok', 'new_rating': post.rating})

    if request.method == 'POST':
        if post.rating > 0:
            if rating_action.action == 'up':

                post.rating -= 1
            else:
                post.rating -= 1

            post.save()

            rating_action.action = 'down'
            rating_action.save()

            cache_keys = [
                f"user_feed_{request.user.id}",
                f"profile_{request.user.id}",
                f"profile_{post.author.id}",
                f"user_posts_{request.user.id}"
                f"post_{post_id}",
            ]

            for country in post.countries.all():
                cache_keys.append(f"posts_by_country_{country.id}")

            for tag in post.tags.all():
                cache_keys.append(f"tag_posts_{tag.id}")

            for cache_key in cache_keys:
                cache.delete(cache_key)
                print(f"Cache cleared for key: {cache_key}")

        return JsonResponse({'status': 'ok', 'new_rating': post.rating})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def toggle_subscription(request, author_id):

    """
    подписка на пользователя
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    author_profile = get_object_or_404(Profile, user_id=author_id)
    user_profile = get_object_or_404(Profile, user=request.user)

    if author_profile.followers.filter(id=request.user.id).exists():
        author_profile.followers.remove(request.user)
    else:
        author_profile.followers.add(request.user)

    author_profile.followers_count = author_profile.followers.count()
    author_profile.save()

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
def post_detail_view(request, pk):
    """
    Подробная информация поста
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    form = CommentForm()

    cache_key_post = f"post_{pk}"
    post = cache.get(cache_key_post)
    if not post:
        post = get_object_or_404(Post, id=pk)
        cache.set(cache_key_post, post, timeout=60*5)

    is_following = False
    if request.user.is_authenticated:
        cache_key_author_profile = f"profile_{post.author.id}"
        author_profile = cache.get(cache_key_author_profile)
        if not author_profile:
            author_profile = get_object_or_404(Profile, user=post.author)
            cache.set(cache_key_author_profile, author_profile, timeout=60*5)

        is_following = author_profile.followers.filter(id=request.user.id).exists()

    context = {
        'form': form,
        'post': post,
        'is_following': is_following,
        'active_link': 'post_detail',
    }

    return render(request, 'user/post_detail.html', context)


@login_required
def profiles_list_view(request):
    """
    Список пользователей
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profiles'

    cache_key_profiles = "profiles_list"
    profiles = cache.get(cache_key_profiles)
    if not profiles:
        profiles = Profile.objects.exclude(user__is_superuser=True).select_related('user')
        cache.set(cache_key_profiles, profiles, timeout=60*5)

    for profile in profiles:
        profile.unique_country_count = profile.user.posts.values('countries').distinct().count()

    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profiles': page_obj,
        'active_link': active_link
    }

    return render(request, 'user/index.html', context)


@login_required
def profile_detail_view(request, user_id):
    """
    Подробная информация о пользователе
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profile_detail_view'

    cache_key_user_profile = f"profile_detail_{user_id}"
    profile = cache.get(cache_key_user_profile)
    if not profile:
        profile = get_object_or_404(Profile, user__id=user_id)
        cache.set(cache_key_user_profile, profile, timeout=60*5)

    user = profile.user

    cache_key_posts = f"user_posts_{user_id}"
    posts = cache.get(cache_key_posts)
    if not posts:
        posts = profile.user.posts.all().order_by('-create_date')
        cache.set(cache_key_posts, posts, timeout=60*10)

    cache_key_unique_country_count = f"unique_country_count_{user_id}"
    unique_country_count = cache.get(cache_key_unique_country_count)
    if unique_country_count is None:
        unique_country_count = profile.user.posts.values('countries').distinct().count()
        cache.set(cache_key_unique_country_count, unique_country_count, timeout=60*5)

    cache_key_interested_countries = f"interested_countries_{user_id}"
    interested_countries = cache.get(cache_key_interested_countries)
    if not interested_countries:
        interested_countries = profile.countries_interest.all()
        cache.set(cache_key_interested_countries, interested_countries, timeout=60*5)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'user': user,
        'posts': page_obj,
        'active_link': active_link,
        'unique_country_count': unique_country_count,
        'interested_countries': interested_countries
    }

    return render(request, 'user/profile_detail.html', context)


@login_required
def profile_posts(request, user_id):
    """
    Посты определенного пользователя
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profile_posts'

    cache_key_user_profile = f"profile_detail_{user_id}"
    profile = cache.get(cache_key_user_profile)
    if not profile:
        profile = get_object_or_404(Profile, user__id=user_id)
        cache.set(cache_key_user_profile, profile, timeout=60*5)

    user = profile.user

    cache_key_posts = f"user_posts_{user_id}"
    posts = cache.get(cache_key_posts)
    if not posts:
        posts = profile.user.posts.all().order_by('-create_date')
        cache.set(cache_key_posts, posts, timeout=60*5)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'user': user,
        'posts': page_obj,
        'active_link': active_link
    }

    return render(request, 'user/profile_detail.html', context)


@login_required
def posts_by_country_view(request, country_id):
    """
    Посты, связанные со страной
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'posts_by_country_view'

    cache_key_country = f"country_{country_id}"
    country = cache.get(cache_key_country)
    if not country:
        country = get_object_or_404(Country, id=country_id)
        cache.set(cache_key_country, country, timeout=60*5)

    cache_key_posts = f"posts_by_country_{country_id}"
    posts = cache.get(cache_key_posts)
    if not posts:
        posts = Post.objects.filter(countries=country).order_by('-create_date')
        cache.set(cache_key_posts, posts, timeout=60*5)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_link': active_link,
        'country': country,
        'posts': page_obj,
    }

    return render(request, 'country/country_detail.html', context)


@login_required
def add_comment(request, post_id):

    """
    форма комментариев
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', pk=post.id)

    else:
        form = CommentForm()

    return render(request, 'user/post_detail.html', {'form': form, 'post': post})


@login_required
def post_comments_view(request, post_id):
    """
    Список комментариев определенного поста
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'post_comments_view'

    cache_key_post = f"post_{post_id}"
    post = cache.get(cache_key_post)
    if not post:
        post = get_object_or_404(Post, id=post_id)
        cache.set(cache_key_post, post, timeout=60*5)

    cache_key_comments = f"post_comments_{post_id}"
    comments = cache.get(cache_key_comments)
    if not comments:
        comments = post.comments.all().order_by('created_at')
        cache.set(cache_key_comments, comments, timeout=60*5)

    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'post': post,
        'comments': page_obj,
        'active_link': active_link
    }

    return render(request, 'user/post_detail.html', context)


@login_required
def tag_view(request, id):
    """
    Получение тегов по id
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*10)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    cache_key_tag = f"tag_{id}"
    tag = cache.get(cache_key_tag)
    if not tag:
        tag = get_object_or_404(Tag, id=id)
        cache.set(cache_key_tag, tag, timeout=60*5)

    cache_key_posts = f"tag_posts_{id}"
    posts = cache.get(cache_key_posts)
    if not posts:
        posts = Post.objects.filter(tags=tag).order_by('-create_date')
        cache.set(cache_key_posts, posts, timeout=60*5)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': page_obj,
        'tag': tag,
    }
    return render(request, 'user/posts_by_tag.html', context)


@login_required
def posts_by_tag_view(request, tag_id):
    """
    Список постов по тегу
    """

    cache_key_profile = f"profile_{request.user.id}"
    profile = cache.get(cache_key_profile)
    if not profile:
        profile = Profile.objects.get(user=request.user)
        cache.set(cache_key_profile, profile, timeout=60*5)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    cache_key_tag = f"tag_{tag_id}"
    tag = cache.get(cache_key_tag)
    if not tag:
        tag = get_object_or_404(Tag, id=tag_id)
        cache.set(cache_key_tag, tag, timeout=60*5)

    cache_key_posts = f"tag_posts_{tag_id}"
    posts = cache.get(cache_key_posts)
    if not posts:
        posts = Post.objects.filter(tags=tag).order_by('-create_date')
        cache.set(cache_key_posts, posts, timeout=60*5)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tag': tag,
        'posts': page_obj,
    }
    return render(request, 'user/posts_by_tag.html', context)