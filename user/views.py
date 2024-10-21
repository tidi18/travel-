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
from django.http import JsonResponse, HttpResponse
from user.models import Country

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
     предсталение для ленты если пользователь аутентифицирован будут показыны посты
     по интересующим его странам и посты пользователей на которых он подписан
     если нет то будут показаны первые 10 постов
    """

    active_link = 'index'

    is_authenticated_user = request.user.is_authenticated

    if is_authenticated_user:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return redirect('login')

    if is_authenticated_user:
        posts = Post.objects.filter(
            Q(countries__in=profile.countries_interest.all()) |
            Q(author__in=profile.followers.all())
        ).distinct().order_by('-create_date')

        for post in posts:
            post.is_following = post.author.profile.followers.filter(id=request.user.id).exists()
    else:
        posts = Post.objects.all().order_by('-create_date')[:10]

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
    подробная информация поста
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    form = CommentForm()
    post = get_object_or_404(Post, id=pk)

    is_following = False
    if request.user.is_authenticated:
        author_profile = get_object_or_404(Profile, user=post.author)
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
    список пользователей
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profiles'
    profiles = Profile.objects.exclude(user__is_superuser=True).select_related('user')

    for profile in profiles:
        profile.unique_country_count = profile.user.posts.values('countries').distinct().count()

    context = {
        'profiles': profiles,
        'active_link': active_link
    }

    return render(request, 'user/index.html', context)


@login_required
def profile_detail_view(request, user_id):

    """
    подробнее об пользователе
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profile_detail_view'
    profile = get_object_or_404(Profile, user__id=user_id)
    user = profile.user
    posts = profile.user.posts.all()
    unique_country_count = profile.user.posts.values('countries').distinct().count()
    interested_countries = profile.countries_interest.all()

    context = {
        'profile': profile,
        'user': user,
        'posts': posts,
        'active_link': active_link,
        'unique_country_count': unique_country_count,
        'interested_countries': interested_countries
    }

    return render(request, 'user/profile_detail.html', context)


@login_required
def profile_posts(request, user_id):

    """
    посты определенного пользователя
    """
    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'profile_posts'
    profile = get_object_or_404(Profile, user__id=user_id)
    user = profile.user
    posts = profile.user.posts.all()

    context = {
        'profile': profile,
        'user': user,
        'posts': posts,
        'active_link': active_link
    }

    return render(request, 'user/profile_detail.html', context)


@login_required
def posts_by_country_view(request, country_id):

    """
    посты связанные со странной
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'posts_by_country_view'
    country = get_object_or_404(Country, id=country_id)
    posts = Post.objects.filter(countries=country).order_by('-create_date')

    context = {
        'active_link': active_link,
        'country': country,
        'posts': posts,
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
    список комментариев определенного поста
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'post_comments_view'
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()

    context = {
        'post': post,
        'comments': comments,
        'active_link': active_link
    }

    return render(request, 'user/post_detail.html', context)


def tag_view(request, id):

    """
    получение тегов по id
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    tag = get_object_or_404(Tag, id=id)
    posts = Post.objects.filter(tags=tag).order_by('-create_date')

    context = {
        'posts': posts,
        'tag': tag,
    }
    return render(request, 'user/tag_view.html', context)