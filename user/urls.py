from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('create/post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/increase-rating/', views.increase_rating, name='increase_rating'),
    path('post/<int:post_id>/downgrade-rating/', views.downgrade_rating, name='downgrade_rating'),
    path('subscribe/<int:author_id>/', views.toggle_subscription, name='toggle_subscription'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('', views.index, name='index')


]