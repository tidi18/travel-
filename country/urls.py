from django.urls import path
from . import views

urlpatterns = [
    path('countries/', views.country_list_view, name='country_list_view'),
    path('toggle_country_interest/<int:country_id>/', views.toggle_country_interest, name='toggle_country_interest'),
    path('country/<int:country_id>/', views.country_detail_view, name='country_detail'),

]