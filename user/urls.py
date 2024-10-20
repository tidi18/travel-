from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create/post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/increase-rating/', views.increase_rating, name='increase_rating'),
    path('post/<int:post_id>/downgrade-rating/', views.downgrade_rating, name='downgrade_rating'),
    path('subscribe/<int:author_id>/', views.toggle_subscription, name='toggle_subscription'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('profiles/', views.profiles_list_view, name='profiles'),
    path('profiles/<int:user_id>/', views.profile_detail_view, name='profile_detail'),
    path('profiles/<int:user_id>/posts/', views.profile_posts, name='profile_posts'),
    path('posts/country/<int:country_id>/', views.posts_by_country_view, name='posts_by_country'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/comments/', views.post_comments_view, name='post_comments'),
    path('', views.index, name='index')


]