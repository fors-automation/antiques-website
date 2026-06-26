from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('items/', views.item_list, name='item_list'),
    path('category/<slug:slug>/', views.item_list, name='category'),
    path('item/<slug:slug>/', views.item_detail, name='item'),
    path('information/', views.article_list, name='information'),
    path('information/<slug:slug>/', views.article_detail, name='article'),
    path('contact/', views.contact, name='contact'),
]
