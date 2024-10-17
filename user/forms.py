from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile
from django.utils.translation import gettext_lazy as _
from country.models import Country


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

            # Проверка на существование профиля
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

