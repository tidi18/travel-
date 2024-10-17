import requests
from decouple import config
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from .models import Country
from django.urls import path


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'capital', 'calling_code')

    def update_db(self, request):
        url = 'https://api.countrylayer.com/v2/all'
        api_key = config('APIKEY')
        col = 0

        params = {
            'access_key': api_key
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            countries = response.json()
            for country in countries:
                models_country, created = Country.objects.get_or_create(
                    name=country['name'],
                    top_level_domain=country['topLevelDomain'],
                    alpha2_code=country['alpha2Code'],
                    alpha3_code=country['alpha3Code'],
                    calling_code=country['callingCodes'],
                    capital=country['capital'],
                    alt_spellings=country['altSpellings'],
                    region=country['region']
                )
                if created:
                    col += 1

            if col > 0:
                messages.success(request, f"Новые страны добавлены в базу данных ({col}).")

            else:
                messages.info(request, "Новых данных не обнаружено")

        else:
            messages.info(request, "Функция временно недоступно")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin'))

    def get_urls(self):
        urls = super().get_urls()
        custom_url = [path("update_db/", self.admin_site.admin_view(self.update_db), name='update_db')]
        return custom_url + urls


admin.site.register(Country, CountryAdmin)
