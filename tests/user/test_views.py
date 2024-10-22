import io
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from user.models import Profile, Post, PostRatingAction, Comment, Tag
from country.models import Country
import os
from django.conf import settings


class RegistrationViewTestCase(TestCase):

    def setUp(self):
        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
                                               )

    def tearDown(self):
        """Очистка после каждого теста."""
        all_models = apps.get_models()
        for model in all_models:
            model.objects.all().delete()

    def test_registration_201(self):
        """Тестирование процесса регистрации пользователя"""
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': [self.country1.id]
        }

        response = self.client.post(reverse('register'), data)
        print("Пользователи:", User.objects.all())
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.first()
        self.assertEqual(user.username, 'testuser')

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.countries_interest.count(), 1)

        self.assertRedirects(response, reverse('login'))

    def test_passwords_dont_match(self):
        """Пароли не совпадают"""

        data = {
            'username': 'testuser',
            'password': 'tlsjldslj',  # Пароль
            'confirm_password': 'testpassword',  # Несоответствующий пароль
            'countries_interest': [self.country1.id]
        }

        response = self.client.post(reverse('register'), data)
        self.assertEqual(User.objects.count(), 0)

        form = response.context['form']
        print(form.errors)

        self.assertFalse(form.is_valid())

        self.assertIn('confirm_password', form.errors)

        self.assertEqual(form.errors['confirm_password'], ["Пароли не совпадают."])

        self.assertTemplateUsed(response, 'user/register.html')

    def test_username_already_exists(self):
        """username уже существует"""

        data1 = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': [self.country1.id]
        }

        response1 = self.client.post(reverse('register'), data1)

        data2 = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': [self.country1.id]
        }

        response2 = self.client.post(reverse('register'), data2)
        self.assertEqual(User.objects.count(), 1)

        form = response2.context['form']
        print(form.errors)

        self.assertFalse(form.is_valid())

        self.assertIn('username', form.errors)

        self.assertEqual(form.errors['username'], ["Пользователь с таким именем уже существует."])

        self.assertTemplateUsed(response2, 'user/register.html')

    def test_fields_are_not_filled_in(self):
        """не заполнены поля"""

        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': []
        }

        response = self.client.post(reverse('register'), data)

        self.assertEqual(User.objects.count(), 0)

        form = response.context['form']
        print(form.errors)

        self.assertFalse(form.is_valid())

        self.assertIn('countries_interest', form.errors)

        self.assertEqual(form.errors['countries_interest'], ["Обязательное поле."])

        self.assertTemplateUsed(response, 'user/register.html')


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
                                               )

    def tearDown(self):
        """Очистка после каждого теста."""
        all_models = apps.get_models()
        for model in all_models:
            model.objects.all().delete()

    def test_login_200(self):
        """успешный процесс аутентификации"""

        register_data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': [self.country1.id]
        }

        register_response = self.client.post(reverse('register'), register_data)
        self.assertEqual(User.objects.count(), 1)

        login_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }

        login_response = self.client.post(reverse('login'), login_data)

        self.assertEqual(login_response.status_code, 302)
        self.assertRedirects(login_response, reverse('index'))

        user = self.client.session.get('_auth_user_id')
        self.assertIsNotNone(user)
        self.assertEqual(int(user), User.objects.get(username='testuser').id)

    def test_wrong_username_or_password(self):
        """неверный логин или пароль"""

        register_data = {
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'countries_interest': [self.country1.id]
        }

        register_response = self.client.post(reverse('register'), register_data)
        self.assertEqual(User.objects.count(), 1)

        login_data = {
            'username': 'testuse',
            'password': 'testpasword'
        }

        login_response = self.client.post(reverse('login'), login_data)

        form = login_response.context['form']
        print(form.errors)

        self.assertIn('__all__', form.errors)

        self.assertEqual(form.errors['__all__'], ["Неверный логин или пароль."])

        self.assertTemplateUsed(login_response, 'user/login.html')


class IndexViewTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

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

        self.profile.countries_interest.add(self.country1, self.country2)

        self.post1 = Post.objects.create(author=self.user, subject='Post by user')
        self.post1.countries.set([self.country1])

        self.post2 = Post.objects.create(author=self.user, subject='Another post by user')
        self.post2.countries.set([self.country2])

    def tearDown(self):
        """Очистка после каждого теста."""

        all_models = apps.get_models()
        for model in all_models:
            model.objects.all().delete()

    def test_index_view_authenticated_user(self):
        """Тестирование представления index для аутентифицированного пользователя."""

        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)

        self.assertIn('posts', response.context)

    def test_index_view_unauthenticated_user(self):
        """Тестирование представления index для неаутентифицированного пользователя."""

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.context)

    def test_index_view_redirects_to_login_if_profile_does_not_exist(self):
        """Тестирование редиректа на страницу логина, если профиль не существует."""

        self.client.login(username='testuser', password='testpassword')
        Profile.objects.filter(user=self.user).delete()

        response = self.client.get(reverse('index'))

        self.assertRedirects(response, reverse('login'))


def generate_large_test_file(size_in_mb=6, filename='large_test_image.jpg'):
    """Генерация файла размером size_in_mb в памяти"""
    large_file = io.BytesIO(b'a' * size_in_mb * 1024 * 1024)  # создаем файл размером size_in_mb мегабайт
    large_file.name = filename  # Устанавливаем имя файла
    return large_file


class CreatePostViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.profile = Profile.objects.create(user=self.user, is_create=True, post_count=0)
        self.client.login(username='testuser', password='password123')

        self.test_image_path = os.path.join(settings.BASE_DIR, 'tests', 'user', 'test_img.jpg')
        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

    def tearDown(self):
        """Очистка после каждого теста."""
        all_models = apps.get_models()
        for model in all_models:
            model.objects.all().delete()

    def test_create_post_201(self):
        """флома создания поста"""

        data = {
            'countries': [self.country1.id],
            'tags': [],
            'subject': 'test subject',
            'body': 'test body',
            'photos': [open(self.test_image_path, 'rb'),]
        }

        response = self.client.post(reverse('create_post'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

    def test_is_create_false(self):
        """админ запретил создавать посты"""

        self.user2 = User.objects.create_user(username='testuser2', password='password1232')
        self.profile2 = Profile.objects.create(user=self.user2, is_create=False, post_count=1)
        self.client.login(username='testuser2', password='password1232')

        data = {
            'countries': [self.country1.id],
            'tags': [],
            'subject': 'test subject',
            'body': 'test body',
            'photos': [open(self.test_image_path, 'rb'), ]
        }

        response = self.client.post(reverse('create_post'), data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Post.objects.count(), 0)

    def test_field_is_not_filled_in(self):
        """флома создания поста"""

        data = {
            'countries': [],
            'tags': [],
            'subject': '',
            'body': '',
            'photos': [open(self.test_image_path, 'rb'),]
        }

        response = self.client.post(reverse('create_post'), data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        print(form.errors)

        self.assertIn('countries', form.errors)
        self.assertIn('subject', form.errors)
        self.assertIn('body', form.errors)

        self.assertEqual(form.errors['countries'], ["Обязательное поле."])
        self.assertEqual(form.errors['subject'], ["Обязательное поле."])
        self.assertEqual(form.errors['body'], ["Обязательное поле."])
        self.assertEqual(Post.objects.count(), 0)

    def test_upload_10_photos_at_once(self):
        """можно загрузить 10 сразу"""

        data = {
            'countries': [self.country1.id],
            'tags': [],
            'subject': 'test subject',
            'body': 'test body',
            'photos': [open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'),]
        }

        response = self.client.post(reverse('create_post'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))

    def test_upload_up_to_10_photos_at_once(self):
        """можно загрузить до 10 сразу"""

        data = {
            'countries': [self.country1.id],
            'tags': [],
            'subject': 'test subject',
            'body': 'test body',
            'photos': [open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb'),
                       open(self.test_image_path, 'rb'), open(self.test_image_path, 'rb')]
        }

        response = self.client.post(reverse('create_post'), data)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        print(form.errors)

        self.assertIn('photos', form.errors)

        self.assertEqual(form.errors['photos'], ["Можно прикрепить не более 10 фотографий."])

    def test_file_size_limitation(self):
        """можно загрузить файлы до 5мб"""

        large_file = generate_large_test_file(size_in_mb=6)

        data = {
            'countries': [self.country1.id],
            'tags': [],
            'subject': 'test subject',
            'body': 'test body',
            'photos': [large_file]
        }

        response = self.client.post(reverse('create_post'), data)
        form = response.context['form']
        print(form.errors)

        self.assertIn('photos', form.errors)

        self.assertEqual(form.errors['photos'], ["Размер изображения не может превышать 5 МБ."])


class IncreaseRatingTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.profile.countries_interest.add(self.country1)

        self.post1 = Post.objects.create(author=self.user, subject='Post by user')
        self.post1.countries.set([self.country1])

        self.url = reverse('increase_rating', args=[self.post1.id])

    def test_login_required(self):
        """перенаправоение если пользователь не аутентифицирован"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_increase_rating(self):
        """увеличение рейтинга"""

        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()

        self.assertEqual(self.post1.rating, 1)

        rating_action = PostRatingAction.objects.get(user=self.user, post=self.post1)
        self.assertEqual(rating_action.action, 'up')

        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})

    def test_rating_already_up(self):
        """пользователь может оставить всего один голос"""

        self.client.login(username='testuser', password='testpassword')

        PostRatingAction.objects.create(user=self.user, post=self.post1, action='up')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()

        self.assertEqual(self.post1.rating, 0)
        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})

    def test_change_rating_from_down_to_up(self):
        '''пользователь может поменять свой голос'''

        self.client.login(username='testuser', password='testpassword')

        PostRatingAction.objects.create(user=self.user, post=self.post1, action='down')
        self.post1.rating = -1
        self.post1.save()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()
        self.assertEqual(self.post1.rating, 0)

        rating_action = PostRatingAction.objects.get(user=self.user, post=self.post1)
        self.assertEqual(rating_action.action, 'up')

        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})


class DowngradeRatingTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.country1 = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha3_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.profile.countries_interest.add(self.country1)

        self.post1 = Post.objects.create(author=self.user, subject='Post by user', rating=1)
        self.post1.countries.set([self.country1])

        self.url = reverse('downgrade_rating', args=[self.post1.id])

    def test_login_required(self):
        """перенаправление если пользователь не аутентифицирован"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_downgrade_rating(self):
        """уменьшение рейтинга"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()

        self.assertEqual(self.post1.rating, 0)

        rating_action = PostRatingAction.objects.get(user=self.user, post=self.post1)
        self.assertEqual(rating_action.action, 'down')

        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})

    def test_rating_already_down(self):
        """пользователь может оставить всего один голос"""

        self.client.login(username='testuser', password='testpassword')

        PostRatingAction.objects.create(user=self.user, post=self.post1, action='down')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()
        self.assertEqual(self.post1.rating, 1)

        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})

    def test_change_rating_from_up_to_down(self):
        """пользователь может поменять голос"""

        self.client.login(username='testuser', password='testpassword')

        PostRatingAction.objects.create(user=self.user, post=self.post1, action='up')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        self.post1.refresh_from_db()
        self.assertEqual(self.post1.rating, 0)

        rating_action = PostRatingAction.objects.get(user=self.user, post=self.post1)
        self.assertEqual(rating_action.action, 'down')

        self.assertEqual(response.json(), {'status': 'ok', 'new_rating': self.post1.rating})


class ToggleSubscriptionTestCase(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='password')
        self.author = User.objects.create_user(username='authoruser', password='password')

        self.user_profile = Profile.objects.create(user=self.user)
        self.author_profile = Profile.objects.create(user=self.author)

        self.url = reverse('toggle_subscription', args=[self.author.id])

    def test_login_required(self):
        """перенаправление если пользователь не аутентифицирован"""

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_subscribe_to_author(self):
        """подписка на автора"""

        self.client.login(username='testuser', password='password')

        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(self.author_profile.followers.filter(id=self.user.id).exists())

        self.author_profile.refresh_from_db()
        self.assertEqual(self.author_profile.followers_count, 1)

    def test_unsubscribe_from_author(self):
        """отписка от автора"""

        self.client.login(username='testuser', password='password')

        self.author_profile.followers.add(self.user)
        self.author_profile.followers_count = 1
        self.author_profile.save()

        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertFalse(self.author_profile.followers.filter(id=self.user.id).exists())

        self.author_profile.refresh_from_db()
        self.assertEqual(self.author_profile.followers_count, 0)


class PostDetailViewTestCase(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.other_user_profile = Profile.objects.create(user=self.other_user)

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

        self.post2 = Post.objects.create(author=self.user, subject='Another post by user')
        self.post2.countries.set([self.country2])

        self.url = reverse('post_detail', args=[self.post2.id])

    def test_login_required(self):
        """перенаправление если пользователь не аутентифицирован"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_post_detail_view_authenticated_user(self):
        """Тестирование просмотра поста для аутентифицированного пользователя"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post2.subject)


class ProfilesListViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.superuser = User.objects.create_superuser(username='adminuser', password='adminpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.superuser_profile = Profile.objects.create(user=self.superuser)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post = Post.objects.create(author=self.user, subject='Test post')
        self.post.countries.set([self.country])

        self.url = reverse('profiles')

    def test_login_required(self):
        """Проверка редиректа для неаутентифицированных пользователей"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_profiles_list_view_authenticated_user(self):
        """Проверка списка профилей для аутентифицированного пользователя"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/index.html')
        self.assertContains(response, self.user.username)

    def test_exclude_superuser_profiles(self):
        """Проверка, что суперпользователи не отображаются в списке профилей"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertNotContains(response, self.superuser.username)


class ProfileDetailViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.other_user_profile = Profile.objects.create(user=self.other_user)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post = Post.objects.create(author=self.other_user, subject='Post by other user')
        self.post.countries.set([self.country])

        self.url = reverse('profile_detail', args=[self.other_user.id])

    def test_login_required(self):
        """Проверка редиректа для неаутентифицированных пользователей"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_profile_detail_view_authenticated_user(self):
        """Проверка страницы профиля для аутентифицированного пользователя"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile_detail.html')
        self.assertContains(response, self.other_user.username)
        self.assertContains(response, self.post.subject)

    def test_unique_country_count(self):
        """Проверка подсчета уникальных стран"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        unique_country_count = response.context['unique_country_count']
        self.assertEqual(unique_country_count, 1)

    def test_interested_countries(self):
        """Проверка отображения заинтересованных стран"""
        self.client.login(username='testuser', password='testpassword')

        self.other_user_profile.countries_interest.add(self.country)

        response = self.client.get(self.url)
        interested_countries = response.context['interested_countries']
        self.assertIn(self.country, interested_countries.all())


class ProfilePostsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.other_user_profile = Profile.objects.create(user=self.other_user)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post = Post.objects.create(author=self.user, subject='First Post')
        self.post.countries.set([self.country])

        self.post2 = Post.objects.create(author=self.user, subject='Second Post')
        self.post2.countries.set([self.country])

        self.url = reverse('profile_posts', args=[self.user.id])

    def test_login_required(self):
        """тест на перенаправление для неаутентифицированного пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_profile_posts_view_authenticated_user(self):
        """тест для аутентифицированного пользователя"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile_detail.html')
        self.assertContains(response, 'First Post')
        self.assertContains(response, 'Second Post')


class PostsByCountryViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.other_user_profile = Profile.objects.create(user=self.other_user)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post1 = Post.objects.create(author=self.user, subject='First Post', body='Content of the first post')
        self.post1.countries.set([self.country])
        self.post2 = Post.objects.create(author=self.user, subject='Second Post', body='Content of the second post')
        self.post2.countries.set([self.country])

        self.url = reverse('posts_by_country', args=[self.country.id])

    def test_login_required(self):
        """Тест на перенаправление для неаутентифицированного пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_posts_by_country_view_authenticated_user(self):
        """Тест для аутентифицированного пользователя"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'country/country_detail.html')

        self.assertContains(response, 'First Post')
        self.assertContains(response, 'Second Post')


class AddCommentViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')

        self.user_profile = Profile.objects.create(user=self.user)
        self.other_user_profile = Profile.objects.create(user=self.other_user)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post = Post.objects.create(author=self.user, subject='Test Post', body='Test content')
        self.post.countries.set([self.country])

        self.url = reverse('add_comment', args=[self.post.id])

    def test_login_required(self):
        """Проверка перенаправления для неаутентифицированного пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_successful_comment_submission(self):
        """тест для успешной отправки комментария"""

        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(self.url, {'body': 'test comment.'})

        self.assertRedirects(response, reverse('post_detail', args=[self.post.id]))

        comment = Comment.objects.last()
        self.assertEqual(comment.body, 'test comment.')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)


class PostCommentsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user_profile = Profile.objects.create(user=self.user)

        self.country = Country.objects.create(
            name='test country',
            top_level_domain='test top_level_domain',
            alpha2_code='test alpha2_code',
            alpha3_code='test alpha32_code',
            calling_code='test calling_code',
            capital='test capital',
            alt_spellings='test alt_spellings',
            region='region'
        )

        self.post = Post.objects.create(author=self.user, subject='Test Post', body='Test content')
        self.post.countries.set([self.country])

        self.comment1 = Comment.objects.create(post=self.post, author=self.user, body='First comment')
        self.comment2 = Comment.objects.create(post=self.post, author=self.user, body='Second comment')

        self.url = reverse('post_comments', args=[self.post.id])

    def test_post_comments_view_authenticated_user(self):
        """Тест для просмотра комментариев пользователем, который аутентифицирован"""
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['post'], self.post)

        comments = response.context['comments']
        self.assertIn(self.comment1, comments)
        self.assertIn(self.comment2, comments)

    def test_post_comments_view_unauthenticated_user(self):
        """Тест для перенаправления неаутентифицированного пользователя"""
        response = self.client.get(self.url)

        self.assertRedirects(response, f'{reverse("login")}?next={self.url}')


class TagViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user_profile = Profile.objects.create(user=self.user)

        self.tag = Tag.objects.create(name='Test Tag')

        self.post1 = Post.objects.create(author=self.user, subject='test subject', body='test body')
        self.post1.tags.set([self.tag])

        self.post2 = Post.objects.create(author=self.user, subject='test subject 2', body='test body 2')
        self.post1.tags.set([self.tag])

        self.url = reverse('tag_view', args=[self.tag.id])

    def test_tag_view_authenticated_user(self):
        """Тест для получения постов по тегу аутентифицированным пользователем"""

        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['tag'], self.tag)

        posts = response.context['posts']
        self.assertIn(self.post1, posts)

    def test_tag_view_unauthenticated_user(self):
        """Тест для перенаправления неаутентифицированного пользователя"""

        response = self.client.get(self.url)
        self.assertRedirects(response, f'{reverse("login")}?next={self.url}')


class PostsByTagViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.profile = Profile.objects.create(user=self.user)

        self.tag = Tag.objects.create(name='test_tag')

        self.post1 = Post.objects.create(author=self.user, subject='Test Subject 1', body='Test Body 1')
        self.post1.tags.set([self.tag])

        self.post2 = Post.objects.create(author=self.user, subject='Test Subject 2', body='Test Body 2')
        self.post2.tags.set([self.tag])

        self.url = reverse('posts_by_tag', args=[self.tag.id])

    def test_posts_by_tag_view_authenticated_user(self):
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        posts = response.context['posts']

        self.assertIn(self.post1, posts)
        self.assertIn(self.post2, posts)

    def test_posts_by_tag_view_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next=' + self.url)












