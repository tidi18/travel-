from django.shortcuts import render, get_object_or_404, redirect
from user.models import Profile
from .models import Country


def country_list_view(request):
    active_link = 'countries'
    countries_with_posts = Country.objects.filter(post__isnull=False).distinct()

    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)
        user_countries_interest = profile.countries_interest.values_list('id', flat=True)
    else:
        user_countries_interest = []

    context = {
        'active_link': active_link,
        'countries': countries_with_posts,
        'user_countries_interest': user_countries_interest,
    }
    return render(request, 'user/index.html', context)


def toggle_country_interest(request, country_id):
    country = get_object_or_404(Country, id=country_id)
    profile = get_object_or_404(Profile, user=request.user)

    if country in profile.countries_interest.all():
        profile.countries_interest.remove(country)
    else:
        profile.countries_interest.add(country)

    return redirect(request.META.get('HTTP_REFERER'))


def country_detail_view(request, country_id):
    active_link = 'country_detail_view'
    country = get_object_or_404(Country, id=country_id)

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

