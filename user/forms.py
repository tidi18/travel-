from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import MinLengthValidator
from .models import Profile, Post, Tag, Comment
from country.models import Country


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class RegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Пароль')
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label='Подтверждение пароля')
    countries_interest = forms.ModelMultipleChoiceField(
        queryset=Country.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'countries_interest']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Устанавливаем зашифрованный пароль

        if commit:
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                profile.countries_interest.set(self.cleaned_data['countries_interest'])
                profile.save()

        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        label='Пароль'
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверный логин или пароль.', code='invalid_login')

        return self.cleaned_data


class PostForm(forms.ModelForm):
    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Страны',
        required=True
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Теги',
        required=False
    )
    subject = forms.CharField(
        label='Тема',
        max_length=255,
        required=True
    )
    body = forms.CharField(
        label='Тело поста',
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 20}),
        required=True,
        validators=[MinLengthValidator(3)]
    )
    photos = MultipleFileField(label='Select files', required=True)

    class Meta:
        model = Post
        fields = ['countries', 'tags',  'subject', 'body', 'photos']  # Укажите поля, которые хотите включить в форму

    def clean_photos(self):
        photos = self.cleaned_data.get('photos')

        if len(photos) > 10:
            raise forms.ValidationError("Можно прикрепить не более 10 фотографий.")

        for image in photos:
            if image.size > 5 * 1024 * 1024:  # 5 МБ в байтах
                raise forms.ValidationError("Размер изображения не может превышать 5 МБ.")

        return photos


class CommentForm(forms.ModelForm):
    body = forms.CharField(
        label='Тело поста',
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 20}),
        required=True,
        validators=[MinLengthValidator(3)]  # Убедитесь, что это импортировано
    )

    class Meta:
        model = Comment
        fields = ['body']
