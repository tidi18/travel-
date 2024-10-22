from django.test import TestCase
from django.urls import reverse
from user.models import Profile, User, Post
from django.apps import apps
from country.models import Country


class CountryListViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.country1 = Country.objects.create(
            name='test2 country',
            top_level_domain='test top_level_domain',
            alpha2_code='test2 alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.country2 = Country.objects.create(
            name='test2 count1ry',
            top_level_domain='test top_level_domain',
            alpha2_code='test2 alpha2_code',
            alpha3_code='test aqlpha32_code2',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post1 = Post.objects.create(author=self.user, subject='Post by user')
        self.post1.countries.set([self.country1])

        self.post2 = Post.objects.create(author=self.user, subject='Another post by user')
        self.post2.countries.set([self.country2])

        self.profile.countries_interest.add(self.country1)

        self.url = reverse('country_list_view')

    def tearDown(self):
        """Очистка после каждого теста."""
        all_models = apps.get_models()
        for model in all_models:
            model.objects.all().delete()

    def test_country_list_view_authenticated_user(self):
        """вывод списка для аутентифицированных пользователей"""

        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/index.html')

        countries = response.context['countries']
        self.assertIn(self.country1, countries)
        self.assertIn(self.country2, countries)
        self.assertEqual(list(response.context['user_countries_interest']), [self.country1.id])

    def test_country_list_view_unauthenticated_user(self):
        """перенаправление"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')


class ToggleCountryInterestTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.country2 = Country.objects.create(
            name='test2 country',
            top_level_domain='test top_level_domain',
            alpha2_code='test2 alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.url = reverse('toggle_country_interest', args=[self.country2.id])

    def test_login_required(self):
        """Перенаправление, если пользователь не аутентифицирован"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_toggle_country_interest_add(self):
        """Подписка на страну"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.countries_interest.filter(id=self.country2.id).exists())

    def test_toggle_country_interest_remove(self):
        """Отписка от страны"""
        self.profile.countries_interest.add(self.country2)

        self.client.login(username='testuser', password='testpassword')  # Убедитесь, что пользователь аутентифицирован

        response = self.client.post(self.url)

        self.profile.refresh_from_db()
        self.assertFalse(self.profile.countries_interest.filter(id=self.country2.id).exists())
        self.assertEqual(response.status_code, 200)


class CountryDetailViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)
        self.country = Country.objects.create(
            name='test2 country',
            top_level_domain='test top_level_domain',
            alpha2_code='test2 alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )
        self.url = reverse('country_detail', args=[self.country.id])

    def test_login_required(self):
        """Проверка перенаправления для неаутентифицированных пользователей"""

        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_view_country_detail_authenticated(self):
        """Проверка отображения деталей страны для аутентифицированного пользователя"""

        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test2 country')
        self.assertContains(response, 'test capital')

    def test_user_countries_interest(self):
        """Проверка списка стран, представляющих интерес для пользователя"""

        self.profile.countries_interest.add(self.country)

        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        user_countries_interest = list(response.context['user_countries_interest'])
        self.assertIn(self.country.id, user_countries_interest)
