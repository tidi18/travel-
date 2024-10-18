from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import RegistrationForm, PostForm
from .models import Profile, Photo
from .forms import UserLoginForm


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
    return render(request, "user/index.html")


def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            uploaded_images = request.FILES.getlist('photos')
            for image in uploaded_images:
                photo = Photo(image=image)
                photo.save()
                post.photos.add(photo)
            return redirect('index')
    else:
        form = PostForm()

    return render(request, 'user/create_post.html', {'form': form})

