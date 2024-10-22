from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from user.models import Profile
from .models import Country
from user.permissions import check_user_blocked
from django.core.cache import cache


@login_required
def country_list_view(request):
    """
    Список стран, связанных с постами
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'countries'

    cache_key_countries = "countries_with_posts"
    countries_with_posts = cache.get(cache_key_countries)
    if not countries_with_posts:
        countries_with_posts = Country.objects.filter(post__isnull=False).distinct().order_by('name')
        cache.set(cache_key_countries, countries_with_posts, timeout=60*10)

    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        user_countries_interest = profile.countries_interest.values_list('id', flat=True)
    else:
        user_countries_interest = []

    paginator = Paginator(countries_with_posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_link': active_link,
        'countries': page_obj,
        'user_countries_interest': user_countries_interest,
    }

    return render(request, 'user/index.html', context)


@login_required
def toggle_country_interest(request, country_id):
    """
    Подписка на страну
    """
    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    country = get_object_or_404(Country, id=country_id)

    if country in profile.countries_interest.all():
        profile.countries_interest.remove(country)
    else:
        profile.countries_interest.add(country)

    return JsonResponse({'status': 'ok', 'message': 'Subscription toggled successfully.'}, status=200)


@login_required
def country_detail_view(request, country_id):
    """
    Подробная информация о стране
    """

    profile = Profile.objects.get(user=request.user)

    blocked_response = check_user_blocked(profile)
    if blocked_response:
        return blocked_response

    active_link = 'country_detail_view'

    cache_key_country = f"country_detail_{country_id}"
    country = cache.get(cache_key_country)

    if not country:
        country = get_object_or_404(Country, id=country_id)
        cache.set(cache_key_country, country, timeout=60 * 10)

    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        user_countries_interest = profile.countries_interest.values_list('id', flat=True)
    else:
        user_countries_interest = []

    context = {
        'active_link': active_link,
        'country': country,
        'user_countries_interest': user_countries_interest,
    }
    return render(request, 'country/country_detail.html', context)

